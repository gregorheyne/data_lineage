from pathlib import Path
from data_lineage.lineage_network.network_base import remove_nodes_from_network
from data_lineage.lineage_network.network_base import nodes, edges
from data_lineage.lineage_network.network_base import load_network_from_yaml
from data_lineage.lineage_network.network_plot import add_graphviz_meta_to_io_network
from data_lineage.lineage_network.network_plot import get_implied_layer_order
from data_lineage.lineage_network.network_plot import set_node_colors
from data_lineage.lineage_network.network_plot import draw_lineage_plot
from data_lineage.lineage_network.network_plot import clean_graphviz_svg
from data_lineage.lineage_network.network_plot import wrap_svg_in_html

load_network_from_yaml(Path('data/'))


# prepare for plotting
remove_nodes_from_network(['SamPle_data.CSV'])
add_graphviz_meta_to_io_network()
layer_order = get_implied_layer_order()
set_node_colors()

# draw the plots
svg_bytes = draw_lineage_plot(nodes, edges, layer_order=layer_order)
cleaned_svg = clean_graphviz_svg(svg_bytes)
lineage_html = wrap_svg_in_html(cleaned_svg)
# print(lineage_html)
with open('lineage_plot.html', 'w', encoding='utf-8') as f:
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


