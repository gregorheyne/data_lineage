import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))   # streamlit_app/ for network_state

import streamlit as st
import streamlit.components.v1 as components
from network_state import init_session_state

st.set_page_config(page_title="Network Plot", layout="wide")

init_session_state()

st.title("Network Plot")

if 'plot_html' not in st.session_state:
    st.info("No plot generated yet. Go to the **Filter Network** page to set filters and generate a plot.")
else:
    components.html(st.session_state['plot_html'], height=800, scrolling=True)
