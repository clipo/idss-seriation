#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Utility functions employed by seriation code across classes, driver programs, and automated tests.  These
functions need to be readily accessible at the package level but outside classes like IDSS etc.

"""
import collections
import numpy as np
import networkx as nx


def iso_filter_graphs(list):
    newlist = []
    compare = lambda x, y: collections.Counter(x) == collections.Counter(y)
    for g in list:
        addList = True
        for h in newlist:
            #print "g: ",g.nodes(),"--- h: ",h.nodes(), "----> ", compare(g.nodes(),h.nodes())
            if compare(g.nodes(), h.nodes()) == True:
                addList = False
        if addList == True:
            newlist.append(g)

    return newlist


def interassemblage_distance_euclidean(assemblage1freq, assemblage2freq):
    """
    Efficient calculation of Euclidean distance between two assemblages using Numpy
    dot product.

    :param assemblage1freq: List of frequencies for assemblage 1
    :param assemblage2freq: List of frequencies for assemblage 2
    :return:
    """
    a1 = np.array(assemblage1freq)
    a2 = np.array(assemblage2freq)
    return np.asscalar(np.sqrt(np.dot(a1-a2,a1-a2)))