# Compare fixed IDSS (strict mode, no bootstrap) with the exact solver (tol 0) on random tables.
import json, subprocess, sys, numpy as np
sys.path.insert(0, "/home/claude")
import exact_seriation as E
PY27 = "/home/claude/mamba/py27/bin/python"
rng = np.random.default_rng(42)
def canon(p): return tuple(p) if p[0] < p[-1] else tuple(reversed(p))
n_ok = 0; trials = int(sys.argv[1]) if len(sys.argv) > 1 else 40
for t in range(trials):
    n = int(rng.integers(6, 13)); k = int(rng.integers(3, 7))
    times = rng.uniform(0, 1, n); peaks = np.linspace(0, 1, k)
    w = np.exp(-0.5 * ((times[:, None] - peaks) / 0.25) ** 2) + rng.uniform(0, 0.2 if t % 2 else 0.05, (n, k))
    counts = np.array([rng.multinomial(400, r / r.sum()) for r in w])
    names = ["S%02d" % i for i in range(n)]
    fn = "/home/claude/idsstest/rand/t%02d.txt" % t
    with open(fn, "w") as fh:
        fh.write("Assemblage\t" + "\t".join("T%d" % j for j in range(k)) + "\n")
        for nm, row in zip(names, counts):
            fh.write(nm + "\t" + "\t".join(str(int(v)) for v in row) + "\n")
    out = fn.replace(".txt", ".json")
    subprocess.run([PY27, "/home/claude/idsstest/run_idss_fixed.py", fn, out, "0", "1", "1"],
                   capture_output=True, check=True)
    d = json.load(open(out))
    idss = {canon(o) for o in d["all_max_orderings"]}
    f = counts / counts.sum(1, keepdims=True)
    bad = E.dip_tensor_tol(f, 0.0)
    s = E.Search(bad).run(E.search_order(bad))
    exact = {canon(tuple(names[i] for i in o)) for o in s.solutions}
    same = (idss == exact)
    n_ok += same
    if not same:
        print("MISMATCH table %d: n=%d exact size %d (%d orderings), IDSS size %d (%d)" % (
            t, n, s.best, len(exact), len(next(iter(idss))) if idss else 0, len(idss)))
print("%d of %d tables: identical largest size and identical set of largest orderings" % (n_ok, trials))
