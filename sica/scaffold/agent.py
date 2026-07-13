# GEN0 agent: plan -> act -> verify, with retry/backtrack. Defines solve().
# The engine rewrites this loop (and the helpers it calls) to lift held-out
# solve rate. It must always define solve(ctx, task).


def solve(ctx, task):
    allowed = task.editable_files
    files = read_editable(ctx, task)

    test_feedback = ""
    if SHOW_PUBLIC_TESTS:
        try:
            baseline = ctx.run_tests()
            test_feedback = summarize_tests(baseline)
        except Exception as e:            # noqa -- best effort baseline
            test_feedback = "could not run tests: %s" % e

    extra = ""
    try:
        extra = gather_context(ctx, task)
    except Exception:                     # noqa
        extra = ""

    history = []
    for attempt in range(MAX_ATTEMPTS):
        ctx.step()
        prompt = build_fix_prompt(task, files, allowed, history,
                                  test_feedback, extra)
        reply = ctx.model(prompt, system=SYSTEM_PROMPT,
                          max_tokens=MODEL_MAX_TOKENS)
        patch = parse_patch(reply, allowed)
        if not patch:
            history.append("Your reply had no parseable '### FILE:' blocks. "
                           "Re-send using the exact required format.")
            continue

        apply_patch(ctx, patch, allowed)
        for path in patch:
            files[path] = patch[path]

        try:
            result = ctx.run_tests()
        except Exception as e:            # noqa
            history.append("Running the tests raised: %s" % e)
            continue

        if tests_green(result):
            ctx.log("solved on attempt %d" % (attempt + 1))
            return

        test_feedback = summarize_tests(result)
        history.append("The visible tests still fail:\n%s"
                       % summarize_tests(result))

    ctx.log("exhausted %d attempts; leaving best effort in place"
            % MAX_ATTEMPTS)
