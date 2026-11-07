#!/usr/bin/env python3
"""
exact_seriation.py

Exact enumeration of the largest subsets of assemblages that form a valid
frequency seriation, and every valid ordering of each such subset.

Definition of a valid seriation
-------------------------------
An ordering is valid if, for every type, the frequencies along the ordering
are unimodal. A sequence is unimodal if and only if no element lies below
both an earlier and a later element. So an ordering is valid if and only if
no triple of positions a < b < c has, for some type t,

    f[b, t]  <  min(f[a, t], f[c, t])     (a "dip")

Two criteria for what counts as a dip are available:

  --tol T      dip if f[b,t] < min(f[a,t], f[c,t]) - T   (T in proportion units;
               T = 0 gives strict unimodality)
  --ci LEVEL   dip if the upper bootstrap confidence bound of f[b,t] lies below
               the lower bounds of both f[a,t] and f[c,t]. Bounds come from
               multinomial resampling of each assemblage's counts.
               (This criterion is defined here; it is not claimed to reproduce
               the IDSS criterion exactly.)

Both criteria are defined on triples, which gives the property the search
uses:

  Heredity: if an ordering is valid, deleting any assemblage leaves a valid
  ordering, because every triple of the shorter sequence is also a triple of
  the longer one.

Algorithm
---------
Depth-first branch and bound, structured like exact maximum-clique search.

  * Assemblages are added in a fixed order. Each new assemblage is inserted
    into every position of the current ordering at which it creates no dip.
    Every ordering of every subset is generated exactly once: the relative
    order of the first m assemblages added is fixed by the final ordering.
  * By heredity, an assemblage that cannot be inserted anywhere in the
    current ordering cannot be added to any extension of it. Each node keeps
    only candidates that still have at least one valid insertion position.
  * Bound: if (current size + remaining candidates) < best size found, the
    branch is abandoned. Ties are kept, so all largest solutions are found.
  * Mirror-image orderings are counted once: the second assemblage added is
    always placed to the right of the first.

The result is exact: every maximum-size valid subset and every valid ordering
of it (up to reversal) is reported. The worst case is exponential; run time
depends on how many subsets and orderings are valid in the data.

Usage
-----
  python exact_seriation.py --csv data.csv --tol 0.02
  python exact_seriation.py --csv data.csv --ci 0.95 --boot 1000
  python exact_seriation.py --synthetic 30 --tol 0.03      # test data
  python exact_seriation.py --verify                       # brute-force check

CSV format: first column = assemblage name, remaining columns = type counts
(header row required). Counts are needed for --ci; proportions work for --tol.
"""

import argparse
import csv
import itertools
import math
import random
import sys
import time

import numpy as np


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def read_csv(path):
    names, rows = [], []
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for r in reader:
            if not r or not r[0].strip():
                continue
            names.append(r[0].strip())
            rows.append([float(v) for v in r[1:]])
    return names, np.array(rows, dtype=float), header[1:]


def synthetic_counts(n, n_types=8, n_outliers=None, sample_size=200, seed=1):
    """SYNTHETIC test data, not archaeological.

    n - n_outliers assemblages are drawn along a time axis from Gaussian
    popularity curves (one per type) with multinomial sampling error. The
    remaining assemblages are mixtures of two distant time points, which
    should not fit a single seriation.
    """
    rng = np.random.default_rng(seed)
    if n_outliers is None:
        n_outliers = max(1, n // 5)
    n_good = n - n_outliers
    times = np.sort(rng.uniform(0, 1, n_good))
    peaks = np.linspace(-0.1, 1.1, n_types)
    width = 0.18

    def popularity(t):
        w = np.exp(-0.5 * ((t - peaks) / width) ** 2) + 1e-3
        return w / w.sum()

    rows = [rng.multinomial(sample_size, popularity(t)) for t in times]
    for _ in range(n_outliers):
        t1, t2 = rng.uniform(0, 0.3), rng.uniform(0.7, 1.0)
        p = 0.5 * popularity(t1) + 0.5 * popularity(t2)
        rows.append(rng.multinomial(sample_size, p))
    rows = np.array(rows, dtype=float)
    perm = rng.permutation(n)                 # hide the true order
    true_rank = np.empty(n, dtype=int)
    true_rank[np.arange(n)] = -1
    names = []
    for new_i, old_i in enumerate(perm):
        tag = f"T{old_i:02d}" if old_i < n_good else f"X{old_i - n_good:02d}"
        names.append(f"A{new_i:02d}_{tag}")
    return names, rows[perm]


# ---------------------------------------------------------------------------
# Dip tensor: bad[i, j, k] = True if j placed between i and k creates a dip
# ---------------------------------------------------------------------------

def dip_tensor_tol(f, tol):
    mins = np.minimum(f[:, None, :], f[None, :, :])            # (i, k, t)
    return (f[None, :, None, :] < mins[:, None, :, :] - tol).any(axis=-1)


def bootstrap_bounds(counts, level, n_boot, seed):
    rng = np.random.default_rng(seed)
    n, t = counts.shape
    lo = np.empty((n, t))
    hi = np.empty((n, t))
    alpha = (1.0 - level) / 2.0
    for i in range(n):
        size = int(round(counts[i].sum()))
        p = counts[i] / counts[i].sum()
        sims = rng.multinomial(size, p, size=n_boot) / size
        lo[i] = np.quantile(sims, alpha, axis=0)
        hi[i] = np.quantile(sims, 1.0 - alpha, axis=0)
    return lo, hi


def dip_tensor_ci(lo, hi):
    mins_lo = np.minimum(lo[:, None, :], lo[None, :, :])       # (i, k, t)
    return (hi[None, :, None, :] < mins_lo[:, None, :, :]).any(axis=-1)


# ---------------------------------------------------------------------------
# Insertion test
# ---------------------------------------------------------------------------

def valid_positions(bad, order, x):
    """Positions p (0..k) at which x can be inserted before order[p]
    without creating a dip. order is a list of assemblage indices."""
    k = len(order)
    if k < 2:
        return list(range(k + 1))
    O = np.asarray(order)
    # x first in triple: (x, O[b], O[c]) with p <= b < c
    F = np.triu(bad[x][np.ix_(O, O)], 1).sum(axis=1)               # per b
    countF = np.concatenate([np.cumsum(F[::-1])[::-1], [0]])
    # x last in triple: (O[a], O[b], x) with a < b < p
    L = np.triu(bad[np.ix_(O, O)][:, :, x], 1).sum(axis=0)         # per b
    countL = np.concatenate([[0], np.cumsum(L)])
    # x in middle: (O[a], x, O[c]) with a < p <= c
    M = bad[np.ix_(O, [x], O)][:, 0, :].astype(np.int64)           # (a, c)
    suf = np.zeros((k, k + 1), dtype=np.int64)
    suf[:, :k] = np.cumsum(M[:, ::-1], axis=1)[:, ::-1]            # sum c >= p
    countM = np.triu(suf, 1).sum(axis=0)                           # a < p
    ok = (countF + countL + countM) == 0
    return [int(p) for p in np.flatnonzero(ok)]


# ---------------------------------------------------------------------------
# Branch and bound
# ---------------------------------------------------------------------------

class Search:
    def __init__(self, bad, max_solutions=100000, progress=0):
        self.bad = bad
        self.n = bad.shape[0]
        self.best = 0
        self.solutions = []
        self.n_orderings = 0          # all orderings of best size, stored or not
        self.subsets = set()          # all subsets of best size
        self.nodes = 0
        self.max_solutions = max_solutions
        self.truncated = False
        self.progress = progress
        self.t0 = time.time()

    def record(self, order):
        k = len(order)
        if k > self.best:
            self.best = k
            self.solutions = [tuple(order)]
            self.n_orderings = 1
            self.subsets = {frozenset(order)}
            self.truncated = False
            if self.progress:
                print(f"  [{time.time() - self.t0:8.1f}s] new best size {k}",
                      flush=True)
        elif k == self.best:
            self.n_orderings += 1
            self.subsets.add(frozenset(order))
            if len(self.solutions) < self.max_solutions:
                self.solutions.append(tuple(order))
            else:
                self.truncated = True

    def dfs(self, order, cands):
        """cands: list of (x, positions) in search order, each with >= 1
        valid insertion position in `order`."""
        self.nodes += 1
        if self.progress and self.nodes % self.progress == 0:
            print(f"  [{time.time() - self.t0:8.1f}s] nodes={self.nodes:,} "
                  f"best={self.best} solutions={len(self.solutions)}", flush=True)
        self.record(order)
        k = len(order)
        for idx, (x, positions) in enumerate(cands):
            if k + len(cands) - idx < self.best:
                return
            if k == 1:
                positions = [1]          # break mirror symmetry
            rest = cands[idx + 1:]
            for p in positions:
                new = order[:p] + [x] + order[p:]
                new_cands = []
                for y, _ in rest:
                    pos = valid_positions(self.bad, new, y)
                    if pos:
                        new_cands.append((y, pos))
                if k + 1 + len(new_cands) < self.best:
                    continue
                self.dfs(new, new_cands)

    def run(self, search_order):
        cands = [(x, [0]) for x in search_order]
        self.dfs([], cands)
        return self


class CResult:
    """Result object from the compiled engine, same fields the report uses."""


def run_c_engine(bad, order, max_solutions, time_limit, binary, verbose=1):
    import os
    import subprocess
    import tempfile
    n = bad.shape[0]
    with tempfile.TemporaryDirectory() as tmp:
        fin = os.path.join(tmp, "in.bin")
        fout = os.path.join(tmp, "out.txt")
        with open(fin, "wb") as fh:
            fh.write(np.array([n], dtype="<i4").tobytes())
            fh.write(np.array(order, dtype="<i4").tobytes())
            fh.write(np.ascontiguousarray(bad, dtype=np.uint8).tobytes())
        subprocess.run([binary, fin, fout, str(max_solutions), str(time_limit),
                        str(verbose)],
                       check=True)
        with open(fout) as fh:
            head = fh.readline().split()
            sols, subset_counts = [], {}
            for line in fh:
                parts = line.split()
                if not parts:
                    continue
                if parts[0] == "S":
                    subset_counts[frozenset(int(v) for v in parts[2:])] = int(parts[1])
                else:
                    sols.append(tuple(int(v) for v in parts))
    r = CResult()
    r.best = int(head[0])
    r.n_orderings = int(head[1])
    r.n_subsets = int(head[2])
    r.nodes = int(head[3])
    r.truncated = bool(int(head[4]))
    r.timed_out = bool(int(head[5]))
    r.solutions = sols
    r.subset_counts = subset_counts
    return r


def find_binary():
    import os
    import shutil
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "seriate_core"), shutil.which("seriate_core")):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def search_order(bad):
    """Assemblages that take part in fewer dips go first, which tends to find
    large solutions early and tighten the bound."""
    n = bad.shape[0]
    involvement = bad.sum(axis=(0, 2)) + bad.sum(axis=(1, 2)) + bad.sum(axis=(0, 1))
    return [int(i) for i in np.argsort(involvement, kind="stable")]


def group_by_subset(solutions):
    groups = {}
    for o in solutions:
        groups.setdefault(frozenset(o), []).append(o)
    return groups


# ---------------------------------------------------------------------------
# Brute-force verification
# ---------------------------------------------------------------------------

def ordering_ok(bad, order):
    for a, b, c in itertools.combinations(range(len(order)), 3):
        if bad[order[a], order[b], order[c]]:
            return False
    return True


def brute_force(bad):
    n = bad.shape[0]
    for k in range(n, 0, -1):
        found = set()
        for subset in itertools.combinations(range(n), k):
            for perm in itertools.permutations(subset):
                if perm[0] > perm[-1] and k > 1:
                    continue
                if ordering_ok(bad, perm):
                    found.add(perm)
        if found:
            return k, found
    return 0, set()


def canonical(o):
    return o if len(o) < 2 or o[0] < o[-1] else tuple(reversed(o))


def verify(trials=200, seed=0, binary=None):
    rng = np.random.default_rng(seed)
    print(f"Verifying {'compiled' if binary else 'Python'} engine against brute force "
          f"on {trials} random matrices ...")
    for trial in range(trials):
        n = int(rng.integers(3, 9))
        t = int(rng.integers(2, 6))
        if trial % 2 == 0:
            f = rng.dirichlet(np.ones(t), size=n)
        else:  # partly seriated data, to produce larger solutions
            times = rng.uniform(0, 1, n)
            peaks = np.linspace(0, 1, t)
            f = np.exp(-0.5 * ((times[:, None] - peaks) / 0.3) ** 2)
            f += rng.uniform(0, 0.15, f.shape)
            f /= f.sum(axis=1, keepdims=True)
        tol = float(rng.choice([0.0, 0.01, 0.05]))
        bad = dip_tensor_tol(f, tol)
        if binary:
            s = run_c_engine(bad, search_order(bad), 10**6, 0, binary, verbose=0)
        else:
            s = Search(bad).run(search_order(bad))
        k_bf, sols_bf = brute_force(bad)
        sols_bb = {canonical(o) for o in s.solutions}
        if s.best != k_bf or sols_bb != sols_bf or len(s.solutions) != len(sols_bb):
            print(f"MISMATCH trial {trial}: n={n} tol={tol} "
                  f"bb=({s.best},{len(s.solutions)}) bf=({k_bf},{len(sols_bf)})")
            return False
    print(f"All {trials} trials match: same maximum size, same set of orderings, "
          "no duplicates.")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--csv", help="frequency table: name, type counts ...")
    src.add_argument("--synthetic", type=int, metavar="N",
                     help="generate N synthetic assemblages (test data)")
    src.add_argument("--verify", action="store_true",
                     help="check the solver against brute force and exit")
    crit = ap.add_mutually_exclusive_group()
    crit.add_argument("--tol", type=float, default=None,
                      help="dip tolerance in proportion units (default 0)")
    crit.add_argument("--ci", type=float, default=None,
                      help="bootstrap confidence level, e.g. 0.95")
    ap.add_argument("--boot", type=int, default=1000, help="bootstrap replicates")
    ap.add_argument("--min-sample", type=float, default=0,
                    help="exclude assemblages with fewer than this many counts")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-solutions", type=int, default=100000)
    ap.add_argument("--progress", type=int, default=100000,
                    help="print status every N nodes (0 = off)")
    ap.add_argument("--engine", choices=["auto", "c", "python"], default="auto",
                    help="auto = compiled engine if seriate_core is present")
    ap.add_argument("--time-limit", type=float, default=0,
                    help="stop after this many seconds (compiled engine; 0 = none)")
    ap.add_argument("--out", default="seriation_solutions.csv")
    args = ap.parse_args()

    binary = find_binary() if args.engine in ("auto", "c") else None
    if args.engine == "c" and not binary:
        sys.exit("Compiled engine not found. Build it with: "
                 "gcc -O3 -o seriate_core seriate_core.c")

    if args.verify:
        ok = verify()
        if binary:
            ok = verify(binary=binary) and ok
        sys.exit(0 if ok else 1)

    if args.csv:
        names, counts, _ = read_csv(args.csv)
    else:
        n = args.synthetic or 30
        names, counts = synthetic_counts(n, seed=args.seed)
        print("Using SYNTHETIC test data (not archaeological). Names ending T## are "
              "drawn from one time series; X## are mixtures.")
    if args.min_sample > 0:
        totals = counts.sum(axis=1)
        dropped = [nm for nm, t in zip(names, totals) if t < args.min_sample]
        keep = totals >= args.min_sample
        names = [nm for nm, k in zip(names, keep) if k]
        counts = counts[keep]
        print(f"Minimum sample size {args.min_sample:g}: excluded {len(dropped)} "
              f"assemblage(s): {', '.join(dropped) if dropped else 'none'}")
    f = counts / counts.sum(axis=1, keepdims=True)
    n = len(names)

    if args.ci is not None:
        lo, hi = bootstrap_bounds(counts, args.ci, args.boot, args.seed)
        bad = dip_tensor_ci(lo, hi)
        crit_label = f"bootstrap CI {args.ci} ({args.boot} replicates)"
    else:
        tol = args.tol or 0.0
        bad = dip_tensor_tol(f, tol)
        crit_label = f"tolerance {tol}"

    triples = n * (n - 1) * (n - 2) // 2
    n_bad = int(bad.sum()) // 2
    print(f"Assemblages: {n}  Types: {f.shape[1]}  Criterion: {crit_label}")
    print(f"Middle-placements that create a dip: {n_bad:,} of {triples:,}")

    t0 = time.time()
    if binary:
        print(f"Engine: compiled ({binary})")
        s = run_c_engine(bad, search_order(bad), args.max_solutions,
                         args.time_limit, binary)
        n_subsets = s.n_subsets
    else:
        print("Engine: Python")
        s = Search(bad, max_solutions=args.max_solutions,
                   progress=args.progress).run(search_order(bad))
        s.timed_out = False
        n_subsets = len(s.subsets)
        s.subset_counts = {}
        for o in s.solutions:
            s.subset_counts[frozenset(o)] = s.subset_counts.get(frozenset(o), 0) + 1
        if s.truncated:
            for sub in s.subsets:
                s.subset_counts.setdefault(sub, None)
    elapsed = time.time() - t0

    groups = group_by_subset(s.solutions)
    if s.timed_out:
        print(f"\nTIME LIMIT reached after {elapsed:.1f}s, {s.nodes:,} nodes. "
              "Results below are the best found so far and are NOT proven maximal "
              "or complete.")
    else:
        print(f"\nSearch finished in {elapsed:.1f}s, {s.nodes:,} nodes.")
    print(f"Largest valid subset size: {s.best} of {n}")
    print(f"Distinct largest subsets: {n_subsets}")
    print(f"Valid orderings of those subsets (mirror images counted once): "
          f"{s.n_orderings:,}")
    if s.truncated:
        print(f"NOTE: counts above are complete, but only the first "
              f"{args.max_solutions:,} orderings are listed and written to file. "
              "Raise --max-solutions for a complete list.")
        missing = n_subsets - len(groups)
        if missing:
            print(f"      {missing} subset(s) have no stored ordering.")

    for gi, (subset, orders) in enumerate(sorted(groups.items(),
                                                 key=lambda kv: sorted(kv[0]))):
        if gi >= 10:
            print(f"  ... {len(groups) - 10} more subsets in {args.out}")
            break
        excluded = [names[i] for i in range(n) if i not in subset]
        print(f"\n  Subset {gi + 1}: {len(orders)} ordering(s); excluded: "
              f"{', '.join(excluded) if excluded else 'none'}")
        for o in orders[:3]:
            print("    " + " - ".join(names[i] for i in o))
        if len(orders) > 3:
            print(f"    ... {len(orders) - 3} more")

    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["subset_id", "ordering_id", "position", "assemblage"])
        oid = 0
        for gi, (subset, orders) in enumerate(sorted(groups.items(),
                                                     key=lambda kv: sorted(kv[0]))):
            for o in orders:
                oid += 1
                for pos, i in enumerate(o, start=1):
                    w.writerow([gi + 1, oid, pos, names[i]])
    sub_out = args.out.rsplit(".", 1)[0] + "_subsets.csv"
    ranked = sorted(s.subset_counts.items(), key=lambda kv: sorted(kv[0]))
    with open(sub_out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["subset_id", "n_orderings", "included", "excluded"])
        for gi, (sub, cnt) in enumerate(ranked, start=1):
            inc = "; ".join(names[i] for i in sorted(sub))
            exc = "; ".join(names[i] for i in range(n) if i not in sub)
            w.writerow([gi, "" if cnt is None else cnt, inc, exc])
    if ranked:
        core = frozenset.intersection(*[sub for sub, _ in ranked])
        print(f"\nAssemblages in every largest subset ({len(core)}): "
              + ", ".join(names[i] for i in sorted(core)))
        other = frozenset.union(*[sub for sub, _ in ranked]) - core
        print(f"Assemblages in some but not all ({len(other)}): "
              + ", ".join(names[i] for i in sorted(other)))
    print(f"\nAll subsets written to {sub_out}")
    print(f"Orderings written to {args.out}")


if __name__ == "__main__":
    main()
