# dev run with "streamlit run streamlit_app/app.py"
# prod run with "APP_ENVIRONMENT=prod streamlit run streamlit_app/app.py"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # project root for data_lineage
import streamlit as st

st.set_page_config(page_title="Data Lineage Explorer", layout="wide")

pg = st.navigation([
    st.Page("pages/0_home.py", title="Home"),
    st.Page("pages/1_Network_Components.py", title="Network Components"),
    st.Page("pages/2_Network_Filter.py", title="Network Filter"),
    st.Page("pages/3_Network_Plot.py", title="Network Plot"),
])
pg.run()
