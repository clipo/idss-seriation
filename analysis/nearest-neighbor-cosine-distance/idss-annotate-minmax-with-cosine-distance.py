import annoy
import csv
import logging as log
import argparse
import pprint as pp
from annoy import AnnoyIndex
import itertools
import operator
import networkx as nx
from networkx.utils import open_file, make_str
import sys
from decimal import *
import re
import os

def setup():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputfile", help="Path to input CSV file",required=True)
    parser.add_argument("--minmaxgml", help="Path to input minmax GML file", required=True)
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--outputdirectory", help="path to directory for exported data files", required=True)
    parser.add_argument("--delimiter",help="Delimiter to use in parsing input file",default='\t')
    args = parser.parse_args()

    if args.debug is not None and int(args.debug) == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')



def parse_inputfile(file_path):
    types = []
    labels = []
    counts = dict()
    id_to_label = dict()
    label_to_id = dict()
    dimension = 0
    file = open(file_path, 'r')
    reader = csv.reader(file, delimiter=args.delimiter, quotechar='|')
    rows = 0
    for row in reader:
        # if header row, grab type names
        if rows == 0:
            row.pop(0)
            types = list(row)
        else:
            row_label = row[0]
            labels.append(row_label)
            row.pop(0)
            dimension = len(row)
            counts[row_label] = [int(x) for x in row]
            id_to_label[rows] = row_label
            label_to_id[row_label] = rows
        rows += 1
    file.close()

    return types, labels, counts, id_to_label, label_to_id,dimension


def build_index(counts,label_to_id,dimension):
    index = AnnoyIndex(dimension,metric='angular')
    for label,cnt_list in counts.items():
        id = label_to_id[label]
        index.add_item(id,cnt_list)

    index.build(100)
    return index



def annotate_nx_graph_with_distances(input_graph,pairwise_dist_map,label_to_id):
    """
    Iterates over the edges in a graph, annotating them with the pairwise
    distance derived from an Annoy nearest-neighbor model.
    """

    # base scheme has color sets from 3 to 9
    base_color_scheme = 'accent'

    # make a copy so we don't touch the original graph, we'll return a new one
    g = input_graph.copy()

    # sometimes the "id" attribute is also the label, which we don't want for DOT production
    for node, data in g.nodes_iter(data=True):
        g.node[node]['assemblage'] = g.node[node]['label']
    g = nx.convert_node_labels_to_integers(g)

    # grandchildren might point their child_of attribute at a node which is not present
    # in this minmax graph given that we're operating with a sample of assemblages.
    # So when we find a child_of that's not represented in the
    for node, data in g.nodes_iter(data=True):
        lab = g.node[node]['assemblage']
        short_label = lab.replace('assemblage-','')
        #del g.node[node]['label']
        g.node[node]['short_label']= short_label

    for node, data in g.nodes_iter(data=True):
        g.node[node]['label'] = g.node[node]['short_label']


    for edge in g.edges_iter():
        edata = g.get_edge_data(*edge)

        assem1 = g.node[edge[0]]['assemblage']
        assem2 = g.node[edge[1]]['assemblage']
        id1 = label_to_id[assem1]
        id2 = label_to_id[assem2]

        dist = 0.0
        tup = (id1,id2)
        tup2 = (id2,id1)


        if tup in pairwise_dist_map:
            dist = pairwise_dist_map[tup]
        elif tup2 in pairwise_dist_map:
            dist = pairwise_dist_map[tup2]
        else:
            sys.exit(1)

        edata['cosine_dist'] = dist

    return g


def save_gml(g,suffix):
    """
    Saves a GML file to args.outputdirectory, with the basename of the args.inputfile,
    and a suffix as given, with extension .gml

    :param g:
    :param suffix:
    :return:
    """
    basefile = args.inputfile[0:-4]
    outputfile = args.outputdirectory + '/' + basefile + '-' + suffix + ".gml"
    nx.write_gml(g, outputfile)

def read_gml_and_normalize_floats(file):
    """
    Read a GML file line by line, looking for scientific notation
    and when found, normalize it using the Decimal library.
    Then pass the lines of text to networkx parse_gml to
    parse it.  This is a drop-in replacement for read_gml()
    """

    exp_regex = re.compile(r"(\d+(\.\d+)?)[Ee](\+|-)(\d+)")

    input_lines = []

    with open(file, 'rb') as gmlfile:
        for line in gmlfile:
            result = exp_regex.search(line)
            if result is not None:
                matched_value = result.group(0)
                replacement = str(remove_exponent(Decimal(float(matched_value))))
                line = line.replace(matched_value, replacement)
                #log.debug("Replacing %s with %s", matched_value, replacement)

            input_lines.append(line)

    return nx.parse_gml(input_lines)

def remove_exponent(d):
    '''Remove exponent and trailing zeros.  Used to ensure that we don't have
    scientific notation in node or edge attributes when we write the GML

    >>> remove_exponent(Decimal('5E+3'))
    Decimal('5000')

    '''
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()




def get_graphics_title(root, sample_type):
    import re

    occur = 12  # get the UUID and sampling fractions, and whether it's a minmax graph
    indices = [x.start() for x in re.finditer("-", root)]
    uuid_part = root[0:indices[occur-1]]
    rest = root[indices[occur-1]+1:]

    title = args.experiment
    title += "  "
    title += sample_type
    title += "  "
    title += uuid_part
    title += "  "
    title += args.modeltype

    return title




def write_ordered_dot(N,path,dist_to_rank,name="minmax seriation graph"):
    """Write NetworkX graph G to Graphviz dot format on path.

    Path can be a string or a file handle.
    """
    try:
        import pydot
    except ImportError:
        raise ImportError("write_dot() requires pydot",
                          "http://code.google.com/p/pydot/")

    P=generate_ordered_dot(N, dist_to_rank,name)




    p = P.to_string();
    #log.debug("dot: %s", p)


    with open(path, 'wb') as pathfile:
        pathfile.write(p)
    return




def generate_ordered_dot(N, dist_to_rank, name=None):
    """
    The networkx write_dot() function generates
    """
    try:
        import pydot
    except ImportError:
        raise ImportError('to_pydot() requires pydot: '
                          'http://code.google.com/p/pydot/')

    # set Graphviz graph type
    if N.is_directed():
        graph_type='digraph'
    else:
        graph_type='graph'
    strict=N.number_of_selfloops()==0 and not N.is_multigraph()

    node_attrs = dict()
    node_attrs["shape"] = "circle"
    #node_attrs["label"] = ""
    node_attrs["style"] = "filled"

    graph_defaults=N.graph.get('graph',{})
    graph_defaults["ratio"] = "auto"
    graph_defaults["labelloc"] = "b"
    graph_defaults["label"] = name
    graph_defaults["pad"] = "1.0"


    if name is None:
        P = pydot.Dot(graph_type=graph_type,strict=strict,**graph_defaults)
    else:
        P = pydot.Dot('"%s"'%name,graph_type=graph_type,strict=strict,
                      **graph_defaults)
    try:
        P.set_node_defaults(**node_attrs)
    except KeyError:
        pass
    try:
        P.set_edge_defaults(**N.graph['edge'])
    except KeyError:
        pass

    for n,nodedata in sorted(N.nodes_iter(data=True), key=lambda n: int(n[0])):
        str_nodedata=dict((k,make_str(v)) for k,v in nodedata.items())

        if "name" in str_nodedata:
            del str_nodedata['name']

        p=pydot.Node(make_str(n),**str_nodedata)
        P.add_node(p)

    if N.is_multigraph():
        for u,v,key,edgedata in N.edges_iter(data=True,keys=True):
            str_edgedata=dict((k,make_str(v)) for k,v in edgedata.items())
            edge=pydot.Edge(make_str(u),make_str(v),key=make_str(key),**str_edgedata)
            P.add_edge(edge)

    else:



        for u,v,edgedata in sorted(N.edges_iter(data=True), key=lambda u: int(u[0]) ):
            str_edgedata=dict((k,make_str(v)) for k,v in edgedata.items())
            dist = str_edgedata['cosine_dist']
            dist.encode('ascii','ignore')
            rank = dist_to_rank[dist]
            label = rank + "-" + dist
            str_edgedata['label'] = label
            str_edgedata['len'] = 2
            if int(v) < int(u) :
                edge = pydot.Edge(make_str(v),make_str(u),**str_edgedata)
            else:
                edge=pydot.Edge(make_str(u),make_str(v),**str_edgedata)
            P.add_edge(edge)

    return P


def build_minimum_angular_distance_graph(dist_map,id_to_label,dist_to_rank):
    """
    Builds a continuity-style graph using the minimum angular distances between
    assemblages.  The algorithm is to build the complete graph with the angular
    distance representing edge weight, and then prune edges

    :param dist_map: dict with tuples of (id1,id2) as keys, angular distance as values
    :param id_to_label: dict of assemblage ID from edges to their textual labels
    :param dist_to_rank: dict with distance as key, sorted rank as value (1 being lowest distance)
    :return: NetworkX graph object
    """
    # start with an empty graph
    g = nx.Graph()

    for w in pairwise_dist.items():
        log.info("processing edge %s into the first stage complete graph", w)
        dist = w[1]
        end1 = w[0][0]
        end2 = w[0][1]

        if end1 not in g:
            g.add_node(end1)
        if end2 not in g:
            g.add_node(end2)
        g.node[end1]['label'] = id_to_label[end1]
        g.node[end2]['label'] = id_to_label[end2]
        g.add_edge(end1,end2,cosine_dist=dist,rank=dist_to_rank[str(dist)])

    shortest_paths = nx.shortest_path(g, weight="cosine_distance")

    #pp.pprint(shortest_paths)


    # g should now contain an annotated graph with the minimum required distances to link all vertices
    return g



# def build_minimum_angular_distance_graph(dist_map,id_to_label,dist_to_rank):
#     """
#     Builds a continuity-style graph using the minimum angular distances between
#     assemblages.  The algorithm is as follows:
#
#     1.  start with empty graph g, and a sorted list of edge -> distance pairs
#     2.  for each pair of edge -> distance:
#         a.  if edge0 and edge1 are not in g yet, create v0 and v1 in g
#         b.  if one end of the edge exists, but the other does not, add it only if
#             its edge dist is smaller than another edge with the existing vertex.
#
#     :param dist_map: dict with tuples of (id1,id2) as keys, angular distance as values
#     :param id_to_label: dict of assemblage ID from edges to their textual labels
#     :param dist_to_rank: dict with distance as key, sorted rank as value (1 being lowest distance)
#     :return: NetworkX graph object
#     """
#     # start with an empty graph
#     g = nx.Graph()
#
#     for w in sorted(pairwise_dist.items(), key=operator.itemgetter(1)):
#         log.info("processing edge %s", w)
#         edge = w[0]
#         dist = w[1]
#
#         end1 = edge[0]
#         end2 = edge[1]
#         vn = _is_one_vertex_in_graph(g,end1,end2)
#         if vn == end1:
#             vm = end2
#         else:
#             vm = end1
#
#         if vn != None:
#             """
#             One of the two vertices exists in g, so we have to check whether
#             this edge represents a shorter linkage than other existing paths.
#             """
#             if _does_shorter_path_exist_with_vertex(vn, vm, dist, pairwise_dist) == False:
#                 g.add_node(end1)
#                 g.add_node(end2)
#                 g.node[end1]['label'] = id_to_label[end1]
#                 g.node[end2]['label'] = id_to_label[end2]
#                 g.add_edge(end1,end2,cosine_dist=dist,rank=dist_to_rank[str(dist)])
#         elif end1 not in g and end2 not in g:
#             """
#             Neither vertex exists, so we simply create both and add an edge, annotating as we go
#             """
#             g.add_node(end1)
#             g.add_node(end2)
#             g.node[end1]['label'] = id_to_label[end1]
#             g.node[end2]['label'] = id_to_label[end2]
#             g.add_edge(end1,end2,cosine_dist=dist,rank=dist_to_rank[str(dist)])
#         else:
#             pass
#
#     # g should now contain an annotated graph with the minimum required distances to link all vertices
#     return g

def _does_shorter_path_exist_with_vertex(vn,vm,dist,dist_map):
    """
    Given two vertices of an edge (vn, vm), one of which exists in graph g (vn),
    is there an edge in the distance_map that involves vn and another vertex vi
    which is shorter than dist(vn,vm)?

    :param g: NetworkX graph object
    :param vn: edge vertex - that exists in g
    :param vm: edge vertex - that does not exist in g
    :param dist: distance between vn,vm
    :param dist_map: dict with tuples of (id1,id2) as keys, angular distance as values
    :return: boolean
    """
    total = 0
    hits = 0
    for edge,other_dist in dist_map.items():
        total += 1
        if vn in edge:
            log.debug("comparing %s to edge %s - %s vs edge dist: %s",vn,edge,dist,other_dist)
            if float(dist) < float(other_dist):
                log.debug("...could add %s-%s",vn,vm)
                hits += 1
    if hits > 0:
        return True
    else:
        return False







def _is_one_vertex_in_graph(g,v1,v2):
    """
    Given two vertices (ends of an edge), determines whether only one of the vertices is in graph G.
    If so, the vertex in the graph is returned.  If both exist, or if neither exist, None is returned.

    :param v1:
    :param v2:
    :return: v1 or v2, or None
    """
    if v1 in g and v2 not in g:
        return v1
    elif v2 in g and v1 not in g:
        return v2
    else:
        return None




if __name__ == '__main__':
    setup()
    (types, labels, counts, id_to_label, label_to_id, dimension) = parse_inputfile(args.inputfile)
    index = build_index(counts,label_to_id,dimension)

    pairwise_dist = dict()

    pairs = list(itertools.combinations(id_to_label.keys(),2))
    for pair in pairs:
        dist = index.get_distance(pair[0],pair[1])
        pairwise_dist[pair] = dist

    dist_to_rank = dict()
    rank = 1
    for w in sorted(pairwise_dist.items(), key=operator.itemgetter(1)):
        dist_to_rank[str(w[1])] = str(rank)
        log.debug("rank: %s  pair: %s - %s: dist: %s",rank,id_to_label[w[0][0]], id_to_label[w[0][1]], w[1])
        rank += 1

    # annotate an input GML file (minmax for frequency or continuity) and output as a DOT and PNG
    g = read_gml_and_normalize_floats(args.minmaxgml)
    g = annotate_nx_graph_with_distances(g,pairwise_dist,label_to_id)
    save_gml(g,"angulardistance")

    dot_filename = args.outputdirectory + '/' + args.inputfile[0:-4] + "-angular-distance-annotated.dot"
    png_filename = args.outputdirectory + '/' + args.inputfile[0:-4] + "-angular-distance-annotated.png"

    write_ordered_dot(g, dot_filename, dist_to_rank,name=args.inputfile[0:-4])

    cmd = "neato -Tpng "
    cmd += dot_filename
    cmd += " -o "
    cmd += png_filename

    os.system(cmd)

    # use the pure distances and construct a continuity graph with just the distances, for comparison
    g_constructed = build_minimum_angular_distance_graph(pairwise_dist,id_to_label,dist_to_rank)
    save_gml(g_constructed,"constructed-angulardistance")

    dot_filename = args.outputdirectory + '/' + args.inputfile[0:-4] + "-angular-distance-constructed.dot"
    png_filename = args.outputdirectory + '/' + args.inputfile[0:-4] + "-angular-distance-constructed.png"


    write_ordered_dot(g_constructed, dot_filename, dist_to_rank,name=args.inputfile[0:-4])

    cmd = "neato -Tpng "
    cmd += dot_filename
    cmd += " -o "
    cmd += png_filename

    os.system(cmd)