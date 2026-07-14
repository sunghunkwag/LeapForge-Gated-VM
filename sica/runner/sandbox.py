"""Process sandbox (the runtime half of G-sandbox).

Two things run as subprocesses in this engine and BOTH go through here:
  1. the self-editing scaffold (broker.py launches it), and
  2. every test command the scaffold asks to run (ctx.run -> broker -> here).

Both are wrapped with `unshare -n` so they have NO network namespace at all --
a self-editing agent with filesystem + network is the one thing the directive
says is never worth the speed, so the containment is structural, not a flag the
agent could flip. The environment is stripped to a minimal safe set (no proxy
vars, no auth tokens, no API keys), the working directory is confined to the
task workdir, and test executables are checked against a tiny allowlist.

If `unshare -n` is not available on the host, real runs REFUSE to start rather
than silently executing with network (see probe_isolation / require_isolation).
"""

import os
import shutil
import subprocess

# Test commands may only invoke these (basename of argv[0]).
ALLOWED_TEST_EXE = {"python", "python3"}

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sica/

# Directories that must be INVISIBLE to any sandboxed child, so that even a
# Python-sandbox escape (e.g. reaching os via an allowed module's re-exported
# `sys`/`builtins` attribute) cannot read grading assets or held-out scores.
# A tmpfs is mounted over each inside the child's mount namespace; the parent
# (which does the trusted grading) is unaffected.
_HIDE_DIRS = [
    os.path.join(_REPO_ROOT, "runner", "bench", "tasks"),
    os.path.join(_REPO_ROOT, "runner", "bench", "tasks_hard"),
    os.path.join(_REPO_ROOT, "runner", "bench", "fixtures"),
    os.path.join(_REPO_ROOT, "ledger"),
    os.path.join(_REPO_ROOT, "memory"),
    os.path.join(_REPO_ROOT, "archive"),
    os.path.join(_REPO_ROOT, "runs"),
]

# Minimal environment handed to sandboxed children. Deliberately excludes
# HTTPS_PROXY/HTTP_PROXY/*_TOKEN/ANTHROPIC_API_KEY/GH_TOKEN/... everything.
_SAFE_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "TZ", "HOME")


def _safe_env(extra=None):
    env = {}
    for k in _SAFE_ENV_KEYS:
        if k in os.environ:
            env[k] = os.environ[k]
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["NO_NETWORK"] = "1"
    if extra:
        env.update(extra)
    return env


_UNSHARE = shutil.which("unshare")


def _mount_script(inner):
    """Shell that, inside the child's mount namespace, hides the sensitive
    dirs with a tmpfs then execs the real argv (passed as "$@")."""
    lines = []
    for d in _HIDE_DIRS:
        # only mount over dirs that exist; failures are non-fatal (|| true)
        lines.append('[ -d "%s" ] && mount -t tmpfs none "%s" 2>/dev/null || true'
                     % (d, d))
    lines.append('exec "$@"')
    return "; ".join(lines) if inner else "\n".join(lines)


def _probe():
    if _UNSHARE is None:
        return False, "unshare not found"
    # Require BOTH network (-n) and mount (-m) namespaces, and that a tmpfs
    # mount actually works, since filesystem hiding is load-bearing for
    # G-isolate against a Python-sandbox escape.
    try:
        script = ('d=$(mktemp -d) && mount -t tmpfs none "$d" && '
                  'test -z "$(ls -A "$d")" && echo ok')
        r = subprocess.run([_UNSHARE, "-n", "-m", "--", "sh", "-c", script],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=20)
    except Exception as e:  # noqa
        return False, "unshare probe raised: %s" % e
    if r.returncode != 0 or b"ok" not in r.stdout:
        return False, "unshare -n -m + tmpfs rc=%d: %s" % (
            r.returncode, r.stderr.decode("utf-8", "replace")[:200])
    return True, "net+mount namespaces, tmpfs hiding OK"


_ISOLATION = None


def probe_isolation():
    global _ISOLATION
    if _ISOLATION is None:
        _ISOLATION = _probe()
    return _ISOLATION


def require_isolation():
    ok, why = probe_isolation()
    if not ok:
        raise RuntimeError(
            "G-sandbox: network+mount isolation unavailable (%s); refusing to "
            "run a self-editing agent without it" % why)


def wrap_no_network(argv):
    """Prefix argv so the child runs with NO network namespace AND a mount
    namespace in which the grading-asset / held-out directories are hidden by a
    tmpfs. Even a Python escape to os cannot then read those files."""
    ok, _why = probe_isolation()
    if ok:
        return ([_UNSHARE, "-n", "-m", "--", "sh", "-c",
                 _mount_script(inner=True), "sh"] + list(argv))
    return list(argv)  # caller must have gated on require_isolation()


class SandboxResult(object):
    def __init__(self, code, stdout, stderr, timed_out, duration):
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.duration = duration

    def as_dict(self, cap=4000):
        return {"code": self.code, "stdout": self.stdout[:cap],
                "stderr": self.stderr[:cap], "timed_out": self.timed_out,
                "duration": round(self.duration, 3)}


def run_test_command(argv, cwd, timeout=60, clock=None):
    """Run an allowlisted test command under network isolation, cwd-confined."""
    import time
    clock = clock or time.time
    if not argv:
        raise ValueError("empty argv")
    exe = os.path.basename(argv[0])
    if exe not in ALLOWED_TEST_EXE:
        raise PermissionError("executable not allowed: %s" % exe)
    real_cwd = os.path.realpath(cwd)
    if not os.path.isdir(real_cwd):
        raise ValueError("cwd does not exist: %s" % cwd)
    full = wrap_no_network(argv)
    t0 = clock()
    try:
        proc = subprocess.run(
            full, cwd=real_cwd, env=_safe_env(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace")
        err = (e.stderr or b"").decode("utf-8", "replace")
        return SandboxResult(124, out, err, True, clock() - t0)
    return SandboxResult(
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
        False, clock() - t0)
