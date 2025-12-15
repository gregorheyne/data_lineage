import os

# initialize nodes end edges
nodes = []
edges = []
# and aux dicts
nodes_name_id_map = dict()
nodes_id_meta_map = dict()
edges_id_meta_map = dict()


def _format_node_name(node_name):
    return node_name.upper()

def _node_known(node_name):
    return node_name in nodes_name_id_map

def _add_to_node_name_id_map(node):
    nodes_name_id_map[node['name']] = node['id']
    return None

def _add_to_nodes_id_meta_map(node):
    # nodes_id_meta_map[node['id']] = {
    #         'name': node['name'],
    #         'type': node['type']
    #     }
    nodes_id_meta_map[node['id']] = {key: node[key] for key in node.keys() if key != 'id'}
    return None

def _get_new_node_id():
    return f'n{len(nodes)+1}'

def _add_new_node(node_name, node_type, meta_dict):
    node = {
        'id': _get_new_node_id(),
        'name': node_name,
        'type': node_type,
    }
    if meta_dict:
        node = node | meta_dict
    nodes.append(node)
    _add_to_node_name_id_map(node)
    _add_to_nodes_id_meta_map(node)
    return None

def register_node(node_name, node_type, meta_dict=None):
    node_name = _format_node_name(node_name)
    if _node_known(node_name):
        # if node is known check that registered type is the same
        node_id = nodes_name_id_map[node_name]
        assert nodes_id_meta_map[node_id]['type'] == node_type, f'found conflicting node types for node {node_name}'
    else:
        # if not, add it
        _add_new_node(node_name, node_type, meta_dict)
    return None

def _edge_known(src_id, tgt_id):
    return (src_id, tgt_id) in edges_id_meta_map

def _add_to_edges_id_meta_map(edge):
    edge_key = (edge['src_id'], edge['tgt_id'])
    edges_id_meta_map[edge_key] = {
        'type': edge['type']
        }
    return None

def _add_new_edge(src_id, tgt_id, edge_type):
    edge = {
        'src_id': src_id,
        'tgt_id': tgt_id,
        'type': edge_type
    }
    edges.append(edge)
    _add_to_edges_id_meta_map(edge)
    return None

def register_edge(src, tgt, edge_type):
    src = _format_node_name(src)
    tgt = _format_node_name(tgt)
    # we convert edge node name to id here already
    # as first check that the nodes are known
    src_id = nodes_name_id_map[src]
    tgt_id = nodes_name_id_map[tgt]

    if _edge_known(src_id, tgt_id):
        # check if we find the same meta data in the already existing edge
        assert edges_id_meta_map[(src_id, tgt_id)]['type'] == edge_type, f'found conflicting edge type for edge {(src_id, tgt_id)}'
    else:
        _add_new_edge(src_id, tgt_id, edge_type)
    return None

def remove_nodes_from_network(nodes_to_remove: list):
    """
    checks for partial match in the name of the node and removes all that match
    """
    # nodes_to_remove = ['SAMPLE_DATA.CSV']
    ids_to_remove = set()
    for node_to_remove in nodes_to_remove:
        node_to_remove = _format_node_name(node_to_remove)
        ids_to_remove = ids_to_remove.union(set([nodes_name_id_map[node_name] for node_name in nodes_name_id_map.keys() if node_to_remove in node_name]))
    # collect the full node info to remove later
    nodes_full_to_remove = []
    for node in nodes:
        if node['id'] in ids_to_remove:
            if node not in nodes_full_to_remove:
                nodes_full_to_remove.append(node)
    # collect all edges that need to be removed
    edges_full_to_remove = []
    for edge in edges:
        if edge['src_id'] in ids_to_remove:
            if edge not in edges_full_to_remove:
                edges_full_to_remove.append(edge)
            continue
        if edge['tgt_id'] in ids_to_remove:
            if edge not in edges_full_to_remove:
                edges_full_to_remove.append(edge)

    # remove nodes and edges
    for node in nodes_full_to_remove:
        node_id = node['id']
        node_name = node['name']
        # actual removals
        nodes.remove(node)
        nodes_id_meta_map.pop(node_id)
        nodes_name_id_map.pop(node_name)
    for edge in edges_full_to_remove:
        src_id = edge['src_id']
        tgt_id = edge['tgt_id']
        # actual removals
        edges.remove(edge)
        edges_id_meta_map.pop((src_id, tgt_id))

    return None


def add_graphviz_meta_to_io_network():

    # add color, shape, style for nodes
    # add style for edges

    for node in nodes:

        node['tooltip'] = node['name']
        if 'io_context' in node:
            node['layer'] = (node['io_context'].split('io_ctx_id')[0]).lower()[:-1] + ' (' + node['module'] + ')'

        if node['type'] == 'file':
            node['display_name'] = os.path.basename(node['name'])
            node['shape'] = 'folder'
            node['style'] = 'rounded,filled,dashed'
        elif node['type'] == 'py_node':
            node['display_name'] = 'py'
            node['shape'] = 'diamond'
            node['style'] = 'filled'
        elif node['type'] == 'db_object':
            node['display_name'] = node['name']
            node['shape'] = 'box'
            node['style'] = 'rounded,filled'
        else:
            node['display_name'] = node['name']

    for edge in edges:
        src_id = edge['src_id']
        tgt_id = edge['tgt_id']
        # check if we have a file as source or target
        src_type = nodes_id_meta_map[src_id]['type']
        tgt_type = nodes_id_meta_map[tgt_id]['type']
        if ((src_type == 'file') or (tgt_type == 'file')):
            edge['style'] = 'dashed'

    return None

def get_implied_layer_order():
    layers = set()
    layer_order = []
    for node in nodes:
        if node['layer'] not in layers:
            layers.add(node['layer'])
            layer_order.append(node['layer'])
    return layer_order

def set_node_colors():

    colors_repo = [
        "lightblue",
        "lightyellow",
        "lightgreen",
        "orange",
        "plum",
        "lightcoral",
        "lightseagreen",
        "lightsalmon",
        "lightgoldenrod",
        "khaki",
        "orchid",
        "palegreen",
        "paleturquoise",
        "palevioletred",
        "peachpuff",
        "skyblue",
        "thistle",
        "turquoise",
        "wheat",
        "yellowgreen",
        "tomato",
        "mediumaquamarine"
    ]

    layer_color_dict = dict()
    color_id = 0
    for node in nodes:
        node_layer = node['layer']
        if node_layer not in layer_color_dict.keys():
            layer_color_dict[node_layer] = colors_repo[color_id]
            color_id += 1
        node['color'] = layer_color_dict[node_layer]

    return None



# from network_plots.layer_plot import draw_lineage_plot
# draw_lineage_swimlanes_plot(nodes, edges)
