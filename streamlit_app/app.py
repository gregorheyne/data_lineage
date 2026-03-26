# dev run with "streamlit run streamlit_app/app.py"
# prod run with "APP_ENVIRONMENT=prod APP_DB_CONN_DRIVER=pymssql streamlit run streamlit_app/app.py"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # project root for data_lineage
import streamlit as st
from streamlit_app.utils.app_state import init_session_state, show_user_sidebar

st.set_page_config(page_title="Data Lineage Explorer", layout="wide")

if st.session_state.get('login_failed'):
    pg = st.navigation([st.Page("pages/_not_authorized.py", title="Access Denied")])
elif st.session_state.get('authenticated'):
    show_user_sidebar()
    init_session_state()
    pg = st.navigation([
        st.Page("pages/0_home.py", title="Home"),
        st.Page("pages/1_Network_Components.py", title="Network Components"),
        st.Page("pages/2_Network_Filter.py", title="Network Filter"),
        st.Page("pages/3_Network_Plot.py", title="Network Plot"),
    ])
else:
    pg = st.navigation([st.Page("pages/_login.py", title="Login")])

pg.run()
