"""The adoption gate -- the engine's SELECTION OPERATOR (directive section 2/4).

A candidate is adopted iff it strictly beats the incumbent on the SAME train
tasks/seeds/budget: more train tasks solved. Ties go to the incumbent. Among
several candidates that beat the incumbent, the strict winner is the one with
the most train solves, breaking ties toward fewer model tokens spent, then by
scaffold sha for determinism. This is how a variation becomes an improvement;
without it, drift accumulates and calls itself progress.
"""


def select_winner(incumbent_eval, candidate_evals):
    """incumbent_eval, candidate_evals[i]: dicts from evaluate_scaffold, each
    carrying the candidate scaffold under key 'scaffold' and its proposer
    'info'. Returns (winner_dict, decision)."""
    inc_solved = incumbent_eval["solved"]
    beats = []
    for ce in candidate_evals:
        if ce is None:
            continue
        if ce["solved"] > inc_solved:            # STRICT improvement only
            beats.append(ce)

    decision = {
        "incumbent_solved": inc_solved,
        "incumbent_score": incumbent_eval["score"],
        "n_candidates": len([c for c in candidate_evals if c is not None]),
        "n_beating": len(beats),
        "candidate_summ": [
            {"label": c["info"].get("label"),
             "targeted_failure_mode": c["info"].get("targeted_failure_mode"),
             "solved": c["solved"], "score": c["score"],
             "model_tokens": c["meter"]["model_tokens"],
             "sha": c["sha"], "beats_incumbent": c["solved"] > inc_solved}
            for c in candidate_evals if c is not None
        ],
    }

    if not beats:
        decision["adopted"] = False
        decision["winner_sha"] = incumbent_eval["sha"]
        return None, decision

    beats.sort(key=lambda c: (-c["solved"], c["meter"]["model_tokens"],
                              c["sha"]))
    winner = beats[0]
    decision["adopted"] = True
    decision["winner_sha"] = winner["sha"]
    decision["winner_label"] = winner["info"].get("label")
    decision["winner_solved"] = winner["solved"]
    decision["winner_targeted_failure_mode"] = \
        winner["info"].get("targeted_failure_mode")
    decision["train_delta"] = winner["solved"] - inc_solved
    return winner, decision
