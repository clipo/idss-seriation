#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

from mongoengine import *
from seriation import idss_version



class SeriationParameters(EmbeddedDocument):
    bootstrap_ci_flag = BooleanField()
    bootstrap_significance = FloatField()
    spatial_significance = BooleanField()
    spatial_bootstrap_n = IntField()
    xyfile_path = StringField(required=True)
    inputfile = StringField(required=True)
    outputdirectory = StringField(required=True)



class SeriationRun(Document):

    total_runtime = FloatField()
    total_processing_time = FloatField()
    total_number_solutions = IntField()
    max_solution_size = IntField()
    parameters = EmbeddedDocumentField(SeriationParameters)
    version_used = StringField(required=True)
    meta = {'allow_inheritance': True}


class SeriationDatabase(object):
    """
    persistence connection to the MongoDB database server
    into which SeriationRun metadata, and in the future, primary
    output, are stored.
    """

    def __init__(self, args):
        self.args = args

        connect(db = args.database,
                host = args.dbhost,
                port = args.dbport,
                username = args.dbuser,
                password = args.dbpassword)


    def store_run_metadata(self, stats_map):
        """
        Saves the metadata for a single seriation run. Parameter
        subdocument is constructed from the command line args held
        by the object, and the stats_map argument is a dictionary
        returned by the seriate() method which contains timing
        and solution statistics

        :param stats_map :
        """

        if self.args.xyfile == None:
            xyfile = "none"
        else:
            xyfile = self.args.xyfile

        params = SeriationParameters()
        params.inputfile = self.args.inputfile
        params.bootstrap_ci_flag = bool(self.args.bootstrapCI)
        params.bootstrap_significance = self.args.bootstrapSignificance
        params.spatial_bootstrap_n = self.args.spatialbootstrapN
        params.spatial_significance = self.args.spatialsignificance
        params.xyfile_path = xyfile
        params.outputdirectory = self.args.outputdirectory


        srun = SeriationRun()
        srun.parameters = params
        srun.max_solution_size = stats_map['max_seriation_size']
        srun.total_number_solutions = stats_map['total_number_solutions']
        srun.total_processing_time = stats_map['processing_time']
        srun.total_runtime = stats_map['execution_time']
        srun.version_used = idss_version.__version__

        srun.save()

