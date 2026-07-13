"""Model client. Three backends, one pinned model string.

  claude_cli     -- primary. Shells out to the authenticated `claude` CLI in a
                    hermetic, tool-less, no-MCP, no-settings configuration and
                    parses the JSON usage report for exact token + cost
                    accounting. The CLI exposes no temperature flag, so for
                    this backend temperature is the provider default; this is
                    logged as a substrate caveat (config.MODEL_TEMPERATURE
                    records the *requested* value).
  anthropic_api  -- used iff ANTHROPIC_API_KEY is present. temperature=0.
  stub           -- deterministic, offline, $0. Drives the whole engine for
                    verification without any network or spend. Its behaviour is
                    a pure function of (system, prompt) so verify runs are
                    reproducible.

Every backend returns (text, usage) where usage = {input_tokens,
output_tokens, cost_usd}. The broker feeds usage into the per-task Meter.
"""

import hashlib
import json
import os
import subprocess
import tempfile

from . import config


class ModelError(Exception):
    pass


# --- Haiku list price (USD per token), for the stub + api cost estimate. -----
# Only used when a backend does not report cost directly.
_PRICE_IN = 1.0 / 1_000_000
_PRICE_OUT = 5.0 / 1_000_000


class ModelClient(object):
    def __init__(self, backend="claude_cli", model=None, temperature=None,
                 stub_fn=None):
        self.backend = backend
        self.model = model or config.MODEL_PINNED
        self.temperature = (config.MODEL_TEMPERATURE if temperature is None
                            else temperature)
        self.stub_fn = stub_fn
        self.calls = 0
        # session-wide accumulators (thread-safe enough for coarse caps)
        self.total_input = 0
        self.total_output = 0
        self.total_cost = 0.0
        if backend == "anthropic_api":
            self._client = self._make_api_client()

    # ------------------------------------------------------------------ api
    def complete(self, system, prompt, max_tokens=2048):
        self.calls += 1
        if self.backend == "stub":
            text, usage = self._complete_stub(system, prompt)
        elif self.backend == "claude_cli":
            text, usage = self._complete_cli(system, prompt, max_tokens)
        elif self.backend == "anthropic_api":
            text, usage = self._complete_api(system, prompt, max_tokens)
        else:
            raise ModelError("unknown backend: %s" % self.backend)
        self.total_input += usage["input_tokens"]
        self.total_output += usage["output_tokens"]
        self.total_cost += usage["cost_usd"]
        return text, usage

    def session_totals(self):
        return {"calls": self.calls, "input_tokens": self.total_input,
                "output_tokens": self.total_output,
                "cost_usd": round(self.total_cost, 6)}

    # ------------------------------------------------------------ claude_cli
    def _complete_cli(self, system, prompt, max_tokens, retries=3):
        last = None
        for attempt in range(retries):
            try:
                return self._cli_once(system, prompt)
            except ModelError as e:
                last = e
        raise last

    def _cli_once(self, system, prompt):
        # Hermetic invocation: no tools, no MCP, no settings discovery, run in
        # a throwaway neutral cwd so no CLAUDE.md / skills are picked up.
        with tempfile.TemporaryDirectory(prefix="sica-mc-") as neutral:
            cmd = [
                "claude", "-p",
                "--model", self.model,
                "--output-format", "json",
                "--tools", "",
                "--no-session-persistence",
                "--setting-sources", "",
                "--strict-mcp-config",
                "--mcp-config", "{\"mcpServers\":{}}",
                "--system-prompt", system,
            ]
            try:
                proc = subprocess.run(
                    cmd, input=prompt.encode("utf-8"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    cwd=neutral, timeout=180,
                )
            except subprocess.TimeoutExpired:
                raise ModelError("claude cli timeout")
            if proc.returncode != 0:
                raise ModelError("claude cli rc=%d: %s"
                                 % (proc.returncode,
                                    proc.stderr.decode("utf-8", "replace")[:400]))
            try:
                d = json.loads(proc.stdout.decode("utf-8", "replace"))
            except ValueError:
                raise ModelError("claude cli non-json: %s"
                                 % proc.stdout.decode("utf-8", "replace")[:400])
            if d.get("is_error"):
                raise ModelError("claude cli reported error: %s"
                                 % str(d.get("result"))[:400])
            text = d.get("result", "")
            u = d.get("usage", {}) or {}
            in_tok = (int(u.get("input_tokens", 0))
                      + int(u.get("cache_read_input_tokens", 0))
                      + int(u.get("cache_creation_input_tokens", 0)))
            out_tok = int(u.get("output_tokens", 0))
            cost = float(d.get("total_cost_usd", 0.0) or 0.0)
            if cost == 0.0:
                cost = in_tok * _PRICE_IN + out_tok * _PRICE_OUT
            usage = {"input_tokens": in_tok, "output_tokens": out_tok,
                     "cost_usd": cost}
            return text, usage

    # --------------------------------------------------------- anthropic_api
    def _make_api_client(self):
        try:
            import anthropic  # noqa
        except ImportError:
            raise ModelError("anthropic sdk not installed")
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ModelError("ANTHROPIC_API_KEY not set")
        return anthropic.Anthropic(api_key=key)

    def _complete_api(self, system, prompt, max_tokens):
        msg = self._client.messages.create(
            model=self.model, max_tokens=max_tokens,
            temperature=self.temperature,
            system=system, messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        in_tok = msg.usage.input_tokens
        out_tok = msg.usage.output_tokens
        usage = {"input_tokens": in_tok, "output_tokens": out_tok,
                 "cost_usd": in_tok * _PRICE_IN + out_tok * _PRICE_OUT}
        return text, usage

    # ---------------------------------------------------------------- stub
    def _complete_stub(self, system, prompt):
        if self.stub_fn is None:
            raise ModelError("stub backend requires a stub_fn")
        text = self.stub_fn(system, prompt)
        in_tok = max(1, len(system) // 4 + len(prompt) // 4)
        out_tok = max(1, len(text) // 4)
        usage = {"input_tokens": in_tok, "output_tokens": out_tok,
                 "cost_usd": 0.0}
        return text, usage


def digest(*parts):
    """Small helper for deterministic stub logic."""
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
