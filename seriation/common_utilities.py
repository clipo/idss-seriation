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
import itertools



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


def interassemblage_geographic_distance(a1, a2, xAssemblages, yAssemblages):
    """Efficient calculation of Euclidean geographic distance between two
    assemblages using Numpy operations

    :param a1:
    :param a2:
    :param xAssemblages:
    :param yAssemblages:
    :return:
    """
    raise NotImplemented


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


def create_complete_distance_weighted_graph(assemblages, assemblageFreq, distanceFunction):
    """Create a fully connected network from the list of assemblages, with edges weighted by
    the distance function given between assemblage frequencies.  This artificial graph is useful
    mainly for passing to Kruskal's algorithm or Prim's for calculating the MST with
    respect to those  distances.

    :param assemblages: list of assemblages
    :param assemblageFreq: dict of assemblage frequency lists, with assemblages as key
    :param distanceFunction: function which takes two lists of trait frequencies, and returns a distance metric
    :return: NetworkX graph
    """

    g = nx.Graph()
    for assem in assemblages:
        g.add_node(assem)

    for pair in itertools.product([assemblages,assemblages]):
        if pair[0] == pair[1]:
            # don't create self edges
            continue

        if g.has_edge(pair[0], pair[1]) is False:
            distance = distanceFunction(assemblageFreq[pair[0]], assemblageFreq[pair[1]])
            g.add_edge(pair[0], pair[1], weight=distance)

    return g


def calculateFstForGraph(graph,assemblageFreq):
    """Given a graph of assemblages, calculate the Fst for the set of assemblages.
    :param graph: NetworkX graph of assemblages
    :param assemblageFreq: dict of assemblage frequency lists, with assemblages as key
    :return: Fst value
    """

    Hs = 0.0

    average_Type_Frequencies=np.array([])
    ## iterate through the nodes in the graph
    num_of_columns=0

    for node in graph.nodes():

        ## get the list of types for the assemblages
        typelist=assemblageFreq[node]
        ## count the columns. We do this so we can match the columns between assembalges to do the calculations
        num_of_columns = len(typelist)
        # Hs:  Calculate the average of these subpopulation heterozygosities
        Hs_array=np.asarray(typelist)
        Hs += np.mean(Hs_array)

    Hs_total=Hs/len(graph.nodes())
    Ht=0.0

    for i in range(0, num_of_columns):
        type_array = np.array([])
        sum=0
        count=0
        for node in graph.nodes():
            typelist = assemblageFreq[node]
            np.append(type_array,typelist[i])
            sum += typelist[i]
            count +=1
        np.append(average_Type_Frequencies,sum/count)

    Ht=np.prod(average_Type_Frequencies)

    Fst=(Ht-Hs_total)/Ht
    return Fst





