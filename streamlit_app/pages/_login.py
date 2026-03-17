import getpass
import streamlit as st
from streamlit_app.utils.app_state import set_page_style

set_page_style()

st.title("Data Lineage Explorer")
st.subheader("Login")

with st.form("login_form"):
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    if password == "1":
        os_user = getpass.getuser()
        st.session_state['authenticated'] = True
        st.session_state['login_failed'] = False
        st.session_state['user_id'] = os_user
        st.session_state['user_display_name'] = os_user
        st.rerun()
    else:
        st.session_state['login_failed'] = True
        st.rerun()
