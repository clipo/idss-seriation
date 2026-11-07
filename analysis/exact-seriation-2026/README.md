# Exact frequency seriation: analysis materials (2026)

Materials for the paper "Exact frequency seriation of the largest seriable subsets" (C. P. Lipo, in
preparation): the standalone exact solver, the quantum (QAOA) formulation, the data, the results, the
scripts used to compare IDSS releases with the exact search, and the figures.

The corrected IDSS, including the exact search (`--search=exact`) and the choice of violation rule
(`--dipcriterion`), is the main code of this repository; see the top-level README and FIXES.md.

## Contents

| Folder | Contents |
|---|---|
| `standalone/` | `exact_seriation.py` (Python 3, NumPy) and `seriate_core.c`: exact branch-and-bound search for every largest seriable subset and every valid ordering of it. `python exact_seriation.py --verify` checks it against brute force. |
| `quantum/` | `qaoa_seriation.py`: QAOA formulation of frequency seriation for Qiskit 2.x, with optional submission to IBM Quantum hardware. For small tables (4 or 5 assemblages) only. |
| `data/` | The three ceramic type-frequency tables analyzed (counts of decorated sherds): `cpl-pfg.csv` (20 assemblages; the same data as `testdata/pfg/pfg-cpl.txt`), `mainfort-data-collapsed.csv` (54), `pfg-cpl-mainfort.csv` (55). |
| `results/main/` | Standalone exact search on each table, 95% bootstrap criterion (1,000 replicates, seed 1): run log, every largest subset with its number of orderings (`*_subsets.csv`), and the orderings (`*.csv.gz`, up to 100,000 per table). |
| `results/min_sample/` | The same with minimum sample sizes of 100 and 200 sherds, seeds 1 to 5. `summary.txt` collects the counts. |
| `results/seeds/` | Unfiltered tables at further bootstrap seeds (subset lists and `summary.txt`). |
| `results/table2_runs.json` | Per-run largest size and number of orderings behind Table 2 and Fig. 1 of the paper. |
| `idss_comparison/` | Drivers that run IDSS v2.0, v2.5.1 and the corrected code and save solutions with the bounds IDSS used; comparison scripts; the synthetic test table `perfect7.txt`; the brute-force checker written for the independent review (`brute.py`, `gen.py`, `run_thr.py`, `thr.txt`); `outputs/` holds the saved IDSS results used in the paper. |
| `figures/` | `make_figures.py` draws the paper's Figs 1 to 3 from the files in this folder (Python 3, matplotlib). `export_edges.py` (Python 2.7, networkx 1.9.1) extracts minmax graph edges from IDSS output into `minmax_edges.json`. |

## Reproducing the results

1. Standalone exact search (Python 3):

   ```shell
   cd standalone
   gcc -O3 -o seriate_core seriate_core.c          # optional, 100 to 300 times faster
   python exact_seriation.py --verify
   python exact_seriation.py --csv ../data/pfg-cpl-mainfort.csv --ci 0.95 --seed 1
   python exact_seriation.py --csv ../data/pfg-cpl-mainfort.csv --ci 0.95 --seed 1 --min-sample 200
   ```

2. IDSS (Python 2.7 environment described in the top-level README), for example the re-analysis of the
   PFG results of Lipo et al. (2015) with the published settings:

   ```shell
   python idss-seriation.py --inputfile=testdata/pfg/pfg-cpl.txt --frequency=1 --bootstrapCI=1 \
       --bootstrapSignificance=0.95 --bootsize=1000 --threshold=0.3 --seed=1 --dipcriterion=triple
   ```

   `--dipcriterion=neighbor` gives the rule used in earlier releases, and adding `--cimethod=legacy` gives
   the interval used in earlier releases.

3. Figures: `cd figures && python make_figures.py`.

The scripts in `idss_comparison/` were run in the analysis environment and refer to its locations
(`/home/claude/...` for the IDSS checkouts and the Python 2.7 interpreter, `/tmp/...` for scratch output).
Edit those paths before running them elsewhere. The IDSS versions compared are tag v2.0, tag v2.5.1 and
the corrected code in this repository.

## Data sources

`cpl-pfg.csv` is the Lower Mississippi Valley table of Lipo et al. (2015) (Phillips, Ford and Griffin
1951; Lipo 2001). The other two tables include sites in western Tennessee and eastern Arkansas compiled
from Mainfort's data; see the paper for sources.
