# Copyright (c) 2026.  Carl P. Lipo.
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.
"""
Exact branch-and-bound search for the largest frequency seriation solutions (--search=exact).

The search finds every subset of assemblages of the largest size that has a valid ordering,
and every valid ordering of each such subset (mirror images counted once), with proof that
none is missed. It uses the every-triple criterion (--dipcriterion=triple): an ordering is
invalid if, for some type, an assemblage is lower than both an earlier and a later assemblage
(with bootstrap intervals: its upper bound is below both lower bounds). Under this criterion a
valid ordering stays valid when any assemblage is removed, and the search relies on that:

  * assemblages are added in a fixed order, and each is inserted at every position of the
    current ordering where it creates no violation, so every ordering of every subset is
    generated exactly once;
  * an assemblage that cannot be inserted anywhere in the current ordering cannot be added to
    any extension of it, and is dropped from that branch;
  * a branch is abandoned when its size plus its remaining candidates is smaller than the
    largest size found; ties are kept, so all largest solutions are recorded;
  * the second assemblage added is always placed to the right of the first, so mirror images
    are generated once.

A compiled engine (seriate_core.c, in this directory) runs the same search about 100 to 300
times faster. It is used when the executable `seriate_core` is found next to this file, on the
PATH, or at the location named by the environment variable IDSS_SERIATE_CORE. Build it with:

    gcc -O3 -o seriation/seriate_core seriation/seriate_core.c

Otherwise the pure Python search below is used. Both return identical results.
"""
import os
import sys
import time
import struct
import tempfile
import subprocess
import itertools
import logging as logger


def dip_table(labels, lower, upper):
    """bad[i][j][k] is True if assemblage j placed between i and k is a violation for any type:
    upper[j][t] < min(lower[i][t], lower[k][t]). Without bootstrap intervals, pass the
    frequencies as both lower and upper."""
    n = len(labels)
    ntypes = len(lower[labels[0]])
    lo = [lower[a] for a in labels]
    hi = [upper[a] for a in labels]
    bad = [[[False] * n for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for k in range(i + 1, n):
            mins = [min(lo[i][t], lo[k][t]) for t in range(ntypes)]
            for j in range(n):
                if j == i or j == k:
                    continue
                hj = hi[j]
                for t in range(ntypes):
                    if hj[t] < mins[t]:
                        bad[i][j][k] = True
                        bad[k][j][i] = True
                        break
    return bad


def search_order(bad):
    """Assemblages taking part in fewer violations first: large solutions are found early."""
    n = len(bad)
    involvement = []
    for x in range(n):
        c = 0
        for i in range(n):
            for k in range(n):
                c += bad[x][i][k] + bad[i][x][k] + bad[i][k][x]
        involvement.append((c, x))
    involvement.sort()
    return [x for c, x in involvement]


def _full_positions(bad, order, y):
    k = len(order)
    pos = []
    for p in range(k + 1):
        ok = True
        for a in range(k):
            if not ok:
                break
            for b in range(a + 1, k):
                i, j = order[a], order[b]
                if b < p:
                    if bad[i][j][y]:
                        ok = False
                        break
                elif a < p:
                    if bad[i][y][j]:
                        ok = False
                        break
                else:
                    if bad[y][i][j]:
                        ok = False
                        break
        if ok:
            pos.append(p)
    return pos


def _update_positions(bad, new, p, x, y, positions):
    """Valid positions of y in `new` (the parent ordering with x inserted at p), given its valid
    positions in the parent. By heredity only triples containing both x and y need checking."""
    out = []
    k1 = len(new)
    allowed = set(positions)
    for q in range(k1 + 1):
        qo = q if q <= p else q - 1
        if qo not in allowed:
            continue
        if q <= p:
            first, second = y, x
        else:
            first, second = x, y
        ok = True
        for t in range(k1):
            if t == p:
                continue
            z = new[t]
            before = (t < q) + (t < p)
            if before == 2:
                if bad[z][first][second]:
                    ok = False
                    break
            elif before == 1:
                if bad[first][z][second]:
                    ok = False
                    break
            else:
                if bad[first][second][z]:
                    ok = False
                    break
        if ok:
            out.append(q)
    return out


class _PythonSearch(object):
    def __init__(self, bad, max_store):
        self.bad = bad
        self.best = 0
        self.stored = []
        self.n_orderings = 0
        self.subsets = {}
        self.nodes = 0
        self.max_store = max_store
        self.truncated = False

    def record(self, order):
        k = len(order)
        if k > self.best:
            self.best = k
            self.stored = []
            self.n_orderings = 0
            self.subsets = {}
            self.truncated = False
        if k == self.best:
            self.n_orderings += 1
            key = frozenset(order)
            self.subsets[key] = self.subsets.get(key, 0) + 1
            if len(self.stored) < self.max_store:
                self.stored.append(tuple(order))
            else:
                self.truncated = True

    def dfs(self, order, cands):
        self.nodes += 1
        self.record(order)
        k = len(order)
        for idx in range(len(cands)):
            if k + len(cands) - idx < self.best:
                return
            x, positions = cands[idx]
            if k == 1:
                positions = [1]
            rest = cands[idx + 1:]
            for p in positions:
                new = order[:p] + [x] + order[p:]
                new_cands = []
                for r in range(len(rest)):
                    if k + 1 + len(new_cands) + (len(rest) - r) < self.best:
                        break
                    y, ypos = rest[r]
                    npos = _update_positions(self.bad, new, p, x, y, ypos)
                    if npos:
                        new_cands.append((y, npos))
                if k + 1 + len(new_cands) < self.best:
                    continue
                self.dfs(new, new_cands)


def find_engine():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.environ.get("IDSS_SERIATE_CORE"), os.path.join(here, "seriate_core")]
    for d in os.environ.get("PATH", "").split(os.pathsep):
        candidates.append(os.path.join(d, "seriate_core"))
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def _run_engine(binary, bad, order, max_store):
    n = len(bad)
    tmp = tempfile.mkdtemp(prefix="idss-exact-")
    fin = os.path.join(tmp, "in.bin")
    fout = os.path.join(tmp, "out.txt")
    with open(fin, "wb") as fh:
        fh.write(struct.pack("<i", n))
        fh.write(struct.pack("<%di" % n, *order))
        buf = bytearray(n * n * n)
        idx = 0
        for i in range(n):
            for j in range(n):
                row = bad[i][j]
                for k in range(n):
                    buf[idx] = 1 if row[k] else 0
                    idx += 1
        fh.write(bytes(buf))
    subprocess.check_call([binary, fin, fout, str(max_store), "0", "0"])
    stored, subsets = [], {}
    with open(fout) as fh:
        head = fh.readline().split()
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "S":
                subsets[frozenset(int(v) for v in parts[2:])] = int(parts[1])
            else:
                stored.append(tuple(int(v) for v in parts))
    try:
        os.remove(fin)
        os.remove(fout)
        os.rmdir(tmp)
    except OSError:
        pass
    return {"best": int(head[0]), "n_orderings": int(head[1]), "nodes": int(head[3]),
            "truncated": bool(int(head[4])), "stored": stored, "subsets": subsets}


def exact_search(labels, lower, upper, max_store=100000, engine="auto"):
    """Run the search. labels: list of assemblage names; lower/upper: dicts name -> list of
    per-type bounds (pass the frequencies for both when bootstrap intervals are not used).
    Returns a dict with the largest size, every largest subset with its number of orderings,
    the stored orderings (as lists of names), counts and the engine used."""
    t0 = time.time()
    bad = dip_table(labels, lower, upper)
    order = search_order(bad)
    binary = find_engine() if engine in ("auto", "c") else None
    if engine == "c" and binary is None:
        raise RuntimeError("--exactengine=c requested but seriate_core was not found; build it with "
                           "gcc -O3 -o seriation/seriate_core seriation/seriate_core.c")
    if binary is not None and len(labels) <= 64:
        r = _run_engine(binary, bad, order, max_store)
        used = "compiled (%s)" % binary
    else:
        s = _PythonSearch(bad, max_store)
        cands = [(x, [0]) for x in order]
        sys.setrecursionlimit(max(1000, 10 * len(labels) + 100))
        s.dfs([], cands)
        r = {"best": s.best, "n_orderings": s.n_orderings, "nodes": s.nodes,
             "truncated": s.truncated, "stored": s.stored, "subsets": s.subsets}
        used = "python"
    names = lambda seq: [labels[i] for i in seq]
    return {"best": r["best"],
            "n_orderings": r["n_orderings"],
            "nodes": r["nodes"],
            "truncated": r["truncated"],
            "orderings": [names(o) for o in r["stored"]],
            "subsets": [(sorted(names(sorted(s))), c) for s, c in r["subsets"].items()],
            "engine": used,
            "seconds": time.time() - t0}
