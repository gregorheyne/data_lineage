import sys
from pathlib import Path

# Ensure project root is on sys.path so data_lineage package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
import streamlit as st
from data_lineage.lineage_network.network_filter import register_network_as_nx


@st.cache_resource
def load_network():
    yaml_path = Path(__file__).parent / 'example_network.yaml'
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def init_session_state():
    network = load_network()
    if not st.session_state.get('nx_registered'):
        register_network_as_nx(network)
        st.session_state['nx_registered'] = True
    if 'applied_filters' not in st.session_state:
        st.session_state['applied_filters'] = []
