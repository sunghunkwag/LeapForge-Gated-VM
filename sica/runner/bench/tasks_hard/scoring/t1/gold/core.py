from weights import W_CORRECT, W_PARTIAL, W_WRONG

def score(correct, partial, wrong):
    return correct * W_CORRECT + partial * W_PARTIAL + wrong * W_WRONG
