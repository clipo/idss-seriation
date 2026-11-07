# Corrections to the frequency seriation code (branch fix-comparisons)

Base: release v2.5.1 (master, commit f7a30d5). The defects listed under 1 to 5 are also
present in tag v2.0 in the same or a closely related form, except where noted.

## Defects corrected

1. **Triple enumeration** (`IDSS.all_tuples`). `itertools.combinations(lst, 3)` returns each set
   of three assemblages in one order, so only one of the three possible middle assemblages was
   tested. Valid triples with either of the other two in the middle were never generated, and
   solutions built from them could not be found. Each set is now tested with each assemblage in
   the middle. (Also in v2.0.)

2. **Triple test** (`IDSS.findAllValidTriples`, new helper `compareFrequencies`).
   - Without bootstrap: the codes for all types were concatenated into one string per step and
     the string was searched for "DU", so the code of one type next to the code of another type
     produced false rejections; `comparison23 = "M"` also overwrote instead of appending.
     (Concatenation defect also in v2.0.)
   - With bootstrap: the code was reassigned for each type, so only the last type was tested;
     `elif high2 > low1` should have been `<`.
   Each type is now tested separately with one coding (U increase, D decrease, M no difference,
   reading from the first to the third assemblage); a triple is invalid when any type decreases
   and then increases.

3. **Extension test, bootstrap branch** (`seriationEvaluation.checkForValidAdditions`). The codes
   were reversed relative to the non-bootstrap branch (outer < inner was coded "D"), so the valley
   pattern `DU|DM*U` rejected peaks and accepted valleys. (Also in v2.0.)

4. **Repeated assemblages** (`checkForValidAdditions`). An assemblage already in a solution was not
   excluded and could be added again, creating a cycle in the solution graph.

5. **Pair threshold** (`thresholdDetermination`, `findAllValidTriples`). The maximum-difference
   loop iterated over `(0, columns - 1)`, which tests only the first and last types; and the
   threshold was applied when solutions were extended but not to the triples they start from.

6. **Bootstrap flag** (`seriate`). Intervals were computed only when `bootstrapCI == True`, while
   comparisons used `not in FalseList`; a value such as 2 skipped the intervals and then failed.

7. **No-solution case** (`_get_longest_subsolution`). An empty list was passed on as a solution
   when no solution existed, which caused a crash in `output`.

## Change of method (switchable)

8. **Bootstrap interval** (`confidence_interval`). The original interval was the mean of the
   bootstrap replicates plus or minus t times their standard error. Its width depends on the number
   of replicates, not on sample size: about 0.20 sampling standard deviations with 100 replicates
   (v2.0) and 0.02 with 10,000 (v2.5.1). The default is now the percentile interval of the
   replicates. `--cimethod=legacy` restores the original interval exactly (verified: identical
   bounds for the same seed).

## Additions

- `--seed` sets the random seed for the bootstrap intervals.
- `--bootsize` sets the number of bootstrap replicates (default 10000).
- Identical orderings produced at the same step are kept once (they arise when the ends of an
  ordering are added in different sequences). This changes run time, not results.

## Known properties not changed

- **One ordering per set of assemblages.** `filterSolutions_optimized` discards a solution whose
  assemblages are the same as, or a subset of, an accepted solution, so when a set has several
  valid orderings only one (the first encountered) is reported.
- **Adjacent-step criterion with bootstrap.** Codes come from neighbouring assemblages only, so a
  chain of overlapping intervals can contain an assemblage that is significantly below both an
  earlier and a later one. Such orderings are accepted, while the corresponding triple on its own
  is rejected. The search remains complete for this criterion, because removing an end assemblage
  cannot create the pattern `DM*U`.
- **`largestonly`.** `maxNodes` is set from the number of solutions returned by a worker
  (`maxNodes = len(s)`) rather than from solution size, and `output` uses it to decide which
  solutions count as largest. The `largestonly` option therefore does not select by size as
  intended. Not changed here; the solution set passed to `output` is unaffected.
- **Zero counts.** A type with a zero count has a zero-width interval at any sample size.

## Verification

- Synthetic 7-assemblage table, unimodal in the order A to G: the full order is recovered with
  and without bootstrap (the original returned 6-assemblage solutions, no solutions, or invalid
  triples, depending on version and mode).
- 40 random tables (6 to 12 assemblages), no bootstrap: the largest size and the complete set of
  largest orderings are identical to an independent exact branch-and-bound search.
- PFG table (testdata/pfg/pfg-cpl.txt), no bootstrap: 33 largest orderings of 4 assemblages,
  identical to the exact search (the original found 1 of the 33).
- PFG table with the legacy interval: 48 largest orderings of 4 assemblages, identical to the exact
  search given the same interval bounds.
- Independent review with a separately written brute-force enumeration over every ordering of
  every subset: 60 random tables of 6 to 8 assemblages, with and without bootstrap (120 runs). All
  reported solutions valid, the complete set of largest orderings found, reported sets equal to the
  inclusion-maximal valid sets, no duplicates.
- Full command-line program on the PFG table, with outputs written: no bootstrap; bootstrap with
  the percentile interval; bootstrap with the legacy interval; and bootstrap with --xyfile, --mst,
  --excel, --atlas and --frequencyseriation. All four completed without error (Python 2.7.15,
  networkx 1.9.1, pygraphviz 1.5).
- Regression after the threshold and bootstrap-flag corrections: the 120-run brute-force suite,
  the 40 random tables, the synthetic table and the PFG table were rerun with the same results.
