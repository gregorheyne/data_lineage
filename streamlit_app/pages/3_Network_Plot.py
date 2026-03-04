import streamlit as st
import streamlit.components.v1 as components
from streamlit_app.utils.app_state import init_session_state, require_auth, log_page_event, set_page_style, show_page_spinner, hide_page_spinner

_spinner = show_page_spinner()


require_auth()
init_session_state()
set_page_style()

PAGE_NAME = "Network Plot"
if st.session_state.get('_last_page') != PAGE_NAME:
    log_page_event(PAGE_NAME, "opened_page")
    st.session_state['_last_page'] = PAGE_NAME

st.title("Network Plot")

if 'plot_html' not in st.session_state:
    st.info("No plot generated yet. Go to the **Filter Network** page to set filters and generate a plot.")
else:
    components.html(st.session_state['plot_html'], height=1200, scrolling=False)

hide_page_spinner(_spinner)