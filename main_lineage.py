import os
os.environ["IO_HOOKS_MAIN_NAME"] = "test_module"  # used by the hook to replace the <module> function name
import data_lineage.runtime_hooks.io_hooks_py as io_hooks_py
from pathlib import Path
from tests.io_tests_primary import run_primary_tests
from tests.io_tests_secondary import run_secondary_tests

# three lines as the could be in normal code where io hooks should be used
run_primary_tests()
run_secondary_tests()
io_hooks_py.write_io_logs_to_csv()

# below is about reading
# in io logs and converting them to a
# network and printing them to svg
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


df_io_logs = pd.read_csv('io_logs.csv', sep=';')
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

# TODO:

# # copy to clipboard
# import pyperclip
# pyperclip.copy(cleaned_svg)


# print(cleaned_svg)
# cleaned_svg = "".join(cleaned_svg.splitlines())
# cleaned_svg = cleaned_svg.replace("&#45;", "-")


# # convert to base64
# uri = "data:image/svg+xml;base64," + base64.b64encode(cleaned_svg.encode()).decode()
# print(len(uri), uri.count("\n"))


