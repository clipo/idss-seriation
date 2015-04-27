#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

from mongoengine import *

class SeriationRun(Document):
    inputfile = StringField(max_length=200, required=True)
    total_runtime = FloatField()
    number_solutions = IntField()


    meta = {'allow_inheritance': True}