import sys, os
sys.path.insert(0, "/home/claude/clipo/idss-v2.0")
import itertools, networkx as nx
from seriation.IDSS import IDSS
infile, boot = sys.argv[1], int(sys.argv[2])
argv = ["idss", "--inputfile=" + infile, "--frequency=1"]
if boot: argv.append("--bootstrapCI=1")
sys.argv = argv
s = IDSS(); s.parse_arguments()
s.openFile(infile)
if boot:
    s.bootstrapCICalculation(100, 0.95)
s.thresholdDetermination(1.0)
tr = s.findAllValidTriples()
acc = set(tuple(nx.shortest_path(t, t.graph["End1"], t.graph["End2"])) for t in tr)
labels = sorted(s.assemblages)
def strict_ok(p):
    for t in range(len(s.assemblages[p[0]])):
        a, b, c = [s.assemblages[x][t] for x in p]
        if b < min(a, c): return False
    return True
valid = set(p for p in itertools.permutations(labels, 3) if strict_ok(p))
print("triples accepted by IDSS:", len(acc), " strictly valid triples:", len(valid))
print("valid but rejected:", len(valid - acc), sorted(valid - acc)[:12])
print("accepted but invalid:", len(acc - valid), sorted(acc - valid)[:12])
