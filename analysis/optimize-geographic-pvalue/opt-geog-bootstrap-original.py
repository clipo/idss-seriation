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
    solutionDistance = 0
    assemblagesInSolution = []
    edges = 0
    for e in graph.edges_iter():
        d = graph.get_edge_data(*e)
        edges += 1
        fromAssemblage = e[0]
        toAssemblage = e[1]
        solutionDistance += math.sqrt(
            pow((int(self_xassem[fromAssemblage]) - int(self_xassem[toAssemblage])), 2)
            + pow((int(self_yassem[fromAssemblage]) - int(self_yassem[toAssemblage])), 2))
        assemblagesInSolution.append(fromAssemblage)
        assemblagesInSolution.append(toAssemblage)
    assemblageSet = set(assemblagesInSolution)
    #print "solution Distance: %s" % solutionDistance

    rnd.seed()  # uses system time to initialize random number generator, or you can pass in a deterministic seed as an argument if you want
    x = []
    pvalueScore = 0.000
    for b in range(0, num_bootstrap):
        # code to use to generate K pairs
        list1 = labels
        list2 = labels

        testDistance = 0
        for p in range(0, edges - 1):
            test = False
            p1 = p2 = ""
            while test is False:
                p1 = rnd.choice(list1)
                p2 = rnd.choice(list2)
                if p1 != p2:
                    test = True
            #print "Pair: ", p1, "-", p2
            testDistance += math.sqrt(pow((int(self_xassem[p1]) - int(self_xassem[p2])), 2)
                                      + pow((int(self_yassem[p1]) - int(self_yassem[p2])), 2))
            #print "Test Distance: ", testDistance

        if testDistance <= solutionDistance:
            # print "TEST is less than solutionDistance: ",testDistance
            pvalueScore += 1
        x.append(testDistance)
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
    pvalue = pvalueScore / num_bootstrap
    x1, x2, y1, y2 = plt.axis()
    text = "p-value: " + str(pvalue)
    plt.text(maxx / 3, (y2 - y1) * 2 / 3, text, style='italic')

    if pvalue == 0:
        pvalue = "0.000"
    return pvalue, solutionDistance, mean(x), std(x)


if __name__ == "__main__":
    (mmg,self_xassem,self_yassem,plot_filename,labels) = setup()
    num_bootstraps = 1000000

    start_time = time.clock()
    calculateGeographicSolutionPValue(mmg, num_bootstraps,self_xassem,self_yassem,plot_filename,labels)
    end_time = time.clock()

    elapsed = end_time - start_time
    print "elapsed with %s bootstraps: %s secs" % (num_bootstraps, elapsed)