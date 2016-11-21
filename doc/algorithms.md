# Filter Subsolutions Algorithm #

Version 2.5.0

## Purpose ##

Solution search for seriation often turns up partial seriation solutions which are subsets of one another.  For example, the list of subsolutions may turn up A->B->C->D, and later in the list, A->B->C.  The latter is a subset of the former, so to form the full seriation solution, we can prune the shorter subsets to reduce overall computation of redundant possibilities.  

## Input ##

The algorithm begins with a list/array of NetworkX graphs, each representing a possible seriation solution, usually of a subset of assemblages.  

## Algorithm ##

1.  Find the longest subsolution in the input array, and add it to the output list.
1.  For each graph T in the full list of candidate subsolutions:
	1.  Find the vertex set of the graph T
	1.  For each graph F in the output (filtered) list:
		1.  Find the vertex set of the graph F
		1.  Find the set difference between V(T) and V(F)
		1.  If there are no vertices in T not in F, mark T as overlapping
	1.  If, for a given T, it overlapped with any F, ignore it.  Otherwise, add T to the output list

## Output ##

A filtered list of the input graphs, with any shorter overlaps omitted.  The net result is a list of graphs, each of which differs from all others in at least one element in their vertex set.

## Remarks ##

Performance is improved by caching the vertex sets of each graph in T and F, since these are used O(n^2) times.  


# Interassemblage Euclidean Distance #

Version 2.5.0

## Purpose ##

Calculate the "distance" between assemblages based on the type frequencies, using the L2 or Euclidean distance metric.  

## Input ##

A list of assemblage frequencies, in the same type order, for two assemblages A and B.  

## Algorithm ##

1.  Form a Numpy vector for each list of frequencies, for assemblages A and B.
1.  Calculate the sqrt of the dot product of A-B, A-B.  

## Output ##

A single floating point number giving the Euclidean distance metric between two sets of type frequencies.

## Remarks ##

Since type frequencies are input to the seriation algorithm and do not change, inter-assemblage distances can be calculated once and cached rather than recalculated in various places.


# Sumgraph By Weight Algorithm #

Version 2.5.0

## Purpose ##

Since all valid subsolutions carry information about heritable continuity between assemblages, we can ask what structure exists in the additive graph of subsolutions.  This "summed graph" or "sumgraph," describes the total set of relations between assemblages for which seriation criteria (unimodality or continuity) are met.  In the "sumgraph by weight," edge weights are assigned as functions of the Euclidean distance between assemblage type frequencies.  


## Input ##

The algorithm begins by taking a list/array of NetworkX graphs, filtered such that each graph in the list has unique elements in its vertex set.

## Algorithm ##

1.  Form the empty graph S
1.  Over all graphs G in the filtered solution set F, find the global min and max Euclidean distances between assemblages.
1.  For each graph G in the filtered solution set F:
	1.  Add V(G) to S, ignoring/collapsing duplicates
1.  For each graph G in the filtered solution set F:
	1.  Add E(G) to S, providing three edge weight attributes:
		1.  Simple L2/Euclidean distance
		1.  L2/Euclidean distance normalized to the min/max range of values
		1.  Inverse normalized distance (makes some calculations easier)
1.  Return the weighted graph S

## Output ##

A NetworkX graph with all vertices included in the filtered solution set F, with all edges present in those filtered solutions, with three sets of edge weights that are functions of interassemblage Euclidean distance.  



