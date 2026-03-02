import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))   # streamlit_app/ for network_state

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from app_state import load_network, init_session_state, require_auth

st.set_page_config(page_title="Edges Table", layout="wide")

require_auth()
init_session_state()

network = load_network()
nodes = network['nodes']
edges = network['edges']

id_to_name = {n['id']: n.get('name', n['id']) for n in nodes}
id_to_type = {n['id']: n.get('type', '') for n in nodes}

st.title("Network Edges")

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
gb.configure_grid_options(domLayout='autoHeight')
AgGrid(edges_df, gridOptions=gb.build(), fit_columns_on_grid_load=True)
