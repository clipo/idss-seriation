#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Various implementations of seriation algorithms where we minimize an objective function involving
interassemblage distance in some metric.  This includes "continuity" seriation, and what we did
with minimizing hamming distance in our 2015 paper with MJO et al.

"""

import networkx as nx
import numpy as np

from ..common_utilities import iso_filter_graphs, interassemblage_distance_euclidean, create_complete_distance_weighted_graph


def _continuitySeriationImpl(assemblages,assemblageFrequencies,assemblageSize,xAssemblage,yAssemblage):
    """


    :param assemblages:
    :param assemblageFrequencies:
    :param assemblageSize:
    :param xAssemblage:
    :param yAssemblage:
    :return:
    """

    graphList = []
    numGraphs = 0

    ## special case for the first time through
    ## set up all the initial pairs of two closest assemblages.
    for ass in assemblages:
        numGraphs += 1
        g = nx.Graph(startAssemblage=ass, End1=ass, is_directed=False)
        g.add_node(ass, name=ass, size=assemblageSize[ass], xCoordinate=xAssemblage[ass],
                   yCoordinate=yAssemblage[ass])
        minMatch = 10
        newNeighbor = ""
        ## now find the smallest neighbor from the rest of the assemblages.
        for potentialNeighbor in assemblages:
            if potentialNeighbor is not ass:
                diff = interassemblage_distance_euclidean(assemblageFrequencies[potentialNeighbor],
                                assemblageFrequencies[ass])

                # diff = self.calculateAssemblageEuclideanDistance(potentialNeighbor, ass)
                if diff < minMatch:
                    minMatch = diff
                    newNeighbor = potentialNeighbor
        g.add_node(newNeighbor, name=newNeighbor, xCoordinate=xAssemblage[newNeighbor],
                   yCoordinate=xAssemblage[newNeighbor], size=assemblageSize[newNeighbor])
        if minMatch == 0:  ## prevent divide by zero errors
            minMatch = 10
        g.add_path([ass, newNeighbor], weight=minMatch, inverseweight=(1 / minMatch ))
        g.graph['End2'] = newNeighbor
        graphList.append(g)   ## create a starting graph for each of assemblage put into an array
    ## filter list so that we just have non-isomorphic graphs (1<->2 and not 2<->1).
    filtered_graph_list = iso_filter_graphs(graphList)
    ## Now go through list looking at each one and increasing as long as I can. Add graphs when there are equivalent solutions
    for current_graph in filtered_graph_list:
        globalMinMatch = 10
        endMinMatch = {"End1": 10, "End2": 10}
        currentMinimumMatch = {}
        matchEnd = ""
        matchEndAssemblage = {}   ## this will contain the end assemblages and the differences
        #print "Now on GRAPH: ", current_graph

        ## go through this the # of times of the assemblages -2 (since the network already has 2 nodes)
        for count in range(0, len(assemblages) - 2):
            ## examine both ends to see which is the smallest summed difference.
            matchEndAssemblage = {}
            matchEnd = ""
            currentMinimumMatch = {}
            endMinMatch = {"End1": 10, "End2": 10}
            for assEnd in ("End1", "End2"):
                ## set the current end assemblages
                endAssemblage = current_graph.graph[assEnd]
                ## go through the other assemblages (not already in the graph.
                for assemblage in assemblages:
                    if assemblage not in current_graph.nodes():
                        #print "assemblage: ", assemblage, " is not in : ", current_graph.nodes()
                        diff = interassemblage_distance_euclidean(assemblageFrequencies[endAssemblage],
                                            assemblageFrequencies[assemblage])
                        # diff = self.calculateAssemblageEuclideanDistance(endAssemblage, assemblage)
                        if diff < endMinMatch[assEnd]:
                            endMinMatch[assEnd] = diff
                            currentMinimumMatch[assEnd] = assemblage
                            matchEndAssemblage[assEnd] = endAssemblage
                            matchEnd = assEnd

            ## at this point we should have the minimum distance match for each end.
            ## we then need to compare each end to find which one is the smallest
            ## three possibilities -- end1, end2 and both (i.e., the diff is the same)
            smallestMatchEnd = []
            assemblagesMatchedToEnd = []
            #print "endminmatch-end1: ", endMinMatch['End1'], "  endminmatch-end2: ", endMinMatch['End2']
            if endMinMatch['End1'] < endMinMatch['End2']:
                globalMinMatch = endMinMatch['End1']
                smallestMatchEnd.append('End1')
                assemblagesMatchedToEnd.append(currentMinimumMatch['End1'])
                #print "new match is to end1:  ", currentMinimumMatch['End1']

            elif endMinMatch['End2'] < endMinMatch['End1']:
                globalMinMatch = endMinMatch['End2']
                smallestMatchEnd.append('End2')
                assemblagesMatchedToEnd.append(currentMinimumMatch['End2'])
                #print "new match is to end2:  ", currentMinimumMatch['End1']
            elif endMinMatch['End1'] < 10 and endMinMatch['End2'] < 10:
                #print endMinMatch['End2'], "<--", endMinMatch['End1']
                #print "matchEnd: ", matchEnd
                #print currentMinimumMatch['End1'], "---", currentMinimumMatch['End2']
                globalMinMatch = endMinMatch['End1']
                smallestMatchEnd.append('End1')
                smallestMatchEnd.append('End2')
                assemblagesMatchedToEnd.append(currentMinimumMatch[matchEnd])

            ## find out if there are others that have the same minimum value
            for b in assemblages:
                if b not in current_graph.nodes() and b not in assemblagesMatchedToEnd:
                    diff = interassemblage_distance_euclidean(assemblageFrequencies[b],assemblageFrequencies[endAssemblage])
                    # diff = self.calculateAssemblageEuclideanDistance(b, endAssemblage)
                    if diff == globalMinMatch:
                        ## add this as a matched equivalent assemblage. We will then deal with more than one match
                        assemblagesMatchedToEnd.append(b)
            loop = 1
            firstOne = True

            original_network = current_graph.copy()
            for match in assemblagesMatchedToEnd:
                for endAss in smallestMatchEnd:
                    # for the first time we need to simply add it to the right end but after this we copy...
                    if firstOne == True:
                        firstOne = False
                        current_graph.add_node(match, name=match, xCoordinate=xAssemblage[match],
                                               yCoordinate=xAssemblage[match],
                                               size=assemblageSize[match])
                        if globalMinMatch == 0:
                            globalMinMatch = 10
                        current_graph.add_path([match, matchEndAssemblage[endAss]], weight=globalMinMatch,
                                               inverseweight=(1 / globalMinMatch ))
                        current_graph.graph[endAss] = match

                    ## if there are more than one we need to copy first before adding node
                    else:
                        loop += 1
                        #print "Loop: ", loop
                        new_network = original_network.copy()
                        new_network.add_node(match, name=match, xCoordinate=xAssemblage[match],
                                             yCoordinate=xAssemblage[match], size=assemblageSize[match])
                        if globalMinMatch == 0:
                            globalMinMatch = 10
                        new_network.add_path([matchEndAssemblage[endAss], match], weight=globalMinMatch,
                                             inverseweight=(1 / globalMinMatch ))
                        new_network.graph[endAss] = match
                        filtered_graph_list.append(new_network)
                        numGraphs += 1
                        #print "Number of graphs: ", numGraphs, " -- ", len(filtered_graph_list)

    return filtered_graph_list


def _euclidean_minimum_spanning_tree_seriation_impl(assemblages,assemblageFrequencies,assemblageSize,xAssemblage,yAssemblage):
    """


    1.  Form the complete graph on the assemblage set V, with weights corresponding to Euclidean distance
        between assemblage pairs.
    2.  Use Prim's algorithm


    :param assemblages:
    :param assemblageFrequencies:
    :param assemblageSize:
    :param xAssemblage:
    :param yAssemblage:
    :return:
    """
    cg = create_complete_distance_weighted_graph(assemblages,assemblageFrequencies,interassemblage_distance_euclidean)
    mst_g = nx.minimum_spanning_tree(cg)
    return mst_g