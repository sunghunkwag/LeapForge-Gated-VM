def mode(xs):
    counts = {}
    order = []
    for v in xs:
        if v not in counts:
            counts[v] = 0; order.append(v)
        counts[v] += 1
    best = order[0]
    for v in order:
        if counts[v] < counts[best]:
            best = v
    return best
