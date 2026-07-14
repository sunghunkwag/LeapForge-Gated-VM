"""Per-task meters with hard caps (G-budget).

The broker consults the meter before every brokered capability. A breach
raises BudgetError, which the harness catches: the task ends immediately and
is scored unsolved. Generation-level budget enforcement (auto-halt at >Nx
projected spend) is done in engine.py from the summed task meters.
"""

import time


class BudgetError(Exception):
    """Raised when a task exceeds one of its hard caps."""

    def __init__(self, which, used, cap):
        self.which = which
        self.used = used
        self.cap = cap
        super().__init__("budget exceeded: %s used=%s cap=%s"
                         % (which, used, cap))


class Meter(object):
    def __init__(self, caps, clock=None):
        self.caps = dict(caps)
        self.clock = clock or time.time
        self.t0 = self.clock()
        self.model_calls = 0
        self.model_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.tool_calls = 0
        self.steps = 0
        self.io_ops = 0
        self.bytes_written = 0
        self.cost_usd = 0.0

    # --- checks: called BEFORE the capability, so a breach prevents spend ----
    def check_wall(self):
        """Public wall-clock check, honoured by EVERY op (even cheap ones)."""
        self._check_wall()

    def check_model(self, est_input_tokens=0):
        if self.model_calls >= self.caps["max_model_calls"]:
            raise BudgetError("max_model_calls", self.model_calls,
                              self.caps["max_model_calls"])
        # a single call may not push accumulated tokens past the cap: charge
        # the estimated input up front so one huge call cannot overshoot.
        if self.model_tokens + est_input_tokens >= self.caps["max_model_tokens"]:
            raise BudgetError("max_model_tokens",
                              self.model_tokens + est_input_tokens,
                              self.caps["max_model_tokens"])
        self._check_wall()

    def remaining_model_tokens(self):
        return max(0, self.caps["max_model_tokens"] - self.model_tokens)

    def check_io(self):
        """Cheap filesystem ops (read/ls/grep/log/write) are metered too, so a
        busy-loop on them cannot run unbounded (G-budget)."""
        if self.io_ops >= self.caps.get("max_io_ops", 10 ** 9):
            raise BudgetError("max_io_ops", self.io_ops,
                              self.caps.get("max_io_ops"))
        self._check_wall()

    def check_write(self, nbytes):
        cap = self.caps.get("max_write_bytes", 10 ** 12)
        if self.bytes_written + nbytes > cap:
            raise BudgetError("max_write_bytes", self.bytes_written + nbytes,
                              cap)

    def check_tool(self):
        if self.tool_calls >= self.caps["max_tool_calls"]:
            raise BudgetError("max_tool_calls", self.tool_calls,
                              self.caps["max_tool_calls"])
        self._check_wall()

    def check_step(self):
        if self.steps >= self.caps["max_steps"]:
            raise BudgetError("max_steps", self.steps, self.caps["max_steps"])
        self._check_wall()

    def _check_wall(self):
        el = self.clock() - self.t0
        if el >= self.caps["wall_seconds"]:
            raise BudgetError("wall_seconds", round(el, 1),
                              self.caps["wall_seconds"])

    # --- records: called AFTER the capability, to account spend --------------
    def record_model(self, input_tokens, output_tokens, cost_usd):
        self.model_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.model_tokens += input_tokens + output_tokens
        self.cost_usd += cost_usd

    def record_tool(self):
        self.tool_calls += 1

    def record_step(self):
        self.steps += 1

    def record_io(self):
        self.io_ops += 1

    def record_write(self, nbytes):
        self.bytes_written += nbytes

    def snapshot(self):
        return {
            "model_calls": self.model_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "model_tokens": self.model_tokens,
            "tool_calls": self.tool_calls,
            "steps": self.steps,
            "io_ops": self.io_ops,
            "bytes_written": self.bytes_written,
            "cost_usd": round(self.cost_usd, 6),
            "wall_seconds": round(self.clock() - self.t0, 2),
        }


def sum_snapshots(snaps):
    out = {"model_calls": 0, "input_tokens": 0, "output_tokens": 0,
           "model_tokens": 0, "tool_calls": 0, "steps": 0, "io_ops": 0,
           "bytes_written": 0, "cost_usd": 0.0, "wall_seconds": 0.0}
    for s in snaps:
        for k in out:
            out[k] += s.get(k, 0)
    out["cost_usd"] = round(out["cost_usd"], 6)
    out["wall_seconds"] = round(out["wall_seconds"], 2)
    return out
