import streamlit as st
import streamlit.components.v1 as components
from app_state import init_session_state, require_auth, log_page_event

st.set_page_config(page_title="Network Plot", layout="wide")

require_auth()
init_session_state()

PAGE_NAME = "Network Plot"
if st.session_state.get('_last_page') != PAGE_NAME:
    log_page_event(PAGE_NAME, "opened_page")
    st.session_state['_last_page'] = PAGE_NAME

st.title("Network Plot")

if 'plot_html' not in st.session_state:
    st.info("No plot generated yet. Go to the **Filter Network** page to set filters and generate a plot.")
else:
    components.html(st.session_state['plot_html'], height=800, scrolling=True)
