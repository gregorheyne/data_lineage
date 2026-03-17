import uuid
from pathlib import Path

import yaml
import streamlit as st
from data_lineage.lineage_network.network_filter import register_network_as_nx
from streamlit_app.utils.event_tracker import log_event


@st.cache_resource
def load_network():
    yaml_path = Path(__file__).parent.parent / 'data' / 'lineage_network.yaml'
    # print(yaml_path)
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def show_user_sidebar():
    with st.sidebar:
        st.markdown(f"Logged in as **{st.session_state['user_display_name']}**")
    return None

def init_session_state():
    network = load_network()
    if not st.session_state.get('nx_registered'):
        register_network_as_nx(network)
        st.session_state['nx_registered'] = True
    if 'applied_filters' not in st.session_state:
        st.session_state['applied_filters'] = {}
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

def show_page_spinner():
    placeholder = st.empty()
    placeholder.markdown(
        "<div style='display:flex;justify-content:center;align-items:center;height:80vh'>"
        "<div style='width:48px;height:48px;border:5px solid #e0e0e0;"
        "border-top-color:#555555;border-radius:50%;"
        "animation:_spin 0.8s linear infinite'></div>"
        "<style>@keyframes _spin{to{transform:rotate(360deg)}}</style>"
        "</div>",
        unsafe_allow_html=True,
    )
    return placeholder

def hide_page_spinner(placeholder):
    placeholder.empty()

def log_page_event(page_name: str, event_type: str, metadata: dict = None):
    log_event(
        st.session_state['session_id'],
        st.session_state['username'],
        page_name,
        event_type,
        metadata,
    )
    return None