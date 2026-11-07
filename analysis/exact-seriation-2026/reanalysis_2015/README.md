# Re-analysis of the PFG results of Lipo et al. (2015)

Settings as published: bootstrap intervals at 95%, 1,000 replicates, continuity threshold 0.30.

- `corrected_triple_seed1.json` to `seed10.json`: corrected IDSS (default `--dipcriterion=triple`,
  percentile intervals), solutions and the bounds used, from
  `idss-seriation.py --inputfile=testdata/pfg/pfg-cpl.txt --frequency=1 --bootstrapCI=1
  --bootstrapSignificance=0.95 --bootsize=1000 --threshold=0.3 --seed=N`.
- `edges_tr.json`: minmax graph edges from those runs (keys s1 to s10).
- `edges_v20.json`: minmax graph edges from IDSS v2.0 run with the options of the published analysis
  script plus `--threshold=0.3`, random seeds 1 to 5 (keys v1 to v5; driver `../idss_comparison/run_seeded.py`).
- `edges_ex.json`: minmax graph edges from `--search=exact` without a threshold, seeds 1 to 3 (sensitivity check;
  the exact search reports only maximum-size solutions, so it is not comparable with the published analysis).
- `spatial_test.py`: permutation test of the spatial pattern of a minmax graph (mean geographic edge length;
  10,000 random reassignments of site coordinates). Run:
  `python spatial_test.py ../../../testdata/pfg/pfgXY.txt edges_tr.json edges_v20.json`.

Results are summarized in Table 5 of the paper.
