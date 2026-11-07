# IDSS Seriation #


## Overview ##

Iterative Deterministic Seriation Solutions (IDSS) performs frequency seriation upon "assemblages" (collections of 
trait frequencies), following the strict requirements of the Fordian seriation method in archaeology.  Instead of 
simply ordering a similarity matrix, IDSS uses all of the frequency information given, constructing maximal subsets
of assemblages that still meet the unimodality requirement.  Depending upon the data set, this could yield a single
seriation solution composed of all the input assemblages, or it may result in a larger number of solutions, each of 
which is composed of one or more assemblages.  An assemblage can occur in more than one solution, and is a 
frequent occurrence when a given assemblage is early in a temporal sequence and gives rise to more than one later 
lineage.  

IDSS gets around the combinatorial explosion inherent in seriation methods by not evaluating the entire search space
of solutions, but instead building solutions iteratively by adding valid pieces together.  Every solution with 6
assemblages, for example, can be formed by concatenating two valid 3-assemblage solutions.  

IDSS uses bootstrap evaluation of sample size to determine whether frequency differences are significantly different 
when assessing conformance with unimodality, which assists in removing the noise component which makes visual
and manual seriation methods difficult (and which is usually swept under the rug as "stress" in multivariate 
seriation methods).  

IDSS produces several kinds of output.  First, we construct an approximation of the traditional row-based seriation
orders, and can output data sufficient to produce graphics like those in Lipo (2001) and other publications.  Second,
we output an innovative graph-based representation of all the seriation solutions.  Because some assemblages might 
occur in more than one seriation solution, the set of all solutions is actually a branching graph or network, where
each branch represents a solution (set of assemblages that seriate together, meeting the unimodality criterion).  

## Corrections, November 2026 ##

Releases v2.0 through v2.5.1 contain defects in the code that compares type frequencies, enumerates
candidate triples and extends solutions. Depending on the version and on whether bootstrap intervals
are used, those releases can miss valid solutions, return solutions smaller than the largest that
exist, accept invalid solutions, or fail on data that seriate perfectly. Results produced with those
releases should be re-run with the corrected code.

The corrections, and how each was verified, are listed in [FIXES.md](FIXES.md). In summary:

1. Each set of three assemblages is now tested with each assemblage in the middle. The earlier code
   tested only one of the three placements.
2. The triple test now evaluates each type separately with one consistent coding of increases and
   decreases.
3. In the bootstrap branch of the extension step, increases and decreases were coded in reverse, so
   peaks were rejected and valleys accepted. This is corrected.
4. An assemblage can no longer be added to a solution that already contains it.
5. The pair threshold (`--threshold`) now compares all types and is applied to triples as well as
   to extensions.
6. The bootstrap interval is now the percentile interval of the bootstrap replicates. The earlier
   interval (mean plus or minus t times the standard error of the replicates) narrowed as the number
   of replicates increased. `--cimethod=legacy` restores the earlier interval exactly.

With `--bootstrapCI=0`, the corrected code returns the same largest solutions as an independent
exhaustive search on a synthetic table, the PFG test data (`testdata/pfg/pfg-cpl.txt`) and 40 random
tables, and an independent brute-force check over every ordering of every subset agreed on 120 runs
of small tables with and without bootstrap intervals.

### Two criteria for a violation of unimodality ###

With bootstrap intervals, IDSS can detect violations in two ways, selected with `--dipcriterion`:

- `triple` (default): any assemblage whose upper bound is below the lower bounds of both an earlier and a
  later assemblage in the solution is a violation. This matches the definition of unimodality, and any valid
  solution remains valid when assemblages are removed from it.
- `neighbor` (the test used in releases up to v2.5.1): increases and decreases are judged between neighbouring
  assemblages, and a significant decrease followed (possibly after non-significant steps) by a significant
  increase is a violation. A chain of overlapping intervals can therefore contain an assemblage that is
  significantly lower than both an earlier and a later assemblage, and such a solution is accepted. On the PFG
  test data, the largest solution accepted under this rule contains such dips.

Without bootstrap intervals (`--bootstrapCI=0`) the two criteria are equivalent. Use `neighbor` to reproduce
earlier analyses or to show how much the results depend on the choice.

One property of the iterative search is unchanged: when a set of assemblages has several valid orderings, only
the first one found is reported.

### Exact search option ###

`--search=exact` replaces the iterative search with an exact branch-and-bound search. It returns every subset of
assemblages of the largest size that has a valid ordering, and every valid ordering of each such subset (mirror
images counted once), with proof that none is missed. It uses the every-triple criterion (`--dipcriterion=triple`),
because the search relies on a valid solution staying valid when assemblages are removed from it.

- Assemblages are added one at a time and inserted at every position where they create no violation.
- An assemblage that cannot be inserted anywhere in a partial solution is dropped from that branch, since it
  cannot join any larger solution built from it.
- A branch is abandoned when it cannot reach the largest size already found.

The search writes `<input>-exact-subsets.txt`, which lists every largest subset with its number of valid
orderings, followed by the orderings, and passes the orderings to the usual output routines as solutions
(up to `--maxorderings`, default 10000; the counts and subset list are always complete). It reports only
solutions of the largest size, not smaller solutions that cannot be extended. It cannot be combined with a
`--threshold` below 1.0.

A compiled engine runs the search 100 to 300 times faster than the Python version. Build it once with

```shell
gcc -O3 -o seriation/seriate_core seriation/seriate_core.c
```

It is used automatically when present (`--exactengine=auto`); `--exactengine=python` forces the Python version.
The `--frequencyseriation` figure computes its own bootstrap for every row of every solution, so with many
orderings it can take much longer than the search itself; lower `--maxorderings` when producing that figure.
On the PFG test data with bootstrap intervals, the exact search takes under a second. In testing on tables of
54 and 55 assemblages it completed in seconds to minutes, depending on how many valid orderings the data allow.

## Installation and Prerequisites ##

IDSS requires a standard Python 2.7 installation.  We recommend Anaconda Scientific Python, from http://continuum.io/.  
It is a Python distribution that comes bundled with pre-packaged versions of important packages such as NumPy, SciPy, 
and other dependencies.  Some of these dependencies can be difficult or time-consuming to build from scratch if you are
using another Python distribution.  Additionally, Anaconda is self-contained and does not alter your system Python 
installation, which is a very safe way to proceed, especially on Mac OS X.  

The following assumes that you are using Anaconda.  For some notes on dependencies and packages needed to install under a 
system or standard Python distribution, see below.  

You should be able to execute Python from the command line before proceeding, in a Terminal window, and see something
like the following:

```shell
mark:~/ $ python                                                                                                                                                                                                 [14:51:22]
Python 2.7.8 |Anaconda 2.1.0 (x86_64)| (default, Aug 21 2014, 15:21:46)
[GCC 4.2.1 (Apple Inc. build 5577)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
Anaconda is brought to you by Continuum Analytics.
Please check out: http://continuum.io/thanks and https://binstar.org
>>>
```

1. Clone the Github repository, or download a release package and unzip or untar it into a working directory.
Releases v2.0 through v2.5.1 contain the defects described under "Corrections, November 2026" above; use code that
includes those corrections.  

2.  After cloning or decompressing the IDSS package, change directories into `idss-seriation` and ensure that you have the 
packages listed in `requirements.txt` installed.  The easiest way to do this is to use the `pip` package manager:

```shell
mark:~/ $ pip install -r requirements.txt
```

If you are using Anaconda Scientific Python, some of the dependencies will already have been installed.  This is 
fine.  But there are many small packages that we rely upon, so installation could take several minutes.  Be patient.  

Some packages require a standard C/C++ compiler to install.  On Mac OS X, you will need the XCode development 
environment and its command line tools installed.  On Ubuntu Linux, for example, the package `build-essentials` is sufficient.  
On Windows, you will need a minimal GCC or other command line compiler environment.  http://www.mingw.org/ is a good
place to start.
 
 You will also need to install the GraphViz libraries. GraphViz is available for Mac OS X, Windows, Linux and
  can be installed by going to http://www.graphviz.org/Download.php.

For Ubuntu, you will need to install graphviz before running pip install -r requirements.txt:

   sudo apt-get install graphviz libgraphviz-dev

3.  After dependencies are installed, run the installation script:

```shell
mark:~/ $ python setup.py install
```

This script will:

1.  Copy IDSS library modules to your Python installation's `site-packages` directory
2.  Install the command line script to a suitable directory (e.g., `/usr/local/bin` or the Anaconda distribution's `bin` directory.

At this point, if the installation directory is in your path, you should be able to run the main seriation script and 
get a help message that looks something like this:

```shell
mark:~/ $ idss-seriation.py

Couldn't import dot_parser, loading of dot files will not be possible.
usage: idss-seriation.py [-h] [--debug DEBUG] [--bootstrapCI BOOTSTRAPCI]
                         [--bootstrapSignificance BOOTSTRAPSIGNIFICANCE]
                         [--filtered FILTERED] [--largestonly LARGESTONLY]
                         [--individualfileoutput INDIVIDUALFILEOUTPUT]
                         [--threshold THRESHOLD] [--noscreen NOSCREEN]
                         [--xyfile XYFILE] [--pairwisefile PAIRWISEFILE]
                         [--mst MST] [--stats STATS] [--screen SCREEN]
                         [--allsolutions ALLSOLUTIONS] --inputfile INPUTFILE
                         [--outputdirectory OUTPUTDIRECTORY]
                         [--shapefile SHAPEFILE] [--graphs GRAPHS]
                         [--frequency FREQUENCY] [--continuity CONTINUITY]
                         [--graphroot GRAPHROOT]
                         [--continuityroot CONTINUITYROOT] [--atlas ATLAS]
                         [--excel EXCEL] [--noheader NOHEADER]
                         [--frequencyseriation FREQUENCYSERIATION]
                         [--verbose VERBOSE] [--occurrence OCCURRENCE]
                         [--occurrenceseriation OCCURRENCESERIATION]
                         [--spatialsignificance SPATIALSIGNIFICANCE]
                         [--spatialbootstrapN SPATIALBOOTSTRAPN]
                         [--minmaxbycount MINMAXBYCOUNT]
idss-seriation.py: error: argument --inputfile is required

```

If the first line of output comments on that the system "Couldn't import dot_parser..." do not worry. This is just 
is a warning from the python `NetworkX` package, and does not affect any part of the operation
of the IDSS seriation library.  At this time we cannot suppress the warning.  

The rest of the help message lists the command line options for the `idss-seriation.py` program.  


### Tested Environment (2026) ###

Anaconda's own Python 2.7 packages are no longer distributed, but Python 2.7 environments can still be built from
conda-forge. The corrected code was tested with the following, using `micromamba` (the same commands work with `conda`
or `mamba`):

```shell
micromamba create -p ./py27 -c conda-forge python=2.7 numpy scipy matplotlib pip pygraphviz graphviz
./py27/bin/pip install "networkx==1.9.1" "path.py==7.7.1" "svglib==0.9.3" "reportlab<3.6" \
    pysvg svgwrite xlsxwriter "mongoengine<0.20"
./py27/bin/python idss-seriation.py --inputfile=testdata/pfg/pfg-cpl.txt --frequency=1 --bootstrapCI=1 --seed=1
```

This gave Python 2.7.15, NumPy 1.16.5, SciPy 1.2.1, networkx 1.9.1 and pygraphviz 1.5. Later versions of networkx
(2.x and above) are not compatible with this code.

### Installation Without Anaconda Python ###

If you are using a pre-installed or "system" version of Python, it may be installed in directories on your system which require
root/superuser/Administrator access.  You may need to prepend `sudo` to installation commands, which will prompt you for your
password before continuing:

```shell
mark:~/ $ sudo pip install -r requirements.txt
```

Furthermore, on a standard Ubuntu Linux system, you may need to install some additional package dependencies before 
NumPy, SciPy, and Matplotlib can be compiled and installed.  The following work on Ubuntu from 12.04 through 14.04:

```shell
mark:~/ $ sudo apt-get build-dep python-matplotlib python-numpy python-scipy
mark:~/ $ sudo pip install -r requirements.txt
```
 
### Installation on Windows ###
 
We do not regularly work with Windows systems and cannot answer questions about getting specific Python packages compiled
and installed in a Windows environment.  You are **especially** recommended to use Anaconda Scientific Python on 
Windows, since it ships with an already compiled version of NumPy and SciPy libraries, which require significant effort 
to compile and install on Windows.

One feature that may not work well (or at all) on a Windows machine is the --screen flag.
This flag has the code use the curses library to draw a simple updating screen that shows the progress of the processing.


## Data Input Format ##

We use a basic ascii text format for the input file.  In this format, columns are tab-delimited.  Please note that on Mac OS X
you may need to save .txt files using "Windows tab delimited" rather than the default "tab limited" especially if you are exporting 
from Microsoft Excel. The default Mac OS X version of "tab delimited" often does not have the correct end of line character that is assumed
in python resulting in a botched import. 

The first row of the file is always assumed to be the header. The header should include a label for each of the columns. The first column 
is the name of the rows (i.e., assemblages or collections, etc.) The rest of the columns should be the names of the types/classes. The rows
after the first should contain the data with the first column containing the name and the rest of the columns the counts of the types/classes.
Note that we assume that you will provide the raw count data (not percentages). 

If you have the locations of the assemblages and want to look at how the results appear on geographic space, provide a 
separate file that lists the assemblage/collection name and the X and Y coordinates for each. This files should have a header 
(e.g., Assemblage<tab>Northing<tab>Easting) and be tab delimited. Use the --xyfile flag to set the name/location for this file. 

## Command Line Options ##

If you run IDSS without any options you will get a help message with the various options that are possible. 
To run IDSS you must set at least one  options on the command line.  The most imporant (and required) option is 
--inputfile=<filename>). This option specifies the data file that contains the raw data that describes the 
assemblages that are to be seriated.   Other useful options include:

- `--outputdirectory=<directory>` Directory for output files. The default is `./output`.
- `--frequency=1` Conduct a frequency seriation (the default).
- `--bootstrapCI=1` Use bootstrap confidence intervals when comparing type frequencies (the default). With
  `--bootstrapCI=0`, frequencies are compared directly and any decrease followed by an increase is a violation.
- `--bootstrapSignificance=0.95` Confidence level of the bootstrap intervals. Default is 0.95.
- `--cimethod=percentile|legacy` Bootstrap interval. `percentile` (default) uses the percentile interval of the
  bootstrap replicates; `legacy` reproduces the interval used in releases v2.0 to v2.5.1.
- `--dipcriterion=neighbor|triple` How a violation of unimodality is detected with bootstrap intervals (see
  "Two criteria for a violation of unimodality" above). Default is `triple`.
- `--search=idss|exact` Iterative search (default) or exact branch-and-bound search (see "Exact search option").
- `--maxorderings=<n>` With `--search=exact`, the number of orderings kept as solutions for output. Default 10000.
- `--exactengine=auto|c|python` With `--search=exact`, which implementation to use. Default `auto`.
- `--bootsize=<n>` Number of bootstrap replicates. Default is 10000.
- `--seed=<n>` Random seed for the bootstrap, so that runs can be repeated exactly.
- `--threshold=<x>` Only pairs of assemblages whose largest difference in type proportions is at most `x` may be
  adjacent in a solution. Default is 1.0 (no restriction).
- `--xyfile=<filename>` Spatial coordinates for the assemblages, used to show results in geographic space
  (format: assemblage<tab>X<tab>Y).

(TBD)


## Output Files and Formats ##

(TBD)



## Documentation ##

(TBD)


## License ##

This software is provided as open-source software under the Apache Public License 2.0.  The license is included as the 
file LICENSE in the repository.  The license allows you broad freedom to work with this software as needed for 
research or commercial purposes, so long as you respect the rights of others to do the same.  


## Contact ##

The authors are Carl P. Lipo and Mark E. Madsen.  

We are not able to provide ongoing technical support for the use of this software, although we will answer questions
as time permits.  Bugs must be reported by [filing an issue on the Github repository](https://github.com/clipo/idss-seriation/issues).  
We will fix bugs as time permits.  

Bug reports must be accompanied by a "minimal reproducible example", composed of:

1.  The smallest sample of data which reproduces the problem.  Please do not give us an input file with 50 assemblages when the issue involves 4 of them.  
2.  The exact command line (with all flags and options) used to reproduce the problem.  
3.  A textual description of the issue
4.  The error messages produced, preferably by cut and paste.  


## References and Additional Information ##

(TBD)
