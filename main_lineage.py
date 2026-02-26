# below is about reading
# in io logs and converting them to a
# network and printing them to svg
import os
import yaml
from pathlib import Path
import pandas as pd
from data_lineage.lineage_parsers.pbip_tmdl_parser import get_pbip_sources
from data_lineage.lineage_network.network_populate import process_io_logs_df
from data_lineage.lineage_network.network_populate import add_io_logs_to_network
from data_lineage.lineage_network.network_populate import add_pbip_sources_to_network
from data_lineage.lineage_network.network_base import remove_nodes_from_network
from data_lineage.lineage_network.network_base import nodes, edges
from data_lineage.lineage_network.network_base import nodes_id_meta_map, edges_id_meta_map, nodes_name_id_map
from data_lineage.lineage_network.network_plot import add_graphviz_meta_to_io_network
from data_lineage.lineage_network.network_plot import get_implied_layer_order
from data_lineage.lineage_network.network_plot import set_node_colors
from data_lineage.lineage_network.network_plot import draw_lineage_plot
from data_lineage.lineage_network.network_plot import clean_graphviz_svg
from data_lineage.lineage_network.network_plot import wrap_svg_in_html


df_io_logs = pd.read_csv('data/io_logs.csv', sep=';')
str_required_in_caller_one_file = os.getcwd()
df_io_logs = process_io_logs_df(df_io_logs, str_required_in_caller_one_file=str_required_in_caller_one_file)
add_io_logs_to_network(df_io_logs)


paths_to_pbips = [
    Path(os.getcwd()) / 'tests/pbip/pseudo_pbip.pbip'
]
path_to_pbip_file = paths_to_pbips[0]
pbip_sources = get_pbip_sources(paths_to_pbips[0])
# some hack for testing
for i, pbip_source in enumerate(pbip_sources):
    if pbip_source == {'type': 'db_object', 'name': 'sqllite_schema.Random_data_secondary'}:
        pbip_sources[i] = {'type': 'db_object', 'name': 'Random_data_secondary'}
add_pbip_sources_to_network(paths_to_pbips[0], pbip_sources)

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


write_yaml(nodes, Path('data/network_nodes.yaml'))
write_yaml(edges, Path('data/network_edges.yaml'))
write_yaml(nodes_name_id_map, Path('data/network_nodes_name_id_map.yaml'))
write_yaml(nodes_id_meta_map, Path('data/network_nodes_id_meta_map.yaml'))
write_yaml(edges_id_meta_map, Path('data/network_edges_id_meta_map.yaml'))


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


