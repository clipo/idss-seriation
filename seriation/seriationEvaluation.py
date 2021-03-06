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


def worker(pickledir, networks, out_q):
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

    vchashfile = pickledir + "/validComparisonsHash.p"
    pgfile = pickledir + "/pairGraph.p"
    assemfile = pickledir + "/assemblages.p"
    argsfile = pickledir + "/args.p"
    fucifile = pickledir + "/typeFrequencyUpperCI.p"
    flcifile = pickledir + "/typeFrequencyLowerCI.p"


    validComparisonsHash=pickle.load(open(vchashfile,'rb'))
    pairGraph=pickle.load(open(pgfile,'rb'))
    assemblages=pickle.load(open(assemfile,'rb'))
    args=pickle.load(open(argsfile,'rb'))
    typeFrequencyUpperCI=pickle.load(open(fucifile,'rb'))
    typeFrequencyLowerCI=pickle.load(open(flcifile,'rb'))

    outdict = []

    for n in networks:
        output=checkForValidAdditions(n)
        for o in output:
            outdict.append(o)
    out_q.put(outdict)



def checkForValidAdditions(nnetwork):
    solutionsChecked=0
    pattern_to_find = re.compile('DU|DM*U')

    array_of_new_networks = []  ## a list of all the valid new networks that we run into
    maxnodes = len(nnetwork.nodes())

    for assEnd in ("End1", "End2"):
        if assEnd == "End1":
            otherEnd = "End2"
        else:
            otherEnd = "End1"

        endAssemblage = nnetwork.graph[assEnd]

        validAssemblages=validComparisonsHash[endAssemblage]


        ######################################################################################
        for testAssemblage in validAssemblages:
            if assEnd == "End1":
                if nnetwork.graph["End1"] == nnetwork.graph["End2"]:
                    continue
                else:
                    path = nx.shortest_path(nnetwork, nnetwork.graph["End1"], nnetwork.graph["End2"])
                    #print "checking path between: ", nnetwork.graph["End1"], " and ", nnetwork.graph["End2"]
                    if len(path)<2:
                        print path
                        sys.exit()
                    innerNeighbor = path[1]
            elif assEnd == "End2":
                if nnetwork.graph["End1"] == nnetwork.graph["End2"]:
                    continue
                else:
                    path = nx.shortest_path(nnetwork, nnetwork.graph["End2"], nnetwork.graph["End1"])
                    innerNeighbor = path[1]
            else: ## sanity check
                sys.exit("Quitting due to errors.")
            ## Sanity check
            if innerNeighbor is None:
                sys.exit("Quitting due to errors.")
            solutionsChecked +=1 # increment counter
            c = pairGraph.get_edge_data(innerNeighbor, endAssemblage)
            comparison = c['weight']
            comparisonMap = ""
            oneToColumns = range(len(assemblages[testAssemblage]))

            error = 0  ## set the error check to 0
            for i in oneToColumns:
                newstring = ""
                p = nx.shortest_path(nnetwork, nnetwork.graph[assEnd], nnetwork.graph[otherEnd])
                newVal = assemblages[testAssemblage][i]
                previousAssemblage = testAssemblage
                for compareAssemblage in p:
                    oldVal = assemblages[compareAssemblage][i]

                    if args['bootstrapCI'] not in (None, 0, "", "0", False ):
                        upperCI_test = typeFrequencyUpperCI[previousAssemblage][i]
                        lowerCI_test = typeFrequencyLowerCI[previousAssemblage][i]
                        upperCI_end = typeFrequencyUpperCI[compareAssemblage][i]
                        lowerCI_end = typeFrequencyLowerCI[compareAssemblage][i]

                        if upperCI_test < lowerCI_end:
                            newstring += "D"
                        elif lowerCI_test > upperCI_end:
                            newstring += "U"
                        else:
                            newstring += "M"
                    else:
                        #print("Outer value: %f Inner value: %f"%(oldVal, newVal))
                        if newVal < oldVal:
                            newstring += "U"
                        elif newVal > oldVal:
                            newstring += "D"
                        elif newVal == oldVal:
                            newstring += "M"
                        else:
                            logger.debug("Error. Quitting.")
                            sys.exit("got null value in comparison of value for type %d in the comparison of %s", i,
                                     compareAssemblage)
                        newVal = oldVal

                    previousAssemblage = compareAssemblage

                test = pattern_to_find.search(newstring)
                if test not in (None, ""):
                    error += 1

            if error == 0:
                graphID = uuid.uuid4().urn
                new_network = nnetwork.copy()
                new_network.graph["GraphID"] = graphID
                new_network.graph["name"] = graphID
                path = nx.shortest_path(nnetwork, nnetwork.graph["End1"], nnetwork.graph["End2"])

                new_network.add_node(testAssemblage, name=testAssemblage, end=1, site="end")
                new_network.add_node(endAssemblage, name=endAssemblage, site="middle", end=0)
                new_network.add_edge(testAssemblage, endAssemblage, weight=comparisonMap, end=1, site="end",
                                     GraphID=graphID)

                new_network.graph[assEnd] = testAssemblage
                path = nx.shortest_path(new_network, new_network.graph["End1"], new_network.graph["End2"])

                ## copy this solution to the new array of networks
                array_of_new_networks.append(new_network)

                if len(new_network) > maxnodes:
                    maxnodes = len(new_network)

    # end_time = time.clock()
    # elapsed = end_time - start_time
    # proc_name = multiprocessing.current_process().name
    # print "seriationEvaluation in process: %s elapsed: %s" % (proc_name, elapsed)
    return array_of_new_networks



