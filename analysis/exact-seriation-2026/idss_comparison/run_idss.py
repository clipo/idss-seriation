# Python 2.7 driver for the published IDSS code (github.com/clipo/idss-seriation).
# Runs IDSS.seriate() unchanged up to the point where the filtered solution set is
# complete, then writes the solutions (as ordered paths) and the bootstrap
# confidence bounds IDSS used to a JSON file, and stops before plotting.
#
# usage: python run_idss.py <input.txt> <out.json> <bootstrapCI 0/1> [largestonly 0/1] [seed]
import sys, json, os
sys.path.insert(0, "/home/claude/clipo/idss-seriation")
import numpy as np
import networkx as nx
from seriation.IDSS import IDSS


class Captured(Exception):
    pass


class DriverIDSS(IDSS):
    def checkMinimumRequirements(self):
        pass  # graphviz is needed only for drawing

    def output(self, filteredArray, *a, **k):
        sols, skipped = [], 0
        for g in filteredArray:
            if not hasattr(g, "graph"):
                skipped += 1
                continue
            path = nx.shortest_path(g, g.graph["End1"], g.graph["End2"])
            sols.append(path)
        self.captured = {"solutions": sols, "skipped_non_graph": skipped,
                         "lowerCI": self.typeFrequencyLowerCI,
                         "upperCI": self.typeFrequencyUpperCI,
                         "labels": list(self.labels)}
        raise Captured()


def main():
    infile, outfile, boot = sys.argv[1], sys.argv[2], int(sys.argv[3])
    largest = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    if len(sys.argv) > 5:
        np.random.seed(int(sys.argv[5]))
    outdir = os.path.splitext(outfile)[0] + "_idssout"
    args = {"inputfile": infile, "frequency": 1, "bootstrapCI": boot,
            "largestonly": largest if largest else None, "filtered": 1,
            "noscreen": 1, "screen": None, "debug": 0, "delimiter": "\t",
            "outputdirectory": outdir, "occurrence": None, "continuity": None,
            "xyfile": None, "pairwisefile": None, "mst": None, "threshold": None,
            "excel": 0, "atlas": 0, "preservepickle": 0, "noheader": None,
            "graphs": None, "shapefile": None, "frequencyseriation": None,
            "spatialsignificance": None, "verbose": None,
            "source_identifier": "none"}
    s = DriverIDSS()
    s.initialize(args, sys.argv)
    try:
        s.seriate()
        result = {"error": "seriate returned without output"}
    except Captured:
        result = s.captured
    with open(outfile, "w") as fh:
        json.dump(result, fh)
    print("solutions: %d  sizes: %s  skipped: %d" % (
        len(result.get("solutions", [])),
        sorted(set(len(p) for p in result.get("solutions", [])), reverse=True)[:5],
        result.get("skipped_non_graph", 0)))


if __name__ == "__main__":
    main()
