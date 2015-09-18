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
    continuity_seriation = BooleanField()
    frequency_seriation = BooleanField()



class SeriationRun(Document):

    total_runtime = FloatField()
    frequency_processing_time = FloatField()
    continuity_processing_time = FloatField()
    spatial_processing_time = FloatField()
    minmax_weight_processing_time = FloatField()
    occurrence_processing_time = FloatField()
    total_number_solutions = IntField()
    max_solution_size = IntField()
    parameters = EmbeddedDocumentField(SeriationParameters)
    version_used = StringField(required=True)
    seriation_run_id = StringField(required=True)
    num_assemblages = IntField()
    num_classes = IntField()
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
        params.spatial_significance = bool(self.args.spatialsignificance)
        params.xyfile_path = xyfile
        params.outputdirectory = self.args.outputdirectory
        params.continuity_seriation = bool(stats_map["continuity"])
        params.frequency_seriation = bool(stats_map["frequency"])


        srun = SeriationRun()
        srun.parameters = params
        srun.max_solution_size = stats_map['max_seriation_size']
        srun.total_number_solutions = stats_map['total_number_solutions']
        if 'processing_time' in stats_map:
            srun.frequency_processing_time = stats_map['processing_time']
        if 'continuity_processing_time' in stats_map:
            srun.continuity_processing_time = stats_map["continuity_processing_time"]
        if 'spatial_processing_time' in stats_map:
            srun.spatial_processing_time = stats_map["spatial_processing_time"]
        if 'minmax_weight_processing_time' in stats_map:
            srun.minmax_weight_processing_time = stats_map["minmax_weight_processing_time"]
        if 'occurrence_processing_time' in stats_map:
            srun.occurrence_processing_time = stats_map["occurrence_processing_time"]
        srun.total_runtime = stats_map['execution_time']
        srun.version_used = idss_version.__version__
        srun.seriation_run_id = stats_map['seriation_run_id']
        srun.num_assemblages = stats_map["num_assemblages"]
        srun.num_classes = stats_map["num_classes"]

        srun.save()

