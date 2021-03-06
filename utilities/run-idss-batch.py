#!/usr/bin/env python

import argparse
import logging as log
import os
import fnmatch


def parse_filename_into_root(filename):
    base = os.path.basename(filename)
    root, ext = os.path.splitext(base)
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--inputdirectory", help="path to directory with IDSS input files to process", required=True)
    parser.add_argument("--outputdirectory", help="path to directory where IDSS output directories will be created",
                        required=True)
    parser.add_argument("--xyfile", help="path to XY coordinate file for spatial significance", required=True)
    parser.add_argument("--execpath", help="Path to the IDSS executable script (optional)")
    parser.add_argument("--parallelbackground", help="Start the seriations in the background, all at once (don't do this with big batches, use Grid Engine!)", type=int, default=0)
    parser.add_argument("--dobootstrapsignificance", type=int, default=1, help="Perform bootstrap significance tests with a 95% CI")
    parser.add_argument("--database", help="Name of database to store seriation run statistics in")
    parser.add_argument("--continuity",type=int, help="Perform continuity seriation",default=0)
    parser.add_argument("--frequency",type=int, help="Perform frequency seriation",default=1)
    parser.add_argument("--createcommandfile", type=int, default=0, help="produce a file of the commands to be executed instead of directly executing the seriations (useful for grid engine)")
    parser.add_argument("--commandfile", help="Name of command file to be written for this batch of seriations")

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    print "WARNING:  At the moment, this script should only be used to process a directory of input files associated with a single XY file\n"

    f = None
    if args.createcommandfile == 1:
        f = open(args.commandfile, 'wb')
        f.write("#!/bin/sh")
        f.write('\n')

    base_cmd = ''

    if args.database is not None:
        base_cmd += "idss-seriation-mongodb.py --debug 0 --graphs 0 --spatialbootstrapN 100 --spatialsignificance=1 "
        base_cmd += " --database "
        base_cmd += args.database
    else:
        base_cmd += "idss-seriation.py --debug 0 --graphs 0 --spatialbootstrapN 100 --spatialsignificance=1 "


    if args.continuity is not None:
        base_cmd += " --continuity "
        base_cmd += str(args.continuity)

    if args.frequency is not None:
        base_cmd += " --frequency "
        base_cmd += str(args.frequency)

    if args.dobootstrapsignificance == 1:
        base_cmd += " --bootstrapCI=1 --bootstrapSignificance=0.95 "
    elif args.dobootstrapsignificance == 0:
        log.debug("Turning off bootstrap significance testing")
        base_cmd += " --bootstrapCI=0 "
    else:
        log.error("Bad value for turning on/off bootstrap significance testing")
        os._exit(1)

    for file in os.listdir(args.inputdirectory):
        if fnmatch.fnmatch(file, '*.txt'):

            log.info("Processing input file: %s", file)

            root = parse_filename_into_root(file)

            inputfile = args.inputdirectory + "/" + file

            outdir = os.getcwd() + '/' + args.outputdirectory + "/" + root

            try:
                os.mkdir(outdir)
            except:
                pass

        if args.execpath is not None:
            cmd = args.execpath + "/"
        else:
            cmd = ''

            cmd += base_cmd + " --inputfile " + inputfile
            cmd += " --outputdirectory " + outdir
            cmd += " --xyfile " + args.xyfile

            if args.parallelbackground == 1:
                cmd += " & ) &"

            log.debug("cmd: %s", cmd)

            if args.createcommandfile == 0:
                os.system(cmd)
            else:
                f.write(cmd)
                f.write('\n')

    f.close()


