"""SWE-bench Verified adapter (the `full` / transfer backend).

SWE-bench Verified is the maintained, human-filtered real-repo coding benchmark
(500 instances curated from real GitHub issues + PRs, each with a gold patch
and FAIL_TO_PASS / PASS_TO_PASS test sets). It is the right yardstick for a
one-shot transfer read once a docker host with the images and dataset is
available. This adapter PINS the dataset and a fixed instance subset so a run
is reproducible, and it REFUSES to run (rather than fabricating a score) when
the host cannot provide the images/data -- consistent with the directive's rule
that a number must mean capability or not be produced at all.

Pinning only; wiring to the official `swebench` harness (image build + test
exec) is intentionally left as an explicit host-gated step, because building
those images is exactly the multi-GB, network-heavy operation the engine loop
must not attempt inside this sandbox.
"""

import shutil

# Pinned dataset + a fixed instance subset (repository-disjoint by construction
# when split, since instance ids carry their repo).
PIN = {
    "dataset": "princeton-nlp/SWE-bench_Verified",
    "revision": "v1.0",                 # pin the dataset revision
    "harness": "swebench>=2.1,<3",
    "split": "test",
    # a small, fixed, repo-diverse subset for a transfer read; expand for full.
    "instances": [
        "astropy__astropy-12907",
        "django__django-11099",
        "matplotlib__matplotlib-23299",
        "pytest-dev__pytest-5227",
        "scikit-learn__scikit-learn-13439",
        "sympy__sympy-13471",
        "requests__requests-2317",
        "flask__flask-4045",
    ],
}


def availability():
    """Report whether this host can actually run SWE-bench Verified."""
    reasons = []
    if shutil.which("docker") is None:
        reasons.append("docker not found")
    try:
        import datasets  # noqa
    except ImportError:
        reasons.append("`datasets` not installed")
    try:
        import swebench  # noqa
    except ImportError:
        reasons.append("`swebench` harness not installed")
    return {"runnable": not reasons, "reasons": reasons, "pin": PIN}


def require_runnable():
    a = availability()
    if not a["runnable"]:
        raise RuntimeError(
            "SWE-bench Verified backend is not runnable on this host (%s). "
            "Use the localsuite backend for the engine loop, or provision a "
            "docker host with the pinned images/dataset for a transfer read."
            % "; ".join(a["reasons"]))
    return a
