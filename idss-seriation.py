#!/usr/bin/env python
# Copyright (c) 2013-2015.  Carl P. Lipo and Mark E. Madsen.
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Wrapper script for running an IDSS seriation from the command line on a Mac OS X or Linux system.

"""

from seriation import IDSS

seriation = IDSS()
args = seriation.parse_arguments()
frequencyResults, continuityResults, exceptionList = seriation.seriate(args)


