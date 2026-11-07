"""Permutation test of the spatial pattern of a minmax graph.

Statistic: mean geographic length (km) of the graph's edges. Null distribution: site coordinates
permuted at random among the assemblages that have at least one edge, graph unchanged.
One-sided p = share of permutations with a mean edge length at or below the observed value.
This is our implementation; Lipo et al. (2015) describe their test only briefly.
"""
import json, sys
import numpy as np

def load_xy(path):
    xy = {}
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.split()
            if len(p) >= 3:
                xy[p[0]] = np.array([float(p[2]), float(p[1])]) / 1000.0
    return xy

def test(edges, xy, n_perm=10000, seed=0):
    nodes = sorted({n for e in edges for n in e})
    idx = {n: i for i, n in enumerate(nodes)}
    P = np.array([xy[n] for n in nodes])
    a = np.array([idx[e[0]] for e in edges]); b = np.array([idx[e[1]] for e in edges])
    obs = np.linalg.norm(P[a] - P[b], axis=1).mean()
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for k in range(n_perm):
        Q = P[rng.permutation(len(nodes))]
        null[k] = np.linalg.norm(Q[a] - Q[b], axis=1).mean()
    p = (np.sum(null <= obs) + 1) / (n_perm + 1)
    return obs, null.mean(), p, len(nodes), len(edges)

if __name__ == "__main__":
    xy = load_xy(sys.argv[1])
    for fn in sys.argv[2:]:
        G = json.load(open(fn))
        for tag, g in G.items():
            obs, nullmean, p, nn, ne = test([tuple(e) for e in g["edges"]], xy)
            print("%s %-4s nodes=%d edges=%d mean edge %.1f km (null mean %.1f km) p=%.4f" % (fn.split('/')[-1], tag, nn, ne, obs, nullmean, p))
