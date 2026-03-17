import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_app.utils.app_state import load_network, log_page_event, set_page_style, show_page_spinner, hide_page_spinner
from data_lineage.lineage_network.network_filter import get_node_child_counts

_spinner = show_page_spinner()

set_page_style()


PAGE_NAME = "Network Components"
if st.session_state.get('_last_page') != PAGE_NAME:
    log_page_event(PAGE_NAME, "opened_page")
    st.session_state['_last_page'] = PAGE_NAME

network = load_network()
nodes = network['nodes']
edges = network['edges']

id_to_name = {n['id']: n.get('name', n['id']) for n in nodes}
id_to_type = {n['id']: n.get('type', '') for n in nodes}

st.title("Nodes")

child_counts = get_node_child_counts()
nodes_rows = [
    {
        'display_name': n.get('display_name', ''),
        'type': n.get('type', ''),
        'module': n.get('module', ''),
        'count_children': child_counts.get(n['id'], 0),
        'source_type': n.get('source_type', ''),
        'io_context': n.get('io_context', ''),
    }
    for n in nodes
]
nodes_df = pd.DataFrame(nodes_rows)

gb_nodes = GridOptionsBuilder.from_dataframe(nodes_df)
gb_nodes.configure_default_column(filter=True, sortable=True, resizable=True)
gb_nodes.configure_pagination(paginationAutoPageSize=True)
gb_nodes.configure_grid_options(enableCellTextSelection=True)
AgGrid(nodes_df, gridOptions=gb_nodes.build(), fit_columns_on_grid_load=True, height=600)

st.title("Edges")

edges_rows = [
    {
        'src_name': id_to_name.get(e['src_id'], e['src_id']),
        'src_type': id_to_type.get(e['src_id'], ''),
        'edge_type': e.get('type', ''),
        'tgt_name': id_to_name.get(e['tgt_id'], e['tgt_id']),
        'tgt_type': id_to_type.get(e['tgt_id'], '')
    }
    for e in edges
]
edges_df = pd.DataFrame(edges_rows)

gb = GridOptionsBuilder.from_dataframe(edges_df)
gb.configure_default_column(filter=True, sortable=True, resizable=True)
gb.configure_pagination(paginationAutoPageSize=True)
gb.configure_grid_options(enableCellTextSelection=True)
AgGrid(edges_df, gridOptions=gb.build(), fit_columns_on_grid_load=True, height=600)

hide_page_spinner(_spinner)