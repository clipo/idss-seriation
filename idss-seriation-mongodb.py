#!/usr/bin/env python
# Copyright (c) 2013-2015.  Carl P. Lipo and Mark E. Madsen.
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Wrapper script for running an IDSS seriation from the command line on a Mac OS X or Linux system.

"""

from seriation import IDSS
from seriation.database import SeriationDatabase
import argparse
from seriation import idss_version




def parse_arguments():
    parser = argparse.ArgumentParser(description='Conduct an iterative deterministic seriation analysis')
    parser.add_argument('--debug', '-d', type=int, default=0, help='Sets the DEBUG flag for massive amounts of annotated output.')
    parser.add_argument('--bootstrapCI', '-b', type=int, default=1,
                        help="Sets whether you want to use the bootstrap confidence intervals for the comparisons between assemblage type frequencies. Set's to on or off.")
    parser.add_argument('--bootstrapSignificance', '-bs', default=0.95, type=float,
                        help="The significance to which the confidence intervals are calculated. Default is 0.95.")
    parser.add_argument('--filtered','-f', default=1,
                        help="The script will complete by checking to see if smaller valid solutions are included in the larger sets. If not, they are added to the final set. Default is true. ")
    parser.add_argument('--largestonly','-lo', default=None,
                        help="If set, the results will only include the results from the last and largest successful series of solutions. Smaller solutions will be excluded. Default is false.")
    parser.add_argument('--individualfileoutput', default=None,
                        help="If true, a .VNA files will be created for every solution.")
    parser.add_argument('--threshold', default=None,
                        help="Sets the maximum difference between the frequencies of types that will be examine. This has the effect of keeping one from evaluating trivial solutions or solutions in which there is limited warrant for establishing continuity. Default is false.")
    parser.add_argument('--noscreen', default=1,
                        help="If true, there will be no text output (i.e., runs silently). Default is false.")
    parser.add_argument('--xyfile', default=None,
                        help="Enter the name of the XY file that contains the name of the assemblage and the X and Y coordinates for each.")
    parser.add_argument('--pairwisefile', default=None,
                        help="If you have precalculated the bootstrap comparative p-value, enter the name of the file here and it will be used as the basis of the graphical output for showing significance of comparisons. Default is false.")
    parser.add_argument('--mst', default=None,
                        help="If true, will produce a minimum spanning tree diagram from the set of final solutions.")
    parser.add_argument('--stats', default=None,
                        help="(Not implemented). If true, a histogram of the solutions will be shown in terms of the #s of time pairs are included. Default is false.")
    parser.add_argument('--screen', default=None,
                        help="Sets whether the output will be sent all to the screen or not. Default is false. When true, the screen output is all captured through curses.")
    parser.add_argument('--allsolutions', default=None,
                        help="If set, all of the valid solutions are produced even if they are subsets of larger solutions.")
    parser.add_argument('--inputfile',
                        help="<REQUIRED> Enter the name of the data file with the assemblage data to process.", required=True)
    parser.add_argument('--outputdirectory', default=None,
                        help="If you want the output to go someplace other than the /output directory, specify that here.")
    parser.add_argument('--shapefile', default=None,
                        help="Produces a shapefile as part of the output. You must have specified the --xyfile (coordinates for each point) as well.")
    parser.add_argument('--graphs', default=0,
                        help="If true, the program will display the graphs that are created. If not, the graphs are just saved as .png files.")
    parser.add_argument('--frequency', default=1,
                        help="Conduct a standard frequency seriation analysis. Default is None.")
    parser.add_argument('--continuity', default=None, help="Conduct a continuity seriation analysis. Default is None.")
    parser.add_argument('--graphroot', default=None,
                        help="The root of the graph figures (i.e., name of assemblage you want to treat as one end in the graphs.")
    parser.add_argument('--continuityroot', default=None,
                        help="If you have a outgroup or root of the graph, set that here.")
    parser.add_argument('--atlas', default=1,
                        help="If you want to have a figure that shows all of the results independently, set that here.")
    parser.add_argument('--excel', default=1,
                        help="Will create excel files with the assemblages in seriation order.")
    parser.add_argument('--noheader',default=None,
                        help="If you do not use type names as the first line of the input file, use this option to read the data.")
    parser.add_argument('--frequencyseriation', default=None, help="Generates graphical output for the results in a frequency seriation form.")
    parser.add_argument('--verbose',default=True, help='Provides output for your information')
    parser.add_argument('--occurrence', default=None, help="Treats data as just occurrence information and produces valid occurrence solutions.")
    parser.add_argument('--occurrenceseriation', default=None, help="Generates graphical output for occurrence seriation.")
    parser.add_argument('--spatialsignificance', default=None, help="Calculate the significance of the spatial aspect of the final solution. Default is None.")
    parser.add_argument('--spatialbootstrapN',default=100, help='Set the number of resamples used for calculating the spatial significance. Default is 100.')
    parser.add_argument('--minmaxbycount',default=None, help='Create a minmax solution from the aggregate set by weighting on the basis of # of times edges appear in solutions. Default is None.')
    parser.add_argument('--delimiter', help="character delimiting the fields in inputfile", default='\t')
    parser.add_argument('--preservepickle', help="Do not delete pickle directory, to allow for debugging", type=int, default=0)
    # arguments for database instance
    parser.add_argument("--dbhost", help="MongoDB database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="MongoDB database port, defaults to 27017", type=int, default="27017")
    parser.add_argument("--database", help="Name of Mongodb database to use for saving metadata", required=True)
    parser.add_argument("--dbuser", help="Username on MongoDB database server, optional")
    parser.add_argument("--dbpassword", help="Password on MongoDB database server, optional")

    return parser.parse_args()



if __name__ == "__main__":
    print "IDSS seriation Version %s" % idss_version.__version__

    seriation = IDSS()
    args = parse_arguments()
    db = SeriationDatabase(args)
    seriation.initialize(args)
    (frequencyResults, continuityResults, exceptionList, statsMap) = seriation.seriate()
    db.store_run_metadata(statsMap)

