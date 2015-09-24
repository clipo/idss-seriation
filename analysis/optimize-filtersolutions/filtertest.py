#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import pickle
import logging
import networkx as nx
import pprint as pp
import argparse
import time
from networkx.algorithms import isomorphism
import itertools

LEVEL_TRACE = 5
def idss_trace(self, message, *args, **kws):
    logging.log(LEVEL_TRACE, message, *args, **kws)
    



def get_longest_subsolution(all_solutions):
    cur_longest = []
    for sol in all_solutions:
        if len(sol) > len(cur_longest):
            cur_longest = sol
    return cur_longest


def filterSolutions(self, end_solutions, all_solutions):
    ################################################# FILTERING  ####################################
    # now do some weeding. Basically start with the last network ( largest),
    #  and work backwards to smaller and smaller solutions. Ignore any
    # network that is already represented larger since these are trivial (e.g., A->B->C->D already covers
    # A->C->D.) That should then leave all the unique maximum solutions (or so it seems)
    ################################################# FILTERING  ####################################
    num_comparisons = 0
    filteredarray = []

    log.trace("--- Filtering solutions so we only end up with the unique ones.")
    log.trace("--- Start with %d solutions.", len(end_solutions))
    filteredarray.append(end_solutions)
    newOne = 0
    for tnetwork in reversed(all_solutions):
        log.debug("trying tnetwork: %s of length %s", tnetwork, len(tnetwork.nodes()))
        exists = 0
        for fnetwork in filteredarray:
            fnetworkArray = fnetwork.nodes()
            log.trace("----fnetworkArray: %s", fnetworkArray)
            tnetworkArray = tnetwork.nodes()
            log.trace("----tnetworkArray: %s", tnetworkArray)
            minus = list(set(tnetworkArray) - set(fnetworkArray))
            log.trace("difference between: %s ", minus)
            change = len(minus)
            log.trace("Change: %d", change)
            if change > 0 and len(list(set(minus) - set(fnetworkArray))):
                newOne += 1
            else:
                exists += 1

            num_comparisons += 1

        if exists == 0:
            log.trace("pushing tnetwork to list of filtered arrays")
            filteredarray.append(tnetwork)
        exists = 0

    log.trace("End with %d solutions.", len(filteredarray))
    log.info("filterSolutions performed %s comparisons", num_comparisons)
    filterCount = len(filteredarray)

    return filteredarray


def _get_cached_nodes(cache, solution):
    if solution not in cache:
        cache[solution] = set(solution.nodes())
    return cache[solution]

def filterSolutions_1(self, end_solutions, all_solutions):
    ################################################# FILTERING  ####################################
    # now do some weeding. Basically start with the last network ( largest),
    #  and work backwards to smaller and smaller solutions. Ignore any
    # network that is already represented larger since these are trivial (e.g., A->B->C->D already covers
    # A->C->D.) That should then leave all the unique maximum solutions (or so it seems)
    ################################################# FILTERING  ####################################

    filteredarray = []
    num_comparisons = 0
    node_cache = dict()

    log.trace("--- Filtering solutions so we only end up with the unique ones.")
    log.trace("--- Start with %d solutions.", len(end_solutions))
    filteredarray.append(end_solutions)
    newOne = 0
    for tnetwork in reversed(all_solutions):
        log.trace("trying tnetwork: %s of length %s", tnetwork, len(tnetwork.nodes()))
        tnetwork_nodeset = _get_cached_nodes(node_cache, tnetwork)
        log.trace("Testing tnetworkArray: %s against accepted solutions", tnetwork_nodeset)
        exists = 0

        for fnetwork in filteredarray:
            fnetwork_nodeset = _get_cached_nodes(node_cache, fnetwork)
            log.trace("...trial: fnetworkArray: %s", fnetwork_nodeset)

            diff = tnetwork_nodeset - fnetwork_nodeset

            log.trace("...difference between: %s ", diff)
            log.trace("...Change: %d", len(diff))

            if len(diff) > 0 and len(diff - fnetwork_nodeset):
                newOne += 1
            else:
                exists += 1

            num_comparisons += 1
        if exists == 0:
            log.trace("pushing tnetwork to list of filtered arrays")
            filteredarray.append(tnetwork)
        exists = 0

    log.trace("End with %d solutions.", len(filteredarray))
    log.trace("filterSolutions_1 performed %s comparisons", num_comparisons)

    return filteredarray






def _node_name_matcher(n1,n2):
    if n1['name'] == n2['name']:
        return True
    else:
        return False

def filterSolutions_2(self, all_solutions):
    """

    Filter out solutions that are subgraphs of other solutions, such that if we
    have A-B-C-D, we do not retain B-C-D, but would retain A-B-D.

    This version of the algorithm examines both node and edge patterns, by examining
    whether two solutions, G and H, are either isomorphic to each other, or if
    G is isomorphic to any subgraph in H.  The resulting list of solutions contains
    only those solutions which are not subgraph isomorphic to any other solution.

    To do this efficiently and allow for parallelization if needed, we model the
    pairs of subsolutions as a generator of combinations of size 2, which means
    that we only get each pair of subsolutions once, and we never hold the entire
    list of pairs in memory (important when the number of pairs reaches into the
    multiple billions!).  Each pair combination is then evaluated for isomorphism
    and subgraph isomorphism using the VF2 algorithm (cite below).

    Any pair that returns True for either isomorphism or subgraph isomorphism thus
    has one subsolution that is part of the other or equivalent, and we tag the
    SMALLER of the two for deletion, and add equivalences to a list of equal solutions.

    to parallelize this operation, we can distribute pairs to worker threads or processes,
    each returning lists for deletion and equivalence.  The multiple lists are coalesced
    and collapsed for uniqueness after all parallel workers complete processing the
    entire generator of pairs.

    Once all of the evaluations are performed, we collapse the set of smaller
    solutions, and delete them from a copy of the original solution list.  We then
    remove any of the smaller solutions which appear in the list of equivalences
    as well, and add any solutions which appear in neither.  The result is the
    filtered list of viable solutions to pass to the next step in seriation.

    Citation:
    @article{Cordella:2004fa,
    author = {Cordella, Luigi P and Foggia, Pasquale and Sansone, Carlo and Vento, Mario},
    title = {{A (sub)graph isomorphism algorithm for matching large graphs}},
    journal = {Pattern Analysis and Machine Intelligence, IEEE Transactions on},
    year = {2004},
    volume = {26},
    number = {10},
    pages = {1367--1372},
    publisher = {IEEE},
    doi = {10.1109/TPAMI.2004.75},
    url = {http://ieeexplore.ieee.org/lpdocs/epic03/wrapper.htm?arnumber=1323804},
    }

    :param all_solutions:
    :return:  retained_solutions:  list
    """

    retained_solutions = set()
    smaller_solutions_to_delete = set()
    equivalent_solutions = []
    solutions_from_unmatched_pairs = set()

    for pair in itertools.combinations(all_solutions,2):
        gm = isomorphism.GraphMatcher(pair[0], pair[1], node_match=_node_name_matcher)
        if gm.is_isomorphic():
            equivalent_solutions.append(pair)
        elif gm.subgraph_is_isomorphic():
            pair_zero_len = len(pair[0].nodes())
            pair_one_len = len(pair[1].nodes())
            if pair_zero_len < pair_one_len:
                smaller_solutions_to_delete.add(pair[0])
            else:
                smaller_solutions_to_delete.add(pair[1])
        else:
            solutions_from_unmatched_pairs.add(pair[0])
            solutions_from_unmatched_pairs.add(pair[1])

    # Now we reduce the scored pairs to a unique list of subsolutions

    retained_solutions.update(solutions_from_unmatched_pairs)
    retained_solutions.difference_update(smaller_solutions_to_delete)

    # now, we take the pairs that were truly equivalent (isomorphic) and if neither solution in the pair is represented,
    # we simply choose the first one (convention).  It should not be the case that both are represented already
    # but if that is the case, we remove the second one (by convention).

    for pair in equivalent_solutions:
        matches = 0
        if pair[0] in retained_solutions:
            matches += 1
        if pair[1] in retained_solutions:
            matches += 1
        if matches == 0:
            retained_solutions.add(pair[0])
        if matches == 2:
            retained_solutions.remove(pair[1])

    log.trace("End with %d solutions.", len(retained_solutions))

    return list(retained_solutions)












if __name__ == "__main__":
    global log
    parser = argparse.ArgumentParser(description='Conduct an iterative deterministic seriation analysis')
    parser.add_argument('--debug', '-d', type=int, default=0, help='Sets the DEBUG flag for massive amounts of annotated output.')
    args = parser.parse_args()

    logging.addLevelName(LEVEL_TRACE, 'TRACE')
    logging.Logger.trace = idss_trace

    if args.debug is not None:
        if args.debug == 0:
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')
        elif args.debug > 1:
            logging.basicConfig(level=LEVEL_TRACE, format='%(asctime)s %(levelname)s: %(message)s')
        elif args.debug == 1:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

    log = logging.getLogger()




    all_solutions = pickle.load(open("pfg-prefilter-allsolutions.pickle",'rb'))

    print "length of unfiltered solution list: %s" % len(all_solutions)

    longest = get_longest_subsolution(all_solutions)

    time_start = time.time()
    filtered_array = filterSolutions(None, longest, all_solutions)
    elapsed = time.time() - time_start

    time_start_1 = time.time()
    filtered_array_1 = filterSolutions_1(None, longest, all_solutions)
    elapsed_1 = time.time() - time_start_1

    # time_start_2 = time.time()
    # filtered_array_2 = filterSolutions_2(None, all_solutions)
    # elapsed_2 = time.time() - time_start_2

    # pp.pprint(filtered_array_2)

    speedup_1 = elapsed / elapsed_1
    # speedup_2 = elapsed / elapsed_2

    print "length of filterSolutions final array: %s" % len(filtered_array)
    print "length of filterSolutions_1 final array: %s" % len(filtered_array_1)
    # print "length of filterSolutions_2 final array: %s" % len(filtered_array_2)
    print "filterSolutions execution time: %s" % elapsed
    print "filterSolutions_1 execution time: %s" % elapsed_1
    # print "filterSolutions_2 execution time: %s" % elapsed_2

    print "filterSolutions_1 speedup: %s" % speedup_1
    # print "filterSolutions_2 speedup: %s" % speedup_2

