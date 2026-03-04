import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # project root for data_lineage

import streamlit as st
from streamlit_app.utils.app_state import init_session_state, require_auth, log_page_event, set_page_style

st.set_page_config(page_title="Data Lineage Explorer", layout="wide")

require_auth()
init_session_state()
set_page_style()

PAGE_NAME = "Home"
if st.session_state.get('_last_page') != PAGE_NAME:
    log_page_event(PAGE_NAME, "opened_page")
    st.session_state['_last_page'] = PAGE_NAME

st.title("Data Lineage Explorer")
st.markdown("""
Welcome to the **Data Lineage Explorer** — a tool for browsing and visualising data lineage networks.

---

### Scope

""")

import pandas as pd

scope_data = pd.DataFrame([
    {"Module": "Sales", "As of": "2024-01-15", "Comment": "Initial load from CRM", "Source": "Salesforce"},
    {"Module": "Finance", "As of": "2024-02-01", "Comment": "Quarterly reconciliation", "Source": "SAP"},
    {"Module": "HR", "As of": "2024-03-10", "Comment": "Annual headcount update", "Source": "Workday"},
])
st.dataframe(scope_data, use_container_width=True, hide_index=True)

st.markdown("""


---

### Pages

- **Network Components** — Browse all network nodes and edges in sortable and filterable tables.
- **Network Plot** — Filter the network by node attributes and render an interactive lineage plot.

---

### How to use the Filter Network page

1. Select a **node attribute** (`module`, `display_name`, `origin`, `pbi_name`) from the dropdown.
2. Select one or more **attribute values** to seed the filter.
3. Click **Add nodes to filter** — repeat steps 1–3 to accumulate multiple filter conditions.
4. Optionally set **descendant** and/or **ancestor** expansion levels to include neighbouring nodes.
5. Click **Generate plot** to render the filtered subgraph.
6. Use **Clear filters** to reset and start over.

The rendered plot is displayed on the **Network Plot** page.
""")
