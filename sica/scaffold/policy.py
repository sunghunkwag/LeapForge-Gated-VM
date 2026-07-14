# GEN0 policy knobs. The engine may tune these or replace this file wholesale.
# Kept small and explicit so a proposal can target one failure mode at a time.

MAX_ATTEMPTS = 3            # plan->act->verify iterations before giving up
MODEL_MAX_TOKENS = 4096     # per completion
SHOW_PUBLIC_TESTS = True    # run public tests to get a baseline before editing
INCLUDE_TEST_SOURCE = False # include the public test source in the prompt
GREP_CONTEXT = True         # gather extra context by searching the repo
MAX_CONTEXT_CHARS = 12000   # cap on file text placed in a single prompt
