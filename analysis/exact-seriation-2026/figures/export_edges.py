# python 2.7: export minmax graph edges and nodes from IDSS gml files to JSON
import sys, json, networkx as nx
out = {}
for tag, fn in zip(sys.argv[2::2], sys.argv[3::2]):
    g = nx.read_gml(fn)
    lab = nx.get_node_attributes(g, 'label')
    nm = lambda n: str(lab.get(n, n))
    out[tag] = {"nodes": sorted(nm(n) for n in g.nodes()), "edges": sorted([sorted([nm(a), nm(b)]) for a, b in g.edges()])}
json.dump(out, open(sys.argv[1], "w"), indent=1)
