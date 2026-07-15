def top_k(xs, k):
    counts = {}; order = []
    for v in xs:
        if v not in counts:
            counts[v]=0; order.append(v)
        counts[v]+=1
    ranked = sorted(order, key=lambda v: (-counts[v], order.index(v)))
    return ranked[:k]
