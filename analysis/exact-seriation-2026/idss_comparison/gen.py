# Generate small random tables: half seriation-like (unimodal curves + multinomial noise), half random.
import sys, random
import numpy as np
seed = int(sys.argv[1]); out = sys.argv[2]
rng = np.random.RandomState(seed)
n = rng.randint(6, 9)
t = rng.randint(3, 6)
kind = seed % 3
rows = []
if kind == 0:
    pos = rng.permutation(n)
    peaks = rng.uniform(0, n, t)
    widths = rng.uniform(1.5, 4, t)
    for k in range(n):
        w = np.exp(-((pos[k] - peaks) ** 2) / (2 * widths ** 2)) + 0.02
        p = w / w.sum()
        size = rng.randint(30, 400)
        rows.append(rng.multinomial(size, p))
elif kind == 1:
    for k in range(n):
        rows.append(rng.randint(0, 6, t))   # small counts -> many ties and zeros
else:
    for k in range(n):
        rows.append(rng.randint(0, 100, t))
with open(out, "w") as f:
    f.write("Name\t" + "\t".join("T%d" % i for i in range(t)) + "\n")
    for k, r in enumerate(rows):
        r = list(r)
        if sum(r) == 0: r[0] = 1
        f.write("A%d\t" % k + "\t".join(str(int(x)) for x in r) + "\n")
