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

    if int(args.debug) == 1:
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
            print "error finding distance for edge between %s and %s" % (assem1, assem2)
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

    log.debug("root: %s", root)

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

    log.debug("Plot title: %s", name)

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

        #print "str_nodedata: %s" % str_nodedata
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





if __name__ == '__main__':
    setup()
    (types, labels, counts, id_to_label, label_to_id, dimension) = parse_inputfile(args.inputfile)
    index = build_index(counts,label_to_id,dimension)

    pairwise_dist = dict()

    pairs = list(itertools.combinations(id_to_label.keys(),2))
    for pair in pairs:
        dist = index.get_distance(pair[0],pair[1])
        #print "%s-%s: %s" % (pair[0],pair[1],dist)
        pairwise_dist[pair] = dist

#
    dist_to_rank = dict()
    rank = 1
    for w in sorted(pairwise_dist.items(), key=operator.itemgetter(1)):
        dist_to_rank[str(w[1])] = str(rank)
        print "rank: %s  pair: %s - %s: dist: %s" % (rank,id_to_label[w[0][0]], id_to_label[w[0][1]], w[1])
        rank += 1


    g = read_gml_and_normalize_floats(args.minmaxgml)

    g = annotate_nx_graph_with_distances(g,pairwise_dist,label_to_id)
    save_gml(g,"cosineweight")

    dot_filename = args.outputdirectory + '/' + args.inputfile[0:-4] + "-minmax-cosine-distance.dot"
    png_filename = args.outputdirectory + '/' + args.inputfile[0:-4] + "-minmax-cosine-distance.png"


    write_ordered_dot(g, dot_filename, dist_to_rank,name=args.inputfile[0:-4])

    cmd = "neato -Tpng "
    cmd += dot_filename
    cmd += " -o "
    cmd += png_filename

    os.system(cmd)

