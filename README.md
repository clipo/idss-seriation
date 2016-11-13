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

1. Download one of the [release packages](https://github.com/clipo/idss-seriation/releases) for IDSS, and unzip or 
untar the package into a working directory.  Alternatively, you can clone the main Github repository, but be aware that
branch `master` is under active development and we do not warrant its correctness or functionality.  For published 
research, please use the latest release version.  

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

** --output=  <name/location of directory that will be used for output. The default is ./output
** --bootstrapCI=1 Use a bootstrap determined confidence interval for making comparisons. Default significance is 0.95.
** --bootstrapSignificance=0.95 Set the confidence interval significance value. Default is 0.95.
** --yxfile=<filename> If you have spatial coordinates for your assemblages and want the results shown in geographic space
  set this option to the name of the file with the coordinates (format: assemblage<tab>X<tab>Y<return>).

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