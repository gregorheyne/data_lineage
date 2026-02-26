import yaml
from pathlib import Path

# initialize nodes end edges
nodes = []
edges = []
# and aux dicts
nodes_name_id_map = dict()
nodes_id_meta_map = dict()
edges_id_meta_map = dict()


def clear_network():
    """
    Clears and resets the network by emptying nodes, edges, and all auxiliary maps/dicts.
    """
    nodes.clear()
    edges.clear()
    nodes_name_id_map.clear()
    nodes_id_meta_map.clear()
    edges_id_meta_map.clear()
    return None


def _format_node_name(node_name):
    node_name = node_name.replace('\\', '/')
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
    if not nodes:
        return 'n1'
    else:
        # get all node ids
        node_ids = list(nodes_id_meta_map.keys())
        # strip n and convert to int
        node_ids_int = [int(node_id.replace('n', '')) for node_id in node_ids]
        # max node id
        max_node_id = max(node_ids_int)
        return f'n{max_node_id+1}'

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

def _get_edge_id(src_id, tgt_id):
    return src_id + '_' + tgt_id

def _edge_known(src_id, tgt_id):
    return _get_edge_id(src_id, tgt_id) in edges_id_meta_map

def _add_to_edges_id_meta_map(edge):
    edge_key = _get_edge_id(edge['src_id'], edge['tgt_id'])
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
        assert edges_id_meta_map[_get_edge_id(src_id, tgt_id)]['type'] == edge_type, f'found conflicting edge type for edge {_get_edge_id(src_id, tgt_id)}'
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
        edges_id_meta_map.pop(_get_edge_id(src_id, tgt_id))

    return None

def write_yaml(data, fp):
    with fp.open('w', encoding='utf-8') as f:
        yaml.dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True
        )
    return None

def read_yaml(fp):
    with fp.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_network_to_yaml(dir: Path):
    dir.mkdir(parents=True, exist_ok=True)
    write_yaml(nodes, dir / 'network_nodes.yaml')
    write_yaml(edges, dir / 'network_edges.yaml')
    write_yaml(nodes_name_id_map, dir / 'network_nodes_name_id_map.yaml')
    write_yaml(nodes_id_meta_map, dir / 'network_nodes_id_meta_map.yaml')
    write_yaml(edges_id_meta_map, dir / 'network_edges_id_meta_map.yaml')
    return None

def load_network_from_yaml(dir: Path):
    clear_network()
    nodes.extend(read_yaml(dir / 'network_nodes.yaml'))
    edges.extend(read_yaml(dir / 'network_edges.yaml'))
    nodes_name_id_map.update(read_yaml(dir / 'network_nodes_name_id_map.yaml'))
    nodes_id_meta_map.update(read_yaml(dir / 'network_nodes_id_meta_map.yaml'))
    edges_id_meta_map.update(read_yaml(dir / 'network_edges_id_meta_map.yaml'))
    return None