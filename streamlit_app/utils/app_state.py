import hashlib
import getpass
import uuid
from pathlib import Path

import yaml
import streamlit as st
from data_lineage.lineage_network.network_filter import register_network_as_nx
from streamlit_app.utils.event_tracker import log_event


@st.cache_resource
def load_network():
    yaml_path = Path(__file__).parent / 'lineage_network.yaml'
    # print(yaml_path)
    with open(yaml_path) as f:
        return yaml.safe_load(f)


@st.cache_resource
def load_credentials():
    creds_path = Path(__file__).parent / 'credentials.yaml'
    # print(creds_path)
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
    return None

def init_session_state():
    network = load_network()
    if not st.session_state.get('nx_registered'):
        register_network_as_nx(network)
        st.session_state['nx_registered'] = True
    if 'applied_filters' not in st.session_state:
        st.session_state['applied_filters'] = []
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())
    return None

def set_page_style():
    # - this here is tailor made for version 1.52.2
    # - i.e. it might change/break if a different version is used
    st.markdown(
        "<style>div[data-testid='stMainBlockContainer'] { padding-top: 1rem !important; }</style>",
        unsafe_allow_html=True,
    )
    return None

def log_page_event(page_name: str, event_type: str, metadata: dict = None):
    log_event(
        st.session_state['session_id'],
        st.session_state['username'],
        page_name,
        event_type,
        metadata,
    )
    return None