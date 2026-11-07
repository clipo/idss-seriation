# Independent brute-force checker for IDSS frequency seriation (Python 2.7).
# usage: python brute.py table.txt idss.json mode(0|1)
import sys, json, itertools, re

def read_table(fn):
    rows = [l.rstrip("\n").split("\t") for l in open(fn) if l.strip()]
    labels, props = [], {}
    for r in rows[1:]:
        vals = map(float, r[1:])
        tot = sum(vals)
        labels.append(r[0])
        props[r[0]] = [float(float(v) / float(tot)) for v in vals]
    return labels, props

def code_exact(x, y):
    return "U" if y > x else ("D" if y < x else "M")

VALLEY = re.compile("DM*U")

def valid_exact(order, props):
    for i in range(len(props[order[0]])):
        s = "".join(code_exact(props[a][i], props[b][i]) for a, b in zip(order, order[1:]))
        if VALLEY.search(s):
            return False
    return True

def valid_adjacent_ci(order, lo, hi):
    # adjacent-change criterion: change counts only if intervals do not overlap
    for i in range(len(lo[order[0]])):
        s = ""
        for a, b in zip(order, order[1:]):
            if lo[b][i] > hi[a][i]: s += "U"
            elif hi[b][i] < lo[a][i]: s += "D"
            else: s += "M"
        if VALLEY.search(s):
            return False
    return True

def valid_pairwise_ci(order, lo, hi):
    # stricter reading: no element significantly below both an earlier and a later one
    n = len(order)
    for i in range(len(lo[order[0]])):
        for m in range(1, n - 1):
            c = order[m]
            left = any(lo[order[j]][i] > hi[c][i] for j in range(m))
            right = any(lo[order[j]][i] > hi[c][i] for j in range(m + 1, n))
            if left and right:
                return False
    return True

def enumerate_valid(labels, ok):
    valid = []
    for k in range(3, len(labels) + 1):
        for sub in itertools.combinations(sorted(labels), k):
            for perm in itertools.permutations(sub):
                if perm[0] > perm[-1]:
                    continue  # one of each reversal pair
                if ok(perm):
                    valid.append(perm)
    return valid

def canon(p):
    p = tuple(p)
    return min(p, p[::-1])

def summarize(valid):
    if not valid:
        return 0, set(), set()
    m = max(len(p) for p in valid)
    maxord = set(canon(p) for p in valid if len(p) == m)
    sets = set(frozenset(p) for p in valid)
    maximal = set(s for s in sets if not any(s < t for t in sets))
    return m, maxord, maximal

def main():
    fn, js, mode = sys.argv[1], sys.argv[2], int(sys.argv[3])
    labels, props = read_table(fn)
    res = json.load(open(js))
    if mode == 0:
        ok = lambda o: valid_exact(o, props)
    else:
        lo = dict((str(k), v) for k, v in res["lowerCI"].items())
        hi = dict((str(k), v) for k, v in res["upperCI"].items())
        ok = lambda o: valid_adjacent_ci(o, lo, hi)
    valid = enumerate_valid(labels, ok)
    m, maxord, maximal = summarize(valid)
    sols = [tuple(map(str, s)) for s in res["solutions"]]
    idss_max = set(canon(map(str, p)) for p in res.get("all_max_orderings", []))
    problems = []
    # every reported solution must be valid under the criterion
    for s in sols:
        if len(set(s)) != len(s):
            problems.append("repeated assemblage in %s" % (s,))
        elif not ok(s):
            problems.append("INVALID reported %s" % (s,))
    if idss_max != maxord:
        problems.append("max orderings differ: brute size %d n=%d, idss n=%d; missing %s extra %s" % (
            m, len(maxord), len(idss_max), sorted(maxord - idss_max)[:3], sorted(idss_max - maxord)[:3]))
    rep_sets = set(frozenset(s) for s in sols)
    if rep_sets != maximal:
        problems.append("maximal sets differ: missing %s extra %s" % (
            [sorted(x) for x in maximal - rep_sets][:3], [sorted(x) for x in rep_sets - maximal][:3]))
    if len(sols) != len(rep_sets):
        problems.append("duplicate node sets in reported solutions")
    out = {"maxsize": m, "n_max_orderings": len(maxord), "n_maximal_sets": len(maximal),
           "n_reported": len(sols), "problems": problems}
    if mode == 1:
        pv = enumerate_valid(labels, lambda o: valid_pairwise_ci(o, lo, hi))
        pm, pmax, pmaximal = summarize(pv)
        out["pairwise_maxsize"] = pm
        out["pairwise_vs_adjacent_valid_diff"] = len(set(map(canon, valid)) ^ set(map(canon, pv)))
        # adjacent-accepted but pairwise-invalid examples
        bad = [p for p in valid if not valid_pairwise_ci(p, lo, hi)]
        out["adjacent_valid_but_pairwise_valley"] = len(bad)
        out["example"] = list(bad[0]) if bad else None
    print(json.dumps(out))

if __name__ == "__main__":
    main()
