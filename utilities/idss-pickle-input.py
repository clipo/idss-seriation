#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Script which does all of the input processing that the main IDSS driver programs do, and then
pickles the assemblage information to a directory.  This is useful for producing the mainstream
seriation output, and then running various other analyses as comparison, where you want to depart
from the exact same input data (frequencies, filtered identical assemblages, bootstrap significance, etc)
that the main seriation output was composed of.

This program is mainly of interest to algorithm developers, not consumers of seriations.

"""
from seriation import IDSS
import sys
import os
import argparse
import cPickle as pickle


def parse_arguments():
    parser = argparse.ArgumentParser(description='Conduct an iterative deterministic seriation analysis')
    parser.add_argument('--debug', '-d', type=int, default=0, help='Sets the DEBUG flag for massive amounts of annotated output.')
    parser.add_argument('--bootstrapCI', '-b', type=int, default=1,
                        help="Sets whether you want to use the bootstrap confidence intervals for the comparisons between assemblage type frequencies. Set's to on or off.")
    parser.add_argument('--bootstrapSignificance', '-bs', default=0.95, type=float,
                        help="The significance to which the confidence intervals are calculated. Default is 0.95.")

    parser.add_argument('--xyfile', default=None,
                        help="Enter the name of the XY file that contains the name of the assemblage and the X and Y coordinates for each.")

    parser.add_argument('--inputfile',
                        help="<REQUIRED> Enter the name of the data file with the assemblage data to process.", required=True)
    parser.add_argument('--outputdirectory', default='./',
                        help="If you want the output to go someplace other than the /output directory, specify that here.")
    parser.add_argument('--delimiter', default='\t', help="delimiter for input file, defaults to tab character")
    parser.add_argument('--noheader', default=0, help="Flag, value 1 if there is no header row with type names, 0 otherwise")


    return parser.parse_args()

if __name__ == "__main__":

    ser = IDSS()
    args = parse_arguments()
    ser.initialize(args,sys.argv)
    filename = args.inputfile
    ser.openFile(filename)

    if args.xyfile is not None:
        ser.openXYFile(args.xyfile)

    base_file = os.path.basename(filename)
    base_file = os.path.splitext(base_file)[0]

    afile = args.outputdirectory + "/" + base_file + "-assemblages.pkl"
    pickle.dump(ser.assemblages,open(afile,'wb'))

    affile = args.outputdirectory + '/' + base_file + "-assemblage_freq.pkl"
    pickle.dump(ser.assemblageFrequencies,open(affile, 'wb'))

    asfile = args.outputdirectory + '/' + base_file + "-assemblage_size.pkl"
    pickle.dump(ser.assemblageSize,open(asfile,'wb'))

    axfile = args.outputdirectory + '/' + base_file + "-assemblage_xloc.pkl"
    pickle.dump(ser.xAssemblage,open(axfile,'wb'))

    ayfile = args.outputdirectory + '/' + base_file + "-assemblage_yloc.pkl"
    pickle.dump(ser.yAssemblage,open(ayfile,'wb'))

    print "pickle data structures for input file %s complete" % filename


