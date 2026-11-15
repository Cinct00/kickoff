"""Graph algorithms over the file graph: PageRank and strongly connected components."""
from __future__ import annotations


def pagerank(nodes: list, edges: dict, personalization: dict | None = None, damping: float = 0.85,
             iters: int = 30, tol: float = 1e-6) -> dict:
    """edges: {src: {dst: weight}}. Returns {node: score} summing to 1."""
    n = len(nodes)
    if n == 0:
        return {}
    if personalization:
        total = sum(personalization.values()) or 1.0
        pers = {k: v / total for k, v in personalization.items() if k in edges or k in set(nodes)}
    else:
        pers = None
    base = {v: (pers.get(v, 0.0) if pers else 1.0 / n) for v in nodes}
    out_w = {s: sum(d.values()) for s, d in edges.items()}
    dangling_nodes = [v for v in nodes if not out_w.get(v)]
    rank = dict(base) if pers else {v: 1.0 / n for v in nodes}
    for _ in range(iters):
        new = {v: (1 - damping) * base[v] for v in nodes}
        dangling = sum(rank[v] for v in dangling_nodes)
        for v in nodes:
            new[v] += damping * dangling * base[v]
        for s, dsts in edges.items():
            w = out_w.get(s)
            if not w:
                continue
            share = damping * rank.get(s, 0.0) / w
            for d, wt in dsts.items():
                if d in new:
                    new[d] += share * wt
        diff = sum(abs(new[v] - rank[v]) for v in nodes)
        rank = new
        if diff < tol:
            break
    return rank


def strongly_connected(nodes: list, edges: dict) -> list:
    """Tarjan's algorithm (iterative). Returns components with more than one node."""
    index, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]
    for start in nodes:
        if start in index:
            continue
        work = [(start, iter(edges.get(start, {})))]
        index[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on.add(start)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(edges.get(w, {}))))
                    advanced = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    out.append(comp)
    return sorted(out, key=len, reverse=True)
