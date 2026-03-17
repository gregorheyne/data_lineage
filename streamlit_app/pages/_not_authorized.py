import streamlit as st
from streamlit_app.utils.app_state import set_page_style

set_page_style()

st.title("Access Denied")
st.subheader("You are not authorized to access this page")
