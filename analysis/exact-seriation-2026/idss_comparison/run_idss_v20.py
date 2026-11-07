# Python 2.7 driver for IDSS v2.0 (tag v2.0, "the one used to produce the paper results").
# usage: python run_idss_v20.py <input.txt> <out.json> <bootstrapCI 0/1> [seed]
import sys, json, os
sys.path.insert(0, "/home/claude/clipo/idss-v2.0")
import random, numpy as np
import networkx as nx
from seriation.IDSS import IDSS

class Captured(Exception):
    pass

class DriverIDSS(IDSS):
    def checkMinimumRequirements(self):
        pass
    def output(self, filteredArray, *a, **k):
        sols, skipped = [], 0
        for g in filteredArray:
            if not hasattr(g, "graph"):
                skipped += 1; continue
            sols.append(nx.shortest_path(g, g.graph["End1"], g.graph["End2"]))
        self.captured = {"solutions": sols, "skipped_non_graph": skipped,
                         "lowerCI": self.typeFrequencyLowerCI, "upperCI": self.typeFrequencyUpperCI}
        raise Captured()

infile, outfile, boot = sys.argv[1], sys.argv[2], int(sys.argv[3])
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
random.seed(seed); np.random.seed(seed)
outdir = os.path.abspath(os.path.splitext(outfile)[0] + "_idssout") + "/"
if not os.path.exists(outdir): os.makedirs(outdir)
argv = ["idss", "--inputfile=" + infile, "--frequency=1", "--outputdirectory=" + outdir,
        "--largestonly=1"]
if len(sys.argv) > 5 and sys.argv[5] != "none":
    argv.append("--threshold=" + sys.argv[5])
if boot:
    argv.append("--bootstrapCI=1")
sys.argv = argv
s = DriverIDSS()
args = s.parse_arguments()
try:
    s.seriate(args)
    result = {"error": "no output"}
except Captured:
    result = s.captured
json.dump(result, open(outfile, "w"))
print("solutions: %d sizes: %s skipped: %d" % (len(result.get("solutions", [])),
      sorted(set(len(p) for p in result.get("solutions", [])), reverse=True)[:5], result.get("skipped_non_graph", 0)))
