#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

from mongoengine import *
from seriation import idss_version
import datetime



class SeriationRunParameters(EmbeddedDocument):
    bootstrap_ci_flag = BooleanField()
    bootstrap_significance = FloatField()
    spatial_significance = BooleanField()
    spatial_bootstrap_n = IntField()
    xyfile_path = StringField(required=True)
    inputfile = StringField(required=True)
    outputdirectory = StringField(required=True)
    continuity_seriation = BooleanField()
    frequency_seriation = BooleanField()
    full_cmdline = StringField()


class SeriationProfilingData(EmbeddedDocument):
    bootstrap_ci_processing_time = FloatField()
    total_frequency_processing_time = FloatField()
    freq_main_processing_time = FloatField()
    freq_spatial_processing_time = FloatField()
    freq_output_processing_time = FloatField()
    freq_minmaxweight_processing_time = FloatField()
    freq_sumgraphweight_processing_time = FloatField()
    freq_filter_processing_time = FloatField()
    freq_excelmacro_processing_time = FloatField()
    freq_excel_processing_time = FloatField()
    freq_atlas_processing_time = FloatField()
    freq_mst_processing_time = FloatField()
    total_continuity_processing_time = FloatField()
    total_occurrence_processing_time = FloatField()


class FrequencySeriationResult(EmbeddedDocument):
    max_solution_size = IntField()
    total_number_solutions = IntField()
    spatial_significance_pvalue = FloatField()


class OccurrenceSeriationResult(EmbeddedDocument):
    pass

class ContinuitySeriationResult(EmbeddedDocument):
    spatial_significance_pvalue = FloatField()


class SeriationRun(Document):
    total_runtime = FloatField()
    parameters = EmbeddedDocumentField(SeriationRunParameters)
    profiling = EmbeddedDocumentField(SeriationProfilingData)
    frequency_results = EmbeddedDocumentField(FrequencySeriationResult)
    continuity_results = EmbeddedDocumentField(ContinuitySeriationResult)
    occurrence_results = EmbeddedDocumentField(OccurrenceSeriationResult)
    version_used = StringField(required=True)
    seriation_run_id = StringField(required=True)
    num_assemblages = IntField()
    num_classes = IntField()
    date_seriation_run = DateTimeField(default=datetime.datetime.now)
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

        params = SeriationRunParameters()
        params.inputfile = self.args.inputfile
        params.bootstrap_ci_flag = bool(self.args.bootstrapCI)
        params.bootstrap_significance = self.args.bootstrapSignificance
        params.spatial_bootstrap_n = self.args.spatialbootstrapN
        params.spatial_significance = bool(self.args.spatialsignificance)
        params.xyfile_path = xyfile
        params.outputdirectory = self.args.outputdirectory
        params.continuity_seriation = bool(stats_map["continuity"])
        params.frequency_seriation = bool(stats_map["frequency"])
        params.full_cmdline = stats_map["cmdline"]


        profile = SeriationProfilingData()

        profile.bootstrap_ci_processing_time = stats_map["bootstrap_ci_processing_time"]
        profile.total_frequency_processing_time = stats_map['frequency_processing_time']
        profile.freq_main_processing_time = stats_map['freq_main_processing_time']
        profile.freq_filter_processing_time = stats_map['frequency_filter_solutions_time']
        profile.freq_sumgraphweight_processing_time = stats_map["sumgraphweight_processing_time"]
        profile.freq_output_processing_time = stats_map["frequency_output_processing_time"]
        profile.freq_minmaxweight_processing_time = stats_map["minmax_weight_processing_time"]

        if 'spatial_processing_time' in stats_map:
            profile.freq_spatial_processing_time = stats_map["spatial_processing_time"]

        if 'continuity_processing_time' in stats_map:
            profile.total_continuity_processing_time = stats_map["continuity_processing_time"]

        if 'occurrence_processing_time' in stats_map:
            profile.total_occurrence_processing_time = stats_map["occurrence_processing_time"]

        if 'mst_processing_time' in stats_map:
            profile.freq_mst_processing_time = stats_map["mst_processing_time"]
        if 'atlas_processing_time' in stats_map:
            profile.freq_atlas_processing_time = stats_map["atlas_processing_time"]
        if 'excel_processing_time' in stats_map:
            profile.freq_excel_processing_time = stats_map["excel_processing_time"]
        if 'excel_freqseriation_processing_time' in stats_map:
            profile.freq_excelmacro_processing_time = stats_map["excel_freqseriation_processing_time"]


        srun = SeriationRun()
        srun.parameters = params
        srun.profiling = profile

        srun.total_runtime = stats_map['execution_time']
        srun.version_used = idss_version.__version__
        srun.seriation_run_id = stats_map['seriation_run_id']
        srun.num_assemblages = stats_map["num_assemblages"]
        srun.num_classes = stats_map["num_classes"]



        # add the results from various seriation types
        if self.args.frequency == 1:
            freqres = FrequencySeriationResult()
            freqres.max_solution_size = stats_map['max_seriation_size']
            freqres.total_number_solutions = stats_map['total_number_solutions']
            freqres.spatial_significance_pvalue = stats_map['frequency_geographic_pvalue']

            srun.frequency_results = freqres

        if self.args.continuity == 1:
            contres = ContinuitySeriationResult()
            contres.spatial_significance_pvalue = stats_map['continuity_geographic_pvalue']

            srun.continuity_results = contres




        # persist the entire set of results
        srun.save()

