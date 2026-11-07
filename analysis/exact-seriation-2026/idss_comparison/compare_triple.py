# Fixed IDSS with --dipcriterion=triple and bootstrap intervals, versus the exact solver given the
# same interval bounds (dip if upper(j) < min(lower(i), lower(k))): largest size and full set of
# largest orderings must be identical. Also runs the strict (no bootstrap) case.
import json, subprocess, sys, numpy as np
sys.path.insert(0, "/home/claude")
import exact_seriation as E
PY27 = "/home/claude/mamba/py27/bin/python"
rng = np.random.default_rng(7)
def canon(p): return tuple(p) if p[0] < p[-1] else tuple(reversed(p))
def compare(fn, names, counts, boot, dip, cim="percentile"):
    out = fn.replace(".txt", "_%s_b%d_%s.json" % (dip, boot, cim))
    subprocess.run([PY27, "/home/claude/idsstest/run_idss_repo.py", fn, out, str(boot), "1", "1", cim, dip],
                   capture_output=True, check=True)
    d = json.load(open(out))
    idss = {canon(o) for o in d["all_max_orderings"]}
    if boot:
        lo = np.array([d["lowerCI"][n] for n in names]); hi = np.array([d["upperCI"][n] for n in names])
        bad = E.dip_tensor_ci(lo, hi)
    else:
        bad = E.dip_tensor_tol(counts / counts.sum(1, keepdims=True), 0.0)
    s = E.run_c_engine(bad, E.search_order(bad), 10**6, 0, E.find_binary(), verbose=0)
    exact = {canon(tuple(names[i] for i in o)) for o in s.solutions}
    return idss == exact, s.best, len(exact), len(idss), d
if __name__ == "__main__":
    trials = int(sys.argv[1]); ok = {0: 0, 1: 0}
    for t in range(trials):
        n = int(rng.integers(6, 10)); k = int(rng.integers(3, 7))
        times = rng.uniform(0, 1, n); peaks = np.linspace(0, 1, k)
        w = np.exp(-0.5 * ((times[:, None] - peaks) / 0.25) ** 2) + rng.uniform(0, 0.15, (n, k))
        size = int(rng.choice([150, 300, 600, 1200]))
        counts = np.array([rng.multinomial(size, r / r.sum()) for r in w]).astype(float)
        names = ["S%02d" % i for i in range(n)]
        fn = "/home/claude/idsstest/rand/tri%02d.txt" % t
        with open(fn, "w") as fh:
            fh.write("Assemblage\t" + "\t".join("T%d" % j for j in range(k)) + "\n")
            for nm, row in zip(names, counts):
                fh.write(nm + "\t" + "\t".join(str(int(v)) for v in row) + "\n")
        for boot in (0, 1):
            same, best, ne, ni, _ = compare(fn, names, counts, boot, "triple")
            ok[boot] += same
            if not same:
                print("MISMATCH t%d boot%d n=%d: exact size %d (%d orderings), IDSS %d orderings" % (t, boot, n, best, ne, ni))
    print("triple criterion, no bootstrap: %d of %d identical" % (ok[0], trials))
    print("triple criterion, bootstrap:    %d of %d identical" % (ok[1], trials))
