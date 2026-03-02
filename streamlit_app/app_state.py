import sys
import hashlib
import getpass
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


@st.cache_resource
def load_credentials():
    creds_path = Path(__file__).parent / 'credentials.yaml'
    with open(creds_path) as f:
        return yaml.safe_load(f)


def require_auth():
    """Authenticate via OS login name. Stops execution if user is not in the allowlist."""
    if not st.session_state.get('authenticated'):
        os_user = getpass.getuser()
        user_hash = hashlib.sha256(os_user.encode()).hexdigest()
        credentials = load_credentials()
        user = credentials.get('users', {}).get(user_hash)
        if user:
            st.session_state['authenticated'] = True
            st.session_state['username'] = os_user
            st.session_state['user_display_name'] = user['display_name']
        else:
            st.error(f"Access denied. OS user `{os_user}` is not in the allowlist.")
            st.stop()

    with st.sidebar:
        st.markdown(f"Logged in as **{st.session_state['user_display_name']}**")


def init_session_state():
    network = load_network()
    if not st.session_state.get('nx_registered'):
        register_network_as_nx(network)
        st.session_state['nx_registered'] = True
    if 'applied_filters' not in st.session_state:
        st.session_state['applied_filters'] = []
