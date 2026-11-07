# Python 2.7 driver for the published IDSS code (github.com/clipo/idss-seriation).
# Runs IDSS.seriate() unchanged up to the point where the filtered solution set is
# complete, then writes the solutions (as ordered paths) and the bootstrap
# confidence bounds IDSS used to a JSON file, and stops before plotting.
#
# usage: python run_idss_fixed.py <input.txt> <out.json> <bootstrapCI 0/1> [largestonly 0/1] [seed] [percentile|legacy] [neighbor|triple]
import sys, json, os
sys.path.insert(0, "/home/claude/idss-seriation")
import numpy as np
import networkx as nx
from seriation.IDSS import IDSS


class Captured(Exception):
    pass


class DriverIDSS(IDSS):
    def checkMinimumRequirements(self):
        pass  # graphviz is needed only for drawing

    def filterSolutions_optimized(self, end_solutions, all_solutions):
        # record every ordering of the largest size before IDSS's filter keeps one per subset
        m = max(len(g) for g in all_solutions) if all_solutions else 0
        allmax = set()
        for g in all_solutions:
            if len(g) == m:
                p = tuple(nx.shortest_path(g, g.graph["End1"], g.graph["End2"]))
                allmax.add(min(p, p[::-1]))
        self.all_max_orderings = [list(p) for p in sorted(allmax)]
        return IDSS.filterSolutions_optimized(self, end_solutions, all_solutions)

    def output(self, filteredArray, *a, **k):
        sols, skipped = [], 0
        for g in filteredArray:
            if not hasattr(g, "graph"):
                skipped += 1
                continue
            path = nx.shortest_path(g, g.graph["End1"], g.graph["End2"])
            sols.append(path)
        if getattr(self, "exactResult", None) is not None:
            self.all_max_orderings = self.exactResult["orderings"]
        self.captured = {"solutions": sols, "skipped_non_graph": skipped,
                         "lowerCI": self.typeFrequencyLowerCI,
                         "upperCI": self.typeFrequencyUpperCI,
                         "labels": list(self.labels),
                         "all_max_orderings": getattr(self, "all_max_orderings", [])}
        raise Captured()


def main():
    infile, outfile, boot = sys.argv[1], sys.argv[2], int(sys.argv[3])
    largest = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    CIM = sys.argv[6] if len(sys.argv) > 6 else "percentile"
    DIP = sys.argv[7] if len(sys.argv) > 7 else "neighbor"
    SEARCH = sys.argv[8] if len(sys.argv) > 8 else "idss"
    ENG = sys.argv[9] if len(sys.argv) > 9 else "auto"
    outdir = os.path.splitext(outfile)[0] + "_idssout"
    args = {"inputfile": infile, "frequency": 1, "bootstrapCI": boot,
            "largestonly": largest if largest else None, "filtered": 1,
            "noscreen": 1, "screen": None, "debug": 0, "delimiter": "\t",
            "outputdirectory": outdir, "occurrence": None, "continuity": None,
            "xyfile": None, "pairwisefile": None, "mst": None, "threshold": os.environ.get("THRESH"),
            "excel": 0, "atlas": 0, "preservepickle": 0, "noheader": None,
            "graphs": None, "shapefile": None, "frequencyseriation": None,
            "spatialsignificance": None, "verbose": None,
            "source_identifier": "none", "cimethod": CIM, "seed": SEED, "bootsize": os.environ.get("BOOTSIZE"), "dipcriterion": DIP, "search": SEARCH, "exactengine": ENG, "maxorderings": 1000000}
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
