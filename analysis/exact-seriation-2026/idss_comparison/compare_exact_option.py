# IDSS --search=exact (Python and compiled engines) versus IDSS iterative search with
# --dipcriterion=triple and versus the standalone exact solver, same data and same intervals.
import json, subprocess, sys, numpy as np
sys.path.insert(0, "/home/claude")
import exact_seriation as E
PY27 = "/home/claude/mamba/py27/bin/python"
def canon(p): return tuple(p) if p[0] < p[-1] else tuple(reversed(p))
def run(fn, boot, search, eng, cim):
    out = fn.replace(".txt", "_%s_%s_b%d_%s.json" % (search, eng, boot, cim))
    r = subprocess.run([PY27, "/home/claude/idsstest/run_idss_repo.py", fn, out, str(boot), "1", "1", cim,
                        "triple", search, eng], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-800:]); raise SystemExit(1)
    d = json.load(open(out))
    return {canon(o) for o in d["all_max_orderings"]}, d
rng = np.random.default_rng(5); N = int(sys.argv[1]); ok = 0; tot = 0
for t in range(N):
    n = int(rng.integers(6, 10)); k = int(rng.integers(3, 7)); times = rng.uniform(0, 1, n); peaks = np.linspace(0, 1, k)
    w = np.exp(-0.5 * ((times[:, None] - peaks) / 0.25) ** 2) + rng.uniform(0, 0.15, (n, k))
    size = int(rng.choice([150, 400, 1000]))
    counts = np.array([rng.multinomial(size, r / r.sum()) for r in w]).astype(float); names = ["S%02d" % i for i in range(n)]
    fn = "/home/claude/idsstest/rand/ex%02d.txt" % t
    with open(fn, "w") as fh:
        fh.write("Assemblage\t" + "\t".join("T%d" % j for j in range(k)) + "\n")
        for nm, row in zip(names, counts): fh.write(nm + "\t" + "\t".join(str(int(v)) for v in row) + "\n")
    for boot in (0, 1):
        a, d = run(fn, boot, "exact", "python", "percentile")
        b, _ = run(fn, boot, "exact", "c", "percentile")
        c, _ = run(fn, boot, "idss", "auto", "percentile")
        if boot:
            lo = np.array([d["lowerCI"][x] for x in names]); hi = np.array([d["upperCI"][x] for x in names]); bad = E.dip_tensor_ci(lo, hi)
        else:
            bad = E.dip_tensor_tol(counts / counts.sum(1, keepdims=True), 0.0)
        s = E.Search(bad).run(E.search_order(bad)); e = {canon(tuple(names[i] for i in o)) for o in s.solutions}
        same = (a == b == c == e); ok += same; tot += 1
        if not same: print("MISMATCH t%d boot%d: python %d, compiled %d, iterative %d, standalone %d" % (t, boot, len(a), len(b), len(c), len(e)))
print("%d of %d runs: exact option (Python), exact option (compiled), iterative triple search and standalone solver identical" % (ok, tot))
