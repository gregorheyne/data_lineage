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
from data_lineage.lineage_network.network_base import save_network_to_yaml, load_network_from_yaml
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

save_network_to_yaml(Path('data/'))
