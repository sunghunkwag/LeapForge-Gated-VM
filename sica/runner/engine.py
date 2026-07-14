"""The self-improvement engine: one generation = the directive's section-2 loop.

  1. incumbent attempts the TRAIN slice at fixed budget (metered);
  2. its failing transcripts + the heldout-stripped improvement memory drive
     K candidate scaffolds, each targeting a different failure mode;
  3. GATE: each candidate vs the incumbent on the SAME train tasks/budget;
     keep the strict winner (tie -> incumbent);
  4. score the winner on HELD-OUT -- the curve. This never feeds proposals.
  5. append to memory + archive, snapshot the ledger, print the curve.

Auto-halts (sections 4/5): budget exhaustion, a generation exceeding
gen_budget_multiple x the established per-generation spend, held-out
regression for `regression_halt` consecutive generations, or a scope-escape /
grading-asset access attempt (halt + preserve ledger). Quality-diversity escape
(section 1.4): if held-out has not improved for `stall_restart` generations,
branch from the best PRIOR archived scaffold (chosen by TRAIN score, so the
selection stays held-out-blind) along a failure mode not recently tried.
"""

import os
from concurrent.futures import ThreadPoolExecutor

from . import archive as archive_mod
from . import gate as gate_mod
from . import leakscan
from . import proposer as proposer_mod
from . import sandbox, scaffold_io
from .config import config_sha
from .evaluate import evaluate_scaffold
from .harness import failure_digest
from .ledger import Ledger
from .memory import ImprovementMemory
from .prng import XorShift64Star


class Engine(object):
    def __init__(self, cfg, benchmark, model_client, dirs, logger=None,
                 session_cost_cap=None, run_id="run", halt_on_adopt=False,
                 grading_lock_path=None):
        self.cfg = cfg
        self.bench = benchmark
        self.model = model_client
        self.dirs = dirs
        self.log = logger or (lambda *a: print(*a))
        self.session_cost_cap = session_cost_cap
        self.run_id = run_id
        self.grading_lock_path = grading_lock_path
        # T8 (PI override for the smoke): if a gate adoption fires, do NOT
        # self-modify unattended -- halt and preserve state for a human
        # keypress. When True the loop runs unattended only up to the first
        # adoption; if no gate ever fires it completes unattended.
        self.halt_on_adopt = halt_on_adopt
        self.csha = config_sha(cfg)
        self.prng = XorShift64Star("engine|%s|%s" % (cfg["seed"], self.csha))
        # Each invocation gets its own ledger/memory/archive so separate runs
        # never interleave; within a run the memory compounds across gens.
        self.ledger = Ledger(os.path.join(
            dirs["ledger"], "run_%s_seed%s_%s.jsonl"
            % (self.csha, cfg["seed"], run_id)))
        self.memory = ImprovementMemory(os.path.join(
            dirs["memory"], "improvement_%s_%s.jsonl" % (self.csha, run_id)))
        self.archive = archive_mod.Archive(
            os.path.join(dirs["archive"], "%s_%s" % (self.csha, run_id)))
        self.caps = cfg["task_budget"]
        self.conc = cfg.get("concurrency", 4)

    # ------------------------------------------------------------------ run
    def run(self, incumbent):
        cfg = self.cfg
        sandbox.require_isolation()          # G-sandbox: refuse without it
        iso_ok, iso_why = sandbox.probe_isolation()

        train, heldout = self.bench.split(cfg["seed"], cfg["n_train"],
                                          cfg["n_heldout"])
        self.log("split: %d train (%d repos) / %d heldout (%d repos), "
                 "repo-disjoint"
                 % (len(train), len({t.repo for t in train}),
                    len(heldout), len({t.repo for t in heldout})))

        scaffold_io.audit_scaffold(incumbent)
        gen0_sha = scaffold_io.scaffold_sha(incumbent)

        # T1: grading-asset containment control, fail-closed BEFORE any metered
        # work. Reachability scan proves no hidden test / gold patch / meta is
        # within the agent's read scope; the hash-lock (if committed) proves the
        # grading assets have not drifted since they were locked.
        reach = leakscan.reachability_scan(self.bench)
        if not reach["ok"]:
            raise RuntimeError("T1 reachability scan FAILED (a grading asset is "
                               "reachable by the agent): %s" % reach["reasons"])
        lock_report = {"checked": False, "ok": None, "reasons": []}
        if self.grading_lock_path:
            ok, reasons = leakscan.verify_lock(self.bench, self.grading_lock_path)
            lock_report = {"checked": True, "ok": ok, "reasons": reasons}
            if not ok:
                raise RuntimeError("T1 grading-asset hash-lock FAILED "
                                   "(assets drifted since lock): %s" % reasons)
        self.log("T1 containment: reachability OK (%d tasks scanned); "
                 "hash-lock %s" % (reach["checked"],
                 "verified" if lock_report["ok"] else
                 ("MISSING" if not self.grading_lock_path else "FAILED")))

        self.ledger.append("GENESIS", {
            "engine_version": cfg["engine_version"],
            "run_id": self.run_id,
            "config": cfg, "config_sha": config_sha(cfg),
            "model_pinned": cfg["model_pinned"],
            "model_backend": cfg["model_backend"],
            "model_temperature_requested": cfg["model_temperature"],
            "benchmark_pin": self.bench.pin(),
            "isolation": {"ok": iso_ok, "detail": iso_why},
            "grading_containment": {"reachability": reach,
                                    "hash_lock": lock_report},
            "halt_on_adopt": self.halt_on_adopt,
            "guardrails": ["G-isolate", "G-heldout", "G-sandbox", "G-budget"],
            "train_ids": [t.id for t in train],
            "heldout_ids": [t.id for t in heldout],
            "gen0_scaffold_sha": gen0_sha,
        })

        # curve[0] = GEN0 on held-out (baseline). Held-out is scored on the
        # ADOPTED scaffold only; it never enters proposals or the gate.
        self.log("\n=== GEN 0 (baseline) ===")
        g0_held = self._eval(incumbent, heldout, "gen0-heldout")
        if self._halt_on_violation(g0_held, 0):
            return self._finalize([g0_held["score"]], gen0_sha, halted=True)
        curve = [g0_held["score"]]
        best_heldout = g0_held["score"]
        best_sha = gen0_sha
        self.archive.add(incumbent, 0, None, g0_held["score"],
                         "baseline", "GEN0 seed scaffold", adopted=True)
        self.ledger.append("GEN", {
            "generation": 0, "incumbent_sha": gen0_sha, "adopted": True,
            "heldout_solved": g0_held["solved"], "heldout_n": g0_held["n"],
            "heldout_score": g0_held["score"], "heldout_meter": g0_held["meter"],
        })
        self._print_curve(curve)

        gen_baseline_tokens = None
        regressions = 0
        stall = 0

        for gen in range(1, cfg["max_generations"] + 1):
            self.log("\n=== GEN %d ===" % gen)
            restart_note = None

            # QD escape (section 1.4): held-out stagnation -> diversify from
            # the best PRIOR scaffold (selected by TRAIN score = heldout-blind).
            if stall >= cfg["stall_restart"]:
                prior = self.archive.best_prior(by="train_score")
                if prior is not None:
                    incumbent = self.archive.load(prior)
                    restart_note = {"restart_from": prior["sha"],
                                    "reason": "heldout stalled %d gens" % stall,
                                    "avoid_modes":
                                        self.archive.modes_tried_since(
                                            prior["sha"])}
                    self.log("  QD escape: restart from %s (train_score=%s)"
                             % (prior["sha"], prior.get("train_score")))
                    stall = 0

            # step 1: incumbent attempts TRAIN (fresh, fair gate baseline)
            inc_eval = self._eval(incumbent, train, "gen%d-incumbent" % gen)
            if self._halt_on_violation(inc_eval, gen):
                return self._finalize(curve, gen0_sha, halted=True)
            self.log("  incumbent TRAIN solved %d/%d"
                     % (inc_eval["solved"], inc_eval["n"]))

            # step 2: propose K candidates (parallel), each a distinct steer
            avoid = (restart_note or {}).get("avoid_modes", [])
            cands, prop_infos, prop_cost = self._propose(
                incumbent, inc_eval, gen, avoid)

            # step 3: GATE -- each candidate vs incumbent on the SAME train
            cand_evals = self._gate_eval(cands, prop_infos, train, gen)
            # a model-authored candidate that tried to escape scope halts the
            # run just like the incumbent would (directive section 5).
            for ce in cand_evals:
                if ce and ce.get("violation"):
                    self.ledger.append("HALT", {
                        "generation": gen, "reason": "violation",
                        "detail": ce["violation"], "where": "candidate gate"})
                    self.log("  AUTO-HALT: candidate scaffold attempted a "
                             "scope-escape: %s (ledger preserved)"
                             % ce["violation"])
                    return self._finalize(curve, gen0_sha, halted=True,
                                          halt_reason="violation",
                                          best_sha=best_sha)
            winner, decision = gate_mod.select_winner(inc_eval, cand_evals)
            adopted = decision["adopted"]

            # T8: a gate that fires during a keypress-gated run halts for
            # human approval instead of self-modifying unattended.
            if adopted and self.halt_on_adopt:
                self.archive.add(
                    winner["scaffold"], gen, winner["score"], None,
                    decision.get("winner_targeted_failure_mode") or "none",
                    "PENDING approval: " + (winner["info"].get("label") or ""),
                    adopted=False)
                self.ledger.append("PENDING_ADOPTION", {
                    "generation": gen,
                    "winner_sha": decision["winner_sha"],
                    "winner_label": decision.get("winner_label"),
                    "targeted_failure_mode":
                        decision.get("winner_targeted_failure_mode"),
                    "train_delta": decision.get("train_delta"),
                    "gate": decision,
                    "note": "smoke gate fired; adoption requires a PI keypress "
                            "(T8). Held-out was NOT scored on the candidate.",
                })
                self.log("  GATE FIRED -> HALT for approval (T8): '%s' beat "
                         "the incumbent on TRAIN (+%s). Not scored on held-out; "
                         "awaiting PI keypress before self-modifying."
                         % (decision.get("winner_label"),
                            decision.get("train_delta")))
                return self._finalize(
                    curve, gen0_sha, halted=True,
                    halt_reason="adoption_requires_approval (T8)",
                    best_sha=best_sha)

            adopted_scaffold = winner["scaffold"] if adopted else incumbent
            adopted_sha = scaffold_io.scaffold_sha(adopted_scaffold)
            self.log("  gate: %d/%d candidates beat incumbent -> %s"
                     % (decision["n_beating"], decision["n_candidates"],
                        "ADOPT %s" % decision.get("winner_label")
                        if adopted else "keep incumbent"))

            # step 4: HELD-OUT score of the adopted scaffold (clean)
            held_eval = self._eval(adopted_scaffold, heldout,
                                   "gen%d-heldout" % gen)
            if self._halt_on_violation(held_eval, gen):
                return self._finalize(curve, gen0_sha, halted=True)
            heldout_score = held_eval["score"]

            # spend accounting for this generation
            gen_tokens = (prop_cost["model_tokens"]
                          + inc_eval["meter"]["model_tokens"]
                          + sum(c["meter"]["model_tokens"]
                                for c in cand_evals if c)
                          + held_eval["meter"]["model_tokens"])
            gen_cost = (prop_cost["cost_usd"]
                        + inc_eval["meter"]["cost_usd"]
                        + sum(c["meter"]["cost_usd"] for c in cand_evals if c)
                        + held_eval["meter"]["cost_usd"])

            # step 5: memory + archive + ledger + curve
            train_delta = (decision.get("train_delta", 0) if adopted else 0)
            mode = (decision.get("winner_targeted_failure_mode")
                    if adopted else None)
            self.memory.append({
                "generation": gen,
                "targeted_failure_mode": mode,
                "change_summary": (winner["info"].get("rationale")
                                   if adopted else
                                   "no candidate beat the incumbent"),
                "predicted_effect": (winner["info"].get("predicted_effect")
                                     if adopted else None),
                "measured_train_delta": train_delta,
                "measured_heldout_delta": round(heldout_score - curve[-1], 4),
                "adopted": adopted,
                "candidates": decision["candidate_summ"],
            })
            self.archive.add(adopted_scaffold, gen,
                             (winner["score"] if adopted else inc_eval["score"]),
                             heldout_score, mode or "none",
                             (winner["info"].get("label") if adopted
                              else "incumbent-retained"), adopted)
            self.ledger.append("GEN", {
                "generation": gen,
                "incumbent_sha": inc_eval["sha"],
                "restart": restart_note,
                "gate": decision,
                "proposals": [self._prop_summary(p) for p in prop_infos],
                "adopted": adopted, "adopted_sha": adopted_sha,
                "train_incumbent_solved": inc_eval["solved"],
                "train_winner_solved": (winner["solved"] if adopted else None),
                "heldout_solved": held_eval["solved"],
                "heldout_n": held_eval["n"],
                "heldout_score": heldout_score,
                "gen_model_tokens": gen_tokens,
                "gen_cost_usd": round(gen_cost, 6),
                "session_cost_usd": self.model.session_totals()["cost_usd"],
            })
            curve.append(heldout_score)
            incumbent = adopted_scaffold
            self._print_curve(curve)

            # --- track best / regression / stall ---
            if heldout_score > best_heldout + 1e-9:
                best_heldout = heldout_score
                best_sha = adopted_sha
                stall = 0
            else:
                stall += 1
            if heldout_score < curve[-2] - 1e-9:
                regressions += 1
            else:
                regressions = 0

            # --- auto-halts (section 4/5) ---
            halt = self._check_halts(gen, gen_tokens, gen_baseline_tokens,
                                     regressions)
            if gen == 1:
                gen_baseline_tokens = gen_tokens
            if halt:
                self.ledger.append("HALT", {"generation": gen, "reason": halt})
                self.log("  AUTO-HALT: %s (ledger preserved)" % halt)
                return self._finalize(curve, gen0_sha, halted=True,
                                      halt_reason=halt, best_sha=best_sha)

        return self._finalize(curve, gen0_sha, halted=False, best_sha=best_sha)

    # -------------------------------------------------------------- helpers
    def _eval(self, scaffold, tasks, label):
        return evaluate_scaffold(scaffold, tasks, self.model, self.caps,
                                 concurrency=self.conc, logger=self.log,
                                 label=label)

    def _propose(self, incumbent, inc_eval, gen, avoid_modes):
        digest = failure_digest(inc_eval["records"])
        mem_view = self.memory.view_for_proposer(m=8)
        steers = proposer_mod._steers_for(digest, self.cfg["K"], self.prng)
        # avoid recently tried modes on a QD restart
        if avoid_modes:
            steers = [s for s in proposer_mod.DEFAULT_STEERS
                      if s not in avoid_modes][:self.cfg["K"]] or steers
        self.log("  proposing K=%d candidates..." % self.cfg["K"])

        def one(steer):
            return proposer_mod.propose_candidate(
                self.model, incumbent, digest, mem_view, steer,
                inc_eval["score"], inc_eval["n"])

        results = [None] * len(steers)
        if self.conc > 1 and len(steers) > 1:
            with ThreadPoolExecutor(max_workers=min(self.conc,
                                                    len(steers))) as ex:
                futs = {ex.submit(one, s): i for i, s in enumerate(steers)}
                for fut in futs:
                    results[futs[fut]] = fut.result()
        else:
            for i, s in enumerate(steers):
                results[i] = one(s)

        cands, infos = [], []
        cost = {"model_tokens": 0, "cost_usd": 0.0}
        for cand, info in results:
            infos.append(info)
            u = info.get("proposer_usage")
            if u:
                cost["model_tokens"] += u["input_tokens"] + u["output_tokens"]
                cost["cost_usd"] += u["cost_usd"]
            if cand is not None:
                cands.append((cand, info))
            else:
                self.log("    candidate dropped: %s" % info.get("error"))
        return cands, infos, cost

    def _gate_eval(self, cands, prop_infos, train, gen):
        cand_evals = []
        for cand, info in cands:
            ev = self._eval(cand, train, "gen%d-cand:%s"
                            % (gen, info.get("label", "?")))
            if ev.get("violation"):
                # a candidate that tried to escape scope: record + skip; the
                # violation flag will halt the run at the next check.
                ev["scaffold"] = cand
                ev["info"] = info
                cand_evals.append(ev)
                break
            ev["scaffold"] = cand
            ev["info"] = info
            cand_evals.append(ev)
            self.log("    candidate %-14s TRAIN solved %d/%d"
                     % (info.get("label", "?"), ev["solved"], ev["n"]))
        return cand_evals

    def _prop_summary(self, info):
        return {"label": info.get("label"),
                "steer": info.get("steer"),
                "targeted_failure_mode": info.get("targeted_failure_mode"),
                "predicted_effect": info.get("predicted_effect"),
                "rationale": (info.get("rationale") or "")[:300],
                "sha": info.get("sha"),
                "dropped_reason": info.get("error")}

    def _halt_on_violation(self, ev, gen):
        if ev.get("violation"):
            self.ledger.append("HALT", {
                "generation": gen, "reason": "violation",
                "detail": ev["violation"]})
            self.log("  AUTO-HALT: scope-escape / grading-asset access "
                     "attempt: %s (ledger preserved)" % ev["violation"])
            return True
        return False

    def _check_halts(self, gen, gen_tokens, gen_baseline, regressions):
        tot = self.model.session_totals()
        if self.session_cost_cap is not None and \
                tot["cost_usd"] >= self.session_cost_cap:
            return ("budget_exhausted: session cost $%.4f >= cap $%.4f"
                    % (tot["cost_usd"], self.session_cost_cap))
        if gen_baseline and gen > 1 and \
                gen_tokens > self.cfg["gen_budget_multiple"] * gen_baseline:
            return ("generation_overspend: %d tokens > %.1fx baseline %d"
                    % (gen_tokens, self.cfg["gen_budget_multiple"],
                       gen_baseline))
        if regressions >= self.cfg["regression_halt"]:
            return ("heldout_regression: %d consecutive generations"
                    % regressions)
        return None

    def _print_curve(self, curve):
        cells = "  ".join("g%d:%.2f" % (i, s) for i, s in enumerate(curve))
        self.log("  HELD-OUT CURVE: %s" % cells)

    def _finalize(self, curve, gen0_sha, halted, halt_reason=None,
                  best_sha=None):
        best = max(curve) if curve else 0.0
        summary = {
            "curve": curve,
            "gen0_heldout": curve[0] if curve else None,
            "best_heldout": best,
            "gen0_vs_best_delta": round(best - (curve[0] if curve else 0.0), 4),
            "generations_run": len(curve) - 1,
            "halted": halted,
            "halt_reason": halt_reason,
            "best_sha": best_sha or gen0_sha,
            "session_totals": self.model.session_totals(),
            "config_sha": config_sha(self.cfg),
        }
        self.ledger.append("FINAL", summary)
        return summary
