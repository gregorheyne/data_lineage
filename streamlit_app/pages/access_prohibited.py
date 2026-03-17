import streamlit as st
from streamlit_app.utils.app_state import set_page_style

set_page_style()

st.title("Access Prohibited")
st.error("Incorrect password. You do not have access to this application.")

if st.button("Try again"):
    st.session_state['login_failed'] = False
    st.rerun()
