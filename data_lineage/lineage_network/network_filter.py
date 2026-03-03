import networkx as nx

G = nx.DiGraph()

filtered_nodes = set()

def clear_nx_graph():
    G.clear()
    filtered_nodes.clear()
    return None

def register_network_as_nx(network):

    clear_nx_graph()

    # add nodes
    for node in network['nodes']:
        node_id = node["id"]
        attrs = {k: v for k, v in node.items() if k != "id"}
        G.add_node(node_id, **attrs)

    # add edges
    for edge in network['edges']:
        source = edge["src_id"]
        target = edge["tgt_id"]
        attrs = {k: v for k, v in edge.items() if k not in ["src_id", "tgt_id"]}
        G.add_edge(source, target, **attrs)

    return None

def get_network_from_nx(nx_graph=None):

    if not nx_graph:
        nx_graph = G

    nodes = []
    for nx_node in nx_graph.nodes(data=True):
        node = {'id': nx_node[0]}
        node = node | nx_node[1]
        nodes.append(node)
    edges = []
    for nx_edge in nx_graph.edges(data=True):
        edge = {
            'src_id': nx_edge[0],
            'tgt_id': nx_edge[1]
        }
        edge = edge | nx_edge[2]
        edges.append(edge)

    network = dict()
    network['nodes'] = nodes
    network['edges'] = edges

    return network

def max_path_length(G):
    max_len = 0
    for source in G.nodes():
        # BFS shortest paths = longest reachable in DAG context
        lengths = nx.single_source_shortest_path_length(G, source)
        max_len = max(max_len, max(lengths.values(), default=0))
    return max_len

def descendants_up_to(G, source, n):
    lengths = nx.single_source_shortest_path_length(G, source, cutoff=n)
    return {node for node, dist in lengths.items() if 0 < dist <= n}

def ancestors_up_to(G, source, n):
    # Reverse graph view (no copy)
    G_rev = G.reverse(copy=False)
    lengths = nx.single_source_shortest_path_length(G_rev, source, cutoff=n)
    return {node for node, dist in lengths.items() if 0 < dist <= n}

def get_node_child_counts(nx_graph=None) -> dict:
    """Return a dict mapping node_id -> number of direct successors (children)."""
    if nx_graph is None:
        nx_graph = G
    return {node: len(list(nx_graph.successors(node))) for node in nx_graph.nodes()}

def add_nodes_to_nx_filter(attribute: str, values: list):
    # attribute = 'module'
    # values = ['test_module']
    filtered_nodes_tmp = [
        n for n, data in G.nodes(data=True)
        if data.get(attribute) in values
    ]
    for node in filtered_nodes_tmp:
        filtered_nodes.add(node)
    return None

def get_filtered_network(descendant_level=None, ancestor_level=None):

    # descendant_level = 1
    # ancestor_level = 'max'

    descendants = set()
    ancestors = set()
    if descendant_level:
        if type(descendant_level) == int:
            descendants = set().union(*(descendants_up_to(G, node, descendant_level) for node in filtered_nodes))
        elif descendant_level == 'max':
            descendants = set().union(*(nx.descendants(G, node) for node in filtered_nodes))
    if ancestor_level:
        if type(ancestor_level) == int:
            ancestors = set().union(*(ancestors_up_to(G, node, ancestor_level) for node in filtered_nodes))
        elif ancestor_level == 'max':
            ancestors = set().union(*(nx.ancestors(G, node) for node in filtered_nodes))

    # combine all relevant nodes
    subgraph_nodes = filtered_nodes.union(descendants).union(ancestors)
    
    # build subgraph
    subG = G.subgraph(subgraph_nodes).copy()

    network = get_network_from_nx(subG)

    return network





######### Tests
# add_filter_on_attribute('name', 'RANDOM_DATA_SECONDARY')


# # descendants_test = descendants_up_to(G, 'n4', 6)
# descendants_test = descendants_up_to(G, 'n3', 6)
# for node, attrs in G.nodes(data=True):
#     if node in descendants_test:
#         print(node, attrs)
# ancestors_test = ancestors_up_to(G, 'n3', 6)
# for node, attrs in G.nodes(data=True):
#     if node in ancestors_test:
#         print(node, attrs)



# for node, attrs in G.nodes(data=True):
#     print(node, attrs)
# for u, v, attrs in G.edges(data=True):
#     print(u, v, attrs)

