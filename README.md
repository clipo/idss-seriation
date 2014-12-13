# IDSS Seriation #

(Travis build badge goes here)

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

2.  After cloning or decompressing the IDSS package, change directories into `idss-seration` and ensure that you have the 
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
 
We do not regularly work with Windows systems and cannot answer questions about getting specific Python packages compiled
and installed in a Windows environment.  You are **especially** recommended to use Anaconda Scientific Python on 
Windows, since it ships with an already compiled version of NumPy and SciPy libraries, which require significant effort 
to compile and install on Windows.  

3.  After dependencies are installed, run the installation script:

```shell
mark:~/ $ python setup.py install
```

This script will:

1.  Copy IDSS library modules to your Python installation's `site-packages` directory
2.  Install the command line script to a suitable directory (e.g., `/usr/local/bin` or the Anaconda distribution's `bin` directory.

At this point, if the installation directory is in your path, you should be able to run the main seriation script and 
get a help message:

```shell
TBD
```


## Data Input Format ##

(TBD)


## Command Line Options ##

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