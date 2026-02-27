# reading in io logs and pbi sources and add them to the network
import os
from pathlib import Path
import pandas as pd
from data_lineage.lineage_parsers.pbip_tmdl_parser import get_pbip_sources
from data_lineage.lineage_network.network_populate import process_io_logs_df
from data_lineage.lineage_network.network_populate import add_io_logs_to_network
from data_lineage.lineage_network.network_populate import add_pbip_sources_to_network
from data_lineage.lineage_network.network_base import remove_nodes_from_network
from data_lineage.lineage_network.network_base import save_network_to_yaml


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

remove_nodes_from_network(['SamPle_data.CSV'])

save_network_to_yaml(Path('data/'))
