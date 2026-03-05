import os
import re
from graphviz import Digraph
from collections import defaultdict
from pathlib import Path


def add_graphviz_meta_to_io_network(network):

    # add color, shape, style for nodes
    # add style for edges

    # keep track of node type
    node_types = dict()

    for node in network['nodes']:

        node['tooltip'] = node['name']

        # set layer
        assert node['source_type'] in ['io_logs_py', 'PBI', 'db_views_definitions', 'sql_script'], 'node with invalid node source_type'
        if node['source_type'] == 'io_logs_py':
            if 'io_context' in node:
                node['layer'] = (node['io_context'].split('io_ctx_id')[0]).lower()[:-1] + ' (' + node['module'] + ')'
        elif node['source_type'] == 'PBI':
            node['layer'] = f"PBI ({node['pbi_name']})"
        elif node['source_type'] in ['db_views_definitions', 'sql_script']:
            node['layer'] = f"schema_({node['module']})"

        # set display name, shape and style
        node_type = node['type']
        node_types[node['id']] = node_type

        if node_type == 'file':
            node['display_name'] = os.path.basename(node['name'])
            node['shape'] = 'folder'
            node['style'] = 'rounded,filled,dashed'
        elif node_type == 'py_node':
            node['display_name'] = 'py'
            node['shape'] = 'diamond'
            node['style'] = 'filled'
        elif node_type == 'db_object':
            node['display_name'] = node['name']
            node['shape'] = 'box'
            node['style'] = 'rounded,filled'
        elif node_type == 'pbi':
            node['display_name'] = node['name']
            node['shape'] = 'doubleoctagon'
            node['style'] = 'filled'
        else:
            node['display_name'] = node['name']

    for edge in network['edges']:
        src_id = edge['src_id']
        tgt_id = edge['tgt_id']
        # check if we have a file as source or target
        src_type = node_types[src_id]
        tgt_type = node_types[tgt_id]
        if ((src_type == 'file') or (tgt_type == 'file')):
            edge['style'] = 'dashed'

    return None

def get_implied_layer_order(network):
    layers = set()
    layer_order = []
    for node in network['nodes']:
        if node['layer'] not in layers:
            layers.add(node['layer'])
            layer_order.append(node['layer'])
    return layer_order

def set_node_colors(network):

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
        "mediumaquamarine",
        "lightpink",
        "lavender",
        "lightcyan"
    ]

    layer_color_dict = dict()
    color_id = 0
    for node in network['nodes']:
        node_layer = node['layer']
        if node_layer not in layer_color_dict.keys():
            layer_color_dict[node_layer] = colors_repo[color_id % len(colors_repo)]
            color_id += 1
        node['color'] = layer_color_dict[node_layer]

    return None

def attributes_to_upper_case(network, attributes):
    
    # attributes = ['name', 'module', 'schema', 'display_name']

    for node in network['nodes']:
        for attribute in attributes:
            if attribute in node:
                node[attribute] = node[attribute].upper()
    return None


def draw_lineage_plot(
        network,
        layer_order=None,
        fp_output: str=None,
        fn_output: str='lineage_plot',
        interactivity=True):

    nodes = network['nodes']
    edges = network['edges']

    # check consistency
    node_ids = set([node['id'] for node in nodes])
    edge_ids = set([edge['src_id'] for edge in edges]).union(set([edge['tgt_id'] for edge in edges]))
    assert edge_ids.difference(node_ids) == set(),  "edges with nodes not in nodes not aligned."

    # set some layer and layer order in case layers or layer_order are not given
    if not layer_order:
        print('set layer order')
        layer_order = ['default_io_layer']
        for node in nodes:
            if 'layer' not in node.keys():
                node['layer'] = 'default_io_layer'
            else:
                layer_order.append(node['layer'])
        layer_order = list(set(layer_order))

    # build node_meta from nodes list
    node_meta = dict()
    for node in nodes:
        node_meta[node['id']] = {key: node[key] for key in node.keys()}

    def get_node_name(node: dict) -> str:
        return node.get('name', node['id'])
    
    def get_node_type(node: dict) -> str:
        return node.get('type', 'no type')
    
    def get_node_display_name(node: dict) -> str:
        return node.get('display_name', get_node_name(node))
    
    def get_node_layer(node: dict) -> str:
        return node.get('layer', 'default_io_layer')
    
    def get_node_color(node: dict) -> str:
        return node.get('color', 'lightgray')
    
    def get_node_style(node: dict) -> str:
        return node.get('style', 'rounded,filled')

    def get_node_shape(node: dict) -> str:
        return node.get('shape', 'box')

    def get_node_tooltip(node: dict) -> str:
        default_tooltip = f"Name: {get_node_name(node)}\\nLayer: {get_node_layer(node)}\\nType: {get_node_type(node)}"
        return node.get('tooltip', default_tooltip)

    def get_node_url(node: dict) -> str:
        assert 1==2, "Please implement your own URL logic here."
        # Base URL for clickable links
        BASE_TABLE_URL = "https://example.com/tables/{}"
        return BASE_TABLE_URL.format(get_node_name(node))

    def get_edge_style(edge: dict) -> str:
        return edge.get('style', 'solid')

    # ---------- Group nodes by layer ----------
    # get nodes by layer
    node_ids_by_layer = defaultdict(list)
    for node in nodes:
        node_ids_by_layer[get_node_layer(node)].append(node['id'])
    for layer in node_ids_by_layer:
        node_ids_by_layer[layer] = sorted(node_ids_by_layer[layer])

    # ---------- Graphviz with swimlanes & styles ----------
    if not fp_output:
        dot_name = fn_output
    else:
        dot_name = Path(fp_output) / fn_output
    dot = Digraph("Layered_Lineage", filename=dot_name, format="svg")
    dot.graph_attr.update(
        style='solid',
        margin='4.0',       # padding inside the border
        ratio='expand',     # Center inside expanded viewBox
        size="",            # disables width/height
        dpi="72"            # making units equal to px
    )

    # graph features
    dot.attr(rankdir="LR", fontsize="12")
    dot.attr('graph', splines='ortho')

    # Layer rendering order
    for layer in layer_order:
        node_ids = node_ids_by_layer.get(layer, [])
        if not node_ids:
            continue

        with dot.subgraph(name=f"cluster_{layer}") as sub:
            sub.attr(label=layer, style="filled", color="transparent" if layer=="default_io_layer" else "lightgray", fontsize="14")

            for node_id in node_ids:
                node = node_meta[node_id]

                if interactivity:
                    sub.node(node_id,
                            label=get_node_display_name(node),
                            shape=get_node_shape(node),
                            style=get_node_style(node),
                            fillcolor=get_node_color(node),
                            tooltip=get_node_tooltip(node)
                            #  URL=get_node_url(node)
                            )
                else:
                    sub.node(node_id,
                        label=get_node_display_name(node),
                        shape=get_node_shape(node),
                        style=get_node_style(node),
                        fillcolor=get_node_color(node)
                        )


    # ---------- Add edges with dashed styling if file involved ----------
    for edge in edges:
        src_id = edge['src_id']
        tgt_id = edge['tgt_id']

        # If either node is a file → dashed edge
        edge_style = get_edge_style(edge)

        dot.edge(src_id, tgt_id, style=edge_style)

    # ---------- Legend ----------
    with dot.subgraph(name="cluster_legend") as legend:
        legend.attr(label="Legend", fontsize="14", style="rounded", color="black", rank='sink')

        legend.node("file", label="File", shape="folder", style="filled,dashed", fillcolor="lightgray")
        legend.node("db_object_1", label="DB Table/View 1", shape="box", style="filled", fillcolor="lightgray")
        legend.node("db", label="DB", shape="cylinder", style="filled", fillcolor="lightgray")
        legend.node("py_proc", label="python", shape="diamond", style="filled", fillcolor="lightgray")
        legend.node("db_object_2", label="DB Table/View 2", shape="box", style="filled", fillcolor="lightgray")
        legend.node("pbi", label="PBI", shape="doubleoctagon", style="filled", fillcolor="lightgray")

        legend.edge("file", "py_proc", label="", style='dashed')
        legend.edge("py_proc", "db_object_1", label="", style='solid')
        legend.edge("db", "py_proc", label="", style='solid')
        legend.edge("db_object_1", "db_object_2", label="", style='solid')
        legend.edge("db_object_2", "pbi", label="", style='solid')
        
    if fp_output:
        dot.render(cleanup=True)

    return dot.pipe(format='svg')

def clean_graphviz_svg(svg_bytes, remove_interactive=False):
    """
    - removes some stuff coming from graphviz that interferes with displaying in pbi or even the browser
    - if remove_interactive=True: strips all tooltips and interactive attributes for fully static SVG
    """
    
    svg = svg_bytes.decode("utf-8")

    # Remove XML header or doctype if present
    svg = re.sub(r'<\?xml.*?\?>', '', svg, flags=re.DOTALL)
    svg = re.sub(r'<!DOCTYPE.*?>', '', svg, flags=re.DOTALL)

    # Remove comments: <!-- ... -->
    svg = re.sub(r'<!--.*?-->', '', svg, flags=re.DOTALL)

    # Fix width/height units (pt → nothing)
    svg = re.sub(r'width="([0-9.]+)pt"', r'width="\1"', svg)
    svg = re.sub(r'height="([0-9.]+)pt"', r'height="\1"', svg)

    if remove_interactive:
        # Remove all <title> elements (which create tooltips in SVG)
        svg = re.sub(r'<title>.*?</title>', '', svg, flags=re.DOTALL)
        
        # Remove onclick attributes
        svg = re.sub(r'\s*onclick="[^"]*"', '', svg)
        
        # Remove cursor pointers
        svg = re.sub(r'\s*style="cursor:[^"]*"', '', svg)

    # (Optional) Normalize whitespace
    svg = svg.strip()

    return svg


# <svg viewBox="...">
#   <rect x="0" y="0" width="100%" height="100%" fill="white" stroke="black" />
#   <!-- Graphviz-generated content -->
# </svg>


svg_wrapper_template = """<!DOCTYPE html>
<html>
<head>
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  svg {
    width: 100% !important;
    height: 100% !important;
    display: block;
  }
</style>
</head>
<body>

<!--
<svg viewBox="0 0 300 150" style="width:100%; height:100%; border:1px solid black">
  <circle cx="50" cy="75" r="30" fill="lightblue" stroke="black" />
  <circle cx="200" cy="75" r="30" fill="lightgreen" stroke="black" />
  <line x1="80" y1="75" x2="170" y2="75" stroke="black"/>
</svg>
-->

svg_placeholder

<script>
(function() {
    try {
        const offset = 160;
        const parentHeight = window.parent.innerHeight;
        const iframes = window.parent.document.querySelectorAll('iframe');
        for (const iframe of iframes) {
            if (iframe.contentWindow === window) {
                iframe.style.height = Math.max(parentHeight - offset, 400) + 'px';
                iframe.style.width = '100%';
                break;
            }
        }
    } catch(e) {}
})();</script>

<script>
(function() {
    const svg = document.querySelector("svg");
    let isPanning = false;
    let startX, startY;
    let viewBox = svg.getAttribute("viewBox").split(" ").map(Number);

    svg.addEventListener("mousedown", e => {
        isPanning = true;
        startX = e.clientX;
        startY = e.clientY;
    });

    svg.addEventListener("mousemove", e => {
        if (!isPanning) return;
        const dx = startX - e.clientX;
        const dy = startY - e.clientY;
        viewBox[0] += dx;
        viewBox[1] += dy;
        svg.setAttribute("viewBox", viewBox.join(" "));
        startX = e.clientX;
        startY = e.clientY;
    });

    svg.addEventListener("mouseup", () => isPanning = false);
    svg.addEventListener("mouseleave", () => isPanning = false);

    svg.addEventListener("wheel", e => {
        e.preventDefault();
        const scale = 1.1;
        const zoomFactor = e.deltaY < 0 ? 1/scale : scale;
        viewBox[2] *= zoomFactor;
        viewBox[3] *= zoomFactor;
        svg.setAttribute("viewBox", viewBox.join(" "));
    });
})();
</script>

</body>
</html>
"""


def wrap_svg_in_html(svg: str):
    """
    - adds panning (and zooming functionality)
    """

    # # read the svg_wrapper_template.html file
    # with open('svg_wrapper_template.html', 'r', encoding='utf-8') as f:
    #     svg_wrapper_template = f.read()
    # replcae the placeholder with cleaned_svg
    final_html = svg_wrapper_template.replace('svg_placeholder', svg)
    # write to svg_wrapper_output.html
    # with open('lineage_plot.html', 'w', encoding='utf-8') as f:
    #     f.write(final_html)
    return final_html

