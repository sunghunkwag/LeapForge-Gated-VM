"""Section-7 report: capability-focused, read straight from the ledger.

  - the held-out solve-rate curve per generation (the headline);
  - the best scaffold's adopted change-list with rationales;
  - what the improvement memory learned paid off / didn't;
  - meter totals (so a gain is visibly not just more compute);
  - GEN0 vs best held-out delta, plainly stated;
  - an honest note if the curve is flat.
"""

import json
import os

from . import config
from .ledger import Ledger
from .memory import ImprovementMemory


def _heldout_delta(gen_recs, generation):
    prev = next((b["heldout_score"] for b in gen_recs
                 if b["generation"] == generation - 1), None)
    cur = next((b["heldout_score"] for b in gen_recs
                if b["generation"] == generation), None)
    if prev is None or cur is None:
        return 0.0
    return cur - prev


def _find_ledger(profile, seed):
    # config_sha depends on backend, so try each backend, then glob by seed.
    import glob
    hits = sorted(glob.glob(os.path.join(config.LEDGER_DIR,
                            "run_*_seed%s*.jsonl" % seed)),
                  key=os.path.getmtime, reverse=True)
    if hits:
        return hits[0], None
    cfg = config.make_config(profile, "stub", seed)
    return (os.path.join(config.LEDGER_DIR, "run_%s_seed%s.jsonl"
            % (config.config_sha(cfg), seed)), None)


def report(profile="smoke", seed="s1", ledger_path=None):
    if ledger_path is None:
        ledger_path, csha = _find_ledger(profile, seed)
    if not os.path.exists(ledger_path):
        print("no ledger at %s" % ledger_path)
        return 1
    led = Ledger(ledger_path)
    led.verify()
    gen_recs = [r["body"] for r in led.find("GEN")]
    gen_recs.sort(key=lambda b: b["generation"])
    genesis = led.find("GENESIS")
    final = led.find("FINAL")
    halts = led.find("HALT")

    print("=" * 70)
    print("SICA held-out capability report")
    print("=" * 70)
    if genesis:
        g = genesis[0]["body"]
        print("model (pinned) : %s   backend=%s   temp(req)=%s"
              % (g["model_pinned"], g["model_backend"],
                 g.get("model_temperature_requested")))
        bp = g.get("benchmark_pin", {})
        print("benchmark      : %s  %d tasks / %d repos  sha=%s"
              % (bp.get("benchmark"), bp.get("n_tasks"), bp.get("n_repos"),
                 str(bp.get("content_sha256"))[:16]))
        print("split          : %d train / %d heldout (repo-disjoint)"
              % (len(g.get("train_ids", [])), len(g.get("heldout_ids", []))))
        print("isolation      : %s" % g.get("isolation"))
        print("guardrails     : %s" % " ".join(g.get("guardrails", [])))

    # --- the headline: held-out curve ---
    print("\nHELD-OUT SOLVE-RATE CURVE (the one metric):")
    print("  %-5s %-10s %-10s %-8s %s" %
          ("gen", "heldout%", "solved/n", "adopted", "change"))
    for b in gen_recs:
        pct = 100.0 * b["heldout_score"]
        adopted = b.get("adopted")
        label = ""
        if b["generation"] > 0:
            gate = b.get("gate", {})
            label = (gate.get("winner_label") or "(kept incumbent)"
                     if adopted else "(kept incumbent)")
        print("  g%-4d %6.1f%%    %3d/%-4d   %-8s %s"
              % (b["generation"], pct, b["heldout_solved"], b["heldout_n"],
                 "yes" if adopted and b["generation"] > 0 else
                 ("baseline" if b["generation"] == 0 else "no"), label))

    # --- adopted change list w/ rationales ---
    print("\nADOPTED CHANGES (best scaffold's lineage), with rationale:")
    any_adopt = False
    for b in gen_recs:
        if b["generation"] == 0 or not b.get("adopted"):
            continue
        any_adopt = True
        gate = b.get("gate", {})
        props = b.get("proposals", [])
        win = None
        for p in props:
            if p.get("label") == gate.get("winner_label"):
                win = p
                break
        print("  gen %d: adopt '%s' (train +%s)"
              % (b["generation"], gate.get("winner_label"),
                 gate.get("train_delta")))
        print("     mode     : %s" % gate.get("winner_targeted_failure_mode"))
        if win:
            print("     rationale: %s" % (win.get("rationale") or "")[:200])
            print("     predicted: %s   measured heldout delta: %+.3f"
                  % (win.get("predicted_effect"),
                     _heldout_delta(gen_recs, b["generation"])))
    if not any_adopt:
        print("  (no change was ever adopted -- every candidate tied or lost "
              "the gate)")

    # --- what memory learned ---
    csha = (genesis[0]["body"]["config_sha"] if genesis else "")
    run_id = (genesis[0]["body"].get("run_id", "") if genesis else "")
    mem_path = os.path.join(config.MEMORY_DIR,
                            "improvement_%s_%s.jsonl" % (csha, run_id))
    if os.path.exists(mem_path):
        mem = ImprovementMemory(mem_path)
        print("\nIMPROVEMENT MEMORY -- did the change kind pay off?")
        for e in mem.full_log():
            print("  gen %s: mode=%s  train_delta=%s  heldout_delta=%+.3f  "
                  "adopted=%s" % (e.get("generation"),
                                  e.get("targeted_failure_mode"),
                                  e.get("measured_train_delta"),
                                  e.get("measured_heldout_delta") or 0.0,
                                  e.get("adopted")))

    # --- meters ---
    print("\nMETER TOTALS (a gain must not be just more compute):")
    tot_tokens = tot_cost = 0
    for b in gen_recs:
        tot_tokens += b.get("gen_model_tokens", 0)
        tot_cost += b.get("gen_cost_usd", 0.0)
    print("  model tokens (all gens): %d" % tot_tokens)
    print("  cost (all gens)        : $%.4f" % tot_cost)
    if final:
        st = final[0]["body"].get("session_totals", {})
        print("  session model calls    : %s" % st.get("calls"))

    # --- gen0 vs best, plainly ---
    if final:
        f = final[0]["body"]
        print("\nGEN0 vs BEST HELD-OUT (plainly stated):")
        print("  GEN0 held-out : %.1f%%" % (100.0 * (f.get("gen0_heldout")
                                                     or 0.0)))
        print("  BEST held-out : %.1f%%" % (100.0 * (f.get("best_heldout")
                                                     or 0.0)))
        print("  DELTA         : %+.1f percentage points"
              % (100.0 * (f.get("gen0_vs_best_delta") or 0.0)))
        if f.get("halted"):
            print("  RUN HALTED    : %s" % f.get("halt_reason"))

        # --- honest verdict ---
        delta = f.get("gen0_vs_best_delta") or 0.0
        gen0 = f.get("gen0_heldout") or 0.0
        print("\nVERDICT:")
        if gen0 >= 0.999 and abs(delta) < 1e-9:
            print("  CEILING (benchmark saturated): GEN0 already solved 100%% "
                  "of held-out, so there was NO HEADROOM for the curve to rise "
                  "-- this is a benchmark-difficulty result, NOT evidence about "
                  "self-modification. The engine machinery (proposals, gate, "
                  "memory, archive, QD escape, T8, meters, isolation) ran "
                  "end-to-end and the gate correctly kept the incumbent (a "
                  "candidate cannot strictly beat a perfect score). To test the "
                  "curve, the held-out slice must be hard enough that GEN0 "
                  "fails a meaningful fraction.")
        elif abs(delta) < 1e-9:
            print("  FLAT: self-modification did not improve held-out "
                  "capability at this scale (GEN0 left headroom but no adopted "
                  "change lifted the number). A legitimate result, reported as "
                  "one (directive section 7/9).")
        elif delta > 0:
            print("  Held-out capability ROSE by %+.1f pts across %d "
                  "generations. Small-n; read as a machinery-and-direction "
                  "result, not a powered claim."
                  % (100.0 * delta, f.get("generations_run")))
        else:
            print("  Held-out capability FELL. Self-modification net-hurt at "
                  "this scale; reported honestly.")
    if halts:
        print("\nHALT RECORDS: %s" % json.dumps([h["body"] for h in halts]))
    print("=" * 70)
    return 0
