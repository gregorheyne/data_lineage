import streamlit as st
from network_state import init_session_state

st.set_page_config(page_title="Data Lineage Explorer", layout="wide")

init_session_state()

st.title("Data Lineage Explorer")
st.markdown("""
Welcome to the **Data Lineage Explorer** — a tool for browsing and visualising data lineage networks.

---

### Pages

- **Edges Table** — Browse all network edges and nodes in a sortable, filterable table.
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
