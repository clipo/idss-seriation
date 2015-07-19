__author__ = 'clipo'

import logging as logger
import uuid
from pylab import *
import networkx as nx
import re
import pickle
# import time
# import multiprocessing

def filter_list(full_list, excludes):
    s = set(excludes)
    return (x for x in full_list if x not in s)


def worker(networks, out_q):
    """ The worker function, invoked in a process. The results are placed in
        a dictionary that's pushed to a queue.
    """

    ## unpickle the stuff I need for parallel processing, but only do it the first
    ## time worker is called for this process, otherwise we do a slow operation everytime

    global validComparisonsHash
    global pairGraph
    global assemblages
    global args
    global typeFrequencyUpperCI
    global typeFrequencyLowerCI

    validComparisonsHash=pickle.load(open('.p/validComparisonsHash.p','rb'))
    pairGraph=pickle.load(open('.p/pairGraph.p','rb'))
    assemblages=pickle.load(open('.p/assemblages.p','rb'))
    args=pickle.load(open('.p/args.p','rb'))  
    
    if args['bootstrapCI'] not in (None, ""):
        typeFrequencyUpperCI=pickle.load(open('.p/typeFrequencyUpperCI.p','rb'))
        typeFrequencyLowerCI=pickle.load(open('.p/typeFrequencyLowerCI.p','rb'))

    outdict = []

    for n in networks:
        output=checkForValidAdditions(n)
        for o in output:
            outdict.append(o)
    out_q.put(outdict)

def comparisonWithCI(first, second, trait, typeFrequencyUpperCI, typeFrequencyLowerCI):
    firstUp = typeFrequencyUpperCI[first][trait]
    firstLow = typeFrequencyLowerCI[first][trait]
    secondUp = typeFrequencyUpperCI[second][trait]
    secondLow = typeFrequencyLowerCI[second][trait]

    if firstUp < secondLow:
        return 'U'
    elif firstLow > secondUp:
        return 'D'
    # TODO XRC this will never happen because of floating point arithmetic        
    return 'M'

def comparisonWithAbsolute(first, second, trait):
    if first < second:
        return 'U'
    elif first > second:
        return 'D'
    return 'M'

def checkForValidAdditions(nnetwork):
    pattern_to_find = re.compile('DU|DM*U')
    array_of_new_networks = []  ## a list of all the valid new networks that we run into

    # XRC code
    # 1. look for all assemblages not currently part of the network
    candidates = list()
    for assemblage in assemblages:
        if assemblage in nnetwork.nodes():
            continue
        candidates.append(assemblage)
    logger.debug('candidates:'+str(candidates)+' for network: '+str(nnetwork.nodes()))

    if len(candidates)==0:
        logger.debug('no available candidates, exiting')
        return

    numTraits = len(assemblages[candidates[0]])
    for candidate in candidates:
        logger.debug('begin evaluating:'+str(candidate))
        valid = True
        path = nx.shortest_path(nnetwork, nnetwork.graph["End1"], nnetwork.graph["End2"])
        logger.debug('\tpath:'+str(path))
        for i in range(numTraits): 
            first = candidate
            # evaluate
            c = ''
            logger.debug('\tcolumn: '+str(i)+':')

            for j in range(0,len(path)):
                second = path[j]
                if args['bootstrapCI'] not in (None, ""):
                    c += comparisonWithCI(first, second, i, typeFrequencyUpperCI, typeFrequencyLowerCI)
                else:
                    c += comparisonWithAbsolute(first, second, i)

                first = second
                
            logger.debug('\tcolumn: '+str(i)+':'+c)
            test = pattern_to_find.search(c)
            if test not in (None, ""):
                valid = False
                break
        logger.debug('end evaluating:'+str(candidate)+' - valid? '+str(valid))

        if valid:
            logger.debug('valid solution:'+str(candidate)+' to: '+str(path))
            graphID = uuid.uuid4().urn
            new_network = nnetwork.copy()
            new_network.graph["GraphID"] = graphID
            new_network.graph["name"] = graphID

            # add new node
            new_network.add_node(candidate, name=candidate)
            # add edge from new node to old End1
            new_network.add_edge(candidate, path[0])
            # set new node as new End1 of new_network
            new_network.graph['End1'] = candidate
            
            ## copy this solution to the new array of networks
            array_of_new_networks.append(new_network)
    return array_of_new_networks

