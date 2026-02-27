from pathlib import Path
from data_lineage.lineage_network.network_base import get_network_copy
from data_lineage.lineage_network.network_base import load_network_from_yaml
from data_lineage.lineage_network.network_plot import add_graphviz_meta_to_io_network
from data_lineage.lineage_network.network_plot import get_implied_layer_order
from data_lineage.lineage_network.network_plot import set_node_colors
from data_lineage.lineage_network.network_plot import draw_lineage_plot
from data_lineage.lineage_network.network_plot import clean_graphviz_svg
from data_lineage.lineage_network.network_plot import wrap_svg_in_html

load_network_from_yaml(Path('data/'))

network = get_network_copy()

# TODO:
# - build a function that given a network object and a start node filters the network to ancestors and descendants of this node
# - build a streamlit app that:
#   - consumes the original network object
#   - displays the a filterable table which displays edges, i.e. source, target, source and target type, edge type
#   - has a plotting function which plots the network using the draw lineage plot function 
#     - specify further, e.g. allows selection of nodes that serve as origin for the filtering function


# prepare for plotting
add_graphviz_meta_to_io_network(network)
layer_order = get_implied_layer_order(network)
set_node_colors(network)

# draw the plots
dir_data = Path('data/')
svg_bytes = draw_lineage_plot(network, layer_order=layer_order, fp_output=dir_data)
cleaned_svg = clean_graphviz_svg(svg_bytes)
lineage_html = wrap_svg_in_html(cleaned_svg)
# print(lineage_html)
with open(dir_data / 'lineage_plot.html', 'w', encoding='utf-8') as f:
    f.write(lineage_html)




# # copy to clipboard
# import pyperclip
# pyperclip.copy(cleaned_svg)


# print(cleaned_svg)
# cleaned_svg = "".join(cleaned_svg.splitlines())
# cleaned_svg = cleaned_svg.replace("&#45;", "-")


# # convert to base64
# uri = "data:image/svg+xml;base64," + base64.b64encode(cleaned_svg.encode()).decode()
# print(len(uri), uri.count("\n"))


