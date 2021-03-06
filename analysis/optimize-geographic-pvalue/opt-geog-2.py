#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import pickle
import math
import random as rnd
import matplotlib.pyplot as plt
import time
import scipy as sp
import scipy.stats
from pylab import *
import pprint as pp
import itertools
import numpy as np

import matplotlib
matplotlib.use('Agg')


def setup():
    self_xassem = pickle.load(open("xassem.pickle",'rb'))
    self_yassem = pickle.load(open("yassem.pickle",'rb'))
    mmg = pickle.load(open("mmg.pickle",'rb'))
    labels = pickle.load(open("labels.pickle", 'rb'))
    plot_filename = "test_plot.png"

    return (mmg,self_xassem,self_yassem,plot_filename,labels)

def calculateGeographicSolutionPValue(graph,num_bootstrap,self_xassem,self_yassem,plot_filename,labels):

    # First calculate our reference distance -- the total euclidean distance along the edges of
    # the minmax solution graph.  this is the sum of the distances along each edge where the
    # node XY coordinates from the XY file are used as the position of each assemblage.

    solutionDistance = 0.
    assemblagesInSolution = []
    edges = 0
    for e in graph.edges_iter():
        d = graph.get_edge_data(*e)
        edges += 1
        fromAssemblage = e[0]
        toAssemblage = e[1]
        solutionDistance += math.sqrt(
            pow((self_xassem[fromAssemblage] - self_xassem[toAssemblage]), 2)
            + pow((self_yassem[fromAssemblage] - self_yassem[toAssemblage]), 2))

        assemblagesInSolution.append(fromAssemblage)
        assemblagesInSolution.append(toAssemblage)

    #print "solution Distance: %s" % solutionDistance

    x = []
    pvalueScore = 0.000

    # we pre-calculate unique pairs of assemblages, randomize the list, take the first num_bootstrap entries
    # so we can eliminate doing any unnecessary loops
    random_pairs = list(itertools.combinations(labels, 2))
    #np.random.shuffle(random_pairs)
    #bootstrap_pairs = itertools.cycle(random_pairs)

    # there are a much smaller number of pairs of assemblages than bootstrap iterations, typically,
    # so pre-calculate the distances and then just look them up while going through the bootstrap
    # loop itself.

    # SCALING NOTE:  With 10K bootstrap permutations, the list of combinations is longer than 10K around 150
    # assemblages, and you could gain very slightly by not bothering with the cycle() call and just slicing
    # the first 10K out of the shuffled list.  At 100K iterations, you need 450 assemblages before such a
    # change matters.  So for the moment, this is the most efficient solution that doesn't involve
    # explicit parallelization.
    distances = dict()
    for pair in random_pairs:
        p1 = pair[0]
        p2 = pair[1]
        dist = math.sqrt(pow((self_xassem[p1] - self_xassem[p2]), 2)
                        + pow((self_yassem[p1] - self_yassem[p2]), 2))
        distances[pair] = dist

    # Now, we generate bootstrap samples, by taking len(edges) samples of random
    # assemblage pairs, and adding their distances together, to form a simulated
    # total graph distance.  We then compare this total test graph distance
    # to the actual one from the minmax graph, and if the test graph distance is
    # lower, we score one for this bootstrap iteration.  At the end of num_bootstraps
    # iterations, the pvalue_score / num_bootstraps is the significance value of the
    # actual graph distance.

    for i in xrange(0, num_bootstraps):
        testDistance = 0.0
        for e in xrange(0, edges):
            pair = rnd.choice(random_pairs)

            # print "Pair: ", pair[0], "-", pair[1]
            testDistance += distances[pair]

        #print "Test Distance: ", testDistance
        if testDistance <= solutionDistance:
            #print "TEST is less than solutionDistance: ",testDistance
            pvalueScore += 1.
        x.append(testDistance)

    #print "pvalueScore: %s" % pvalueScore
    pvalue = float(pvalueScore) / float(num_bootstrap)
    #print "pvalue: %0.4f" % pvalue

    ### End of critical phase of algorithm


    filename = plot_filename
    f = plt.figure(filename, figsize=(8, 8))
    plt.rcParams['font.family'] = 'sans-serif'
    # f=plt.figure("Geographic Distance", figsize=(8, 8))
    num_bins = 20
    # the histogram of the data
    n, bins, patches = plt.hist(x, num_bins, facecolor='green', alpha=0.5)

    plt.axvline(solutionDistance, color='r', linestyle='dashed', linewidth=2)
    figure_label = plot_filename[0:-4]
    plt.xlabel(figure_label)
    plt.ylabel('Count')
    plt.title(r'Histogram of Summed Geographic Distance')
    plt.savefig(filename, dpi=75)

    # Tweak spacing to prevent clipping of ylabel
    plt.subplots_adjust(left=0.15)
    minx = min(x)
    maxx = max(x)

    x1, x2, y1, y2 = plt.axis()
    text = "p-value: " + str(pvalue)
    plt.text(maxx / 3, (y2 - y1) * 2 / 3, text, style='italic')



    # if pvalue == 0:
    #     pvalue = "0.000"

    return pvalue, solutionDistance, mean(x), std(x)


if __name__ == "__main__":
    (mmg,self_xassem,self_yassem,plot_filename,labels) = setup()
    num_bootstraps = 1000

    start_time = time.clock()
    result = calculateGeographicSolutionPValue(mmg, num_bootstraps,self_xassem,self_yassem,plot_filename,labels)
    end_time = time.clock()
    print result

    elapsed = end_time - start_time
    print "elapsed with %s bootstraps: %s secs" % (num_bootstraps, elapsed)