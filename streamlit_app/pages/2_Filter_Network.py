import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))   # streamlit_app/ for network_state

import streamlit as st
import streamlit.components.v1 as components
from app_state import load_network, init_session_state, require_auth
from data_lineage.lineage_network.network_filter import (
    G,
    filtered_nodes,
    add_nodes_to_nx_filter,
    clear_nx_graph,
    max_path_length,
    register_network_as_nx,
    get_filtered_network,
)
from data_lineage.lineage_network.network_plot import (
    draw_lineage_plot,
    clean_graphviz_svg,
    wrap_svg_in_html,
)

st.set_page_config(page_title="Filter Network", layout="wide")

require_auth()
init_session_state()

network = load_network()
nodes = network['nodes']

st.title("Filter Network")

# ── Node filter ───────────────────────────────────────────────────────────────
st.subheader("Select nodes")

FILTERABLE_ATTRS = ['module', 'display_name', 'origin', 'pbi_name']

col1, col2 = st.columns(2)
with col1:
    selected_attr = st.selectbox("Node attribute", FILTERABLE_ATTRS)
with col2:
    unique_values = sorted({
        str(node[selected_attr])
        for node in nodes
        if selected_attr in node
    })
    selected_values = st.multiselect("Attribute values", unique_values)

if st.button("Add nodes to filter", disabled=not selected_values):
    add_nodes_to_nx_filter(selected_attr, selected_values)
    st.session_state['applied_filters'].append((selected_attr, list(selected_values)))

# Show accumulated filters
if st.session_state.get('applied_filters'):
    st.markdown("**Active filters:**")
    for attr, vals in st.session_state['applied_filters']:
        st.markdown(f"- `{attr}` in `{vals}`")
else:
    st.info("No filters added yet. Select an attribute and values above, then click **Add nodes to filter**.")

if st.button("Clear filters"):
    clear_nx_graph()
    register_network_as_nx(network)
    st.session_state['applied_filters'] = []
    st.session_state.pop('plot_html', None)
    st.session_state.pop('descendant_level', None)
    st.session_state.pop('ancestor_level', None)
    st.rerun()

st.divider()

# ── Traversal level controls ──────────────────────────────────────────────────
st.subheader("Expansion levels")

max_len = max_path_length(G)
level_options = [None] + list(range(1, max_len + 1)) + ['max']

def fmt_level(x):
    if x is None:
        return "None (no expansion)"
    if x == 'max':
        return "max (all reachable)"
    return str(x)

col3, col4 = st.columns(2)
with col3:
    descendant_level = st.selectbox(
        "Descendant levels",
        level_options,
        format_func=fmt_level,
        index=level_options.index(st.session_state.get('descendant_level')),
    )
with col4:
    ancestor_level = st.selectbox(
        "Ancestor levels",
        level_options,
        format_func=fmt_level,
        index=level_options.index(st.session_state.get('ancestor_level')),
    )

st.session_state['descendant_level'] = descendant_level
st.session_state['ancestor_level'] = ancestor_level

st.divider()

# ── Generate plot ─────────────────────────────────────────────────────────────
has_filters = bool(filtered_nodes)

if not has_filters:
    st.info("Add at least one filter before generating the plot.")
else:
    if st.button("Generate plot"):
        with st.spinner("Generating plot..."):
            filtered_network = get_filtered_network(descendant_level, ancestor_level)
            svg_bytes = draw_lineage_plot(filtered_network)
            svg_clean = clean_graphviz_svg(svg_bytes)
            st.session_state['plot_html'] = wrap_svg_in_html(svg_clean)

if 'plot_html' in st.session_state:
    st.markdown("Plot also available on the **Network Plot** page.")
