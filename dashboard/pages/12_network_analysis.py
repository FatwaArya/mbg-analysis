import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Network Analysis  MBG", page_icon=None, layout="wide")
require_auth()

st.title("Social Network Analysis")
st.caption("Reply-to-reply network structure, centrality metrics, and community detection")
st.markdown("---")

edges = load_reply_dataset("reply_network_edges")
centrality = load_reply_dataset("user_centrality")
network_stats = load_reply_dataset("network_stats")

if edges is None or centrality is None:
    st.error("Network data not available. Run r9_sna_network.py first.")
    st.stop()

#  KPIs
if network_stats is not None and len(network_stats) > 0:
    stats = network_stats.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Nodes", f"{int(stats['num_nodes']):,}")
    c2.metric("Edges", f"{int(stats['num_edges']):,}")
    c3.metric("Density", f"{stats['density']:.6f}")
    c4.metric("Largest Component", f"{int(stats['largest_component_size']):,}")
    c5.metric("Avg Clustering", f"{stats['avg_clustering_coefficient']:.4f}")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Nodes", f"{centrality['user'].nunique():,}")
    c2.metric("Edges", f"{len(edges):,}")
    c3.metric("Density", "N/A")

st.markdown("---")

#  1. Network Visualization (Sampled)
st.subheader("Network Visualization (Top 500 by PageRank)")
top_users = centrality.nlargest(500, "pagerank")["user"].tolist()
sampled_edges = edges[(edges["user"].isin(top_users)) & (edges["parent_user"].isin(top_users))]

if len(sampled_edges) > 0:
    fig_net = go.Figure()
    fig_net.add_trace(go.Scatter(
        x=[], y=[], mode="lines",
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        showlegend=False
    ))
    fig_net.add_trace(go.Scatter(
        x=[], y=[], mode="markers",
        marker=dict(size=8, color="#3498db"),
        hoverinfo="text",
        showlegend=False
    ))

    import numpy as np
    np.random.seed(42)
    node_positions = {node: (np.random.uniform(-1, 1), np.random.uniform(-1, 1)) for node in top_users}

    edge_x, edge_y = [], []
    for _, edge in sampled_edges.head(2000).iterrows():
        x0, y0 = node_positions.get(edge["user"], (0, 0))
        x1, y1 = node_positions.get(edge["parent_user"], (0, 0))
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = [node_positions[n][0] for n in top_users]
    node_y = [node_positions[n][1] for n in top_users]

    fig_net.data[0].x = edge_x
    fig_net.data[0].y = edge_y
    fig_net.data[1].x = node_x
    fig_net.data[1].y = node_y
    fig_net.data[1].text = top_users
    fig_net.data[1].marker.size = [centrality[centrality["user"] == u]["pagerank"].values[0] * 10000 + 5 for u in top_users]
    fig_net.data[1].marker.color = [centrality[centrality["user"] == u]["in_degree"].values[0] for u in top_users]
    fig_net.data[1].marker.colorscale = "Viridis"
    fig_net.data[1].marker.showscale = True
    fig_net.data[1].marker.colorbar.title = "In-Degree"

    fig_net.update_layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_net, use_container_width=True)
else:
    st.warning("No edges found in sampled network.")

#  2. Centrality Rankings
st.subheader("Centrality Rankings")
tab1, tab2, tab3, tab4 = st.tabs(["PageRank", "In-Degree", "Out-Degree", "Betweenness"])

with tab1:
    st.dataframe(
        centrality.nlargest(50, "pagerank")[["user", "pagerank", "in_degree", "out_degree", "betweenness"]],
        use_container_width=True,
        column_config={"user": "Username", "pagerank": st.column_config.NumberColumn("PageRank", format="%.6f")}
    )

with tab2:
    st.dataframe(
        centrality.nlargest(50, "in_degree")[["user", "in_degree", "pagerank"]],
        use_container_width=True,
        column_config={"user": "Username", "in_degree": "In-Degree (Weighted)"}
    )

with tab3:
    st.dataframe(
        centrality.nlargest(50, "out_degree")[["user", "out_degree", "pagerank"]],
        use_container_width=True,
        column_config={"user": "Username", "out_degree": "Out-Degree (Weighted)"}
    )

with tab4:
    st.dataframe(
        centrality.nlargest(50, "betweenness")[["user", "betweenness", "pagerank"]],
        use_container_width=True,
        column_config={"user": "Username", "betweenness": st.column_config.NumberColumn("Betweenness", format="%.6f")}
    )

#  3. Degree Distribution
st.subheader("Degree Distribution")
col1, col2 = st.columns(2)
with col1:
    fig_in = px.histogram(
        centrality[centrality["in_degree"] > 0], x="in_degree", nbins=50,
        labels={"in_degree": "In-Degree (Weighted)", "count": "Users"},
        color_discrete_sequence=["#e74c3c"], log_y=True
    )
    fig_in.update_layout(bargap=0.05, showlegend=False)
    st.plotly_chart(fig_in, use_container_width=True)

with col2:
    fig_out = px.histogram(
        centrality[centrality["out_degree"] > 0], x="out_degree", nbins=50,
        labels={"out_degree": "Out-Degree (Weighted)", "count": "Users"},
        color_discrete_sequence=["#3498db"], log_y=True
    )
    fig_out.update_layout(bargap=0.05, showlegend=False)
    st.plotly_chart(fig_out, use_container_width=True)

#  4. Network Stats Summary
if network_stats is not None and len(network_stats) > 0:
    st.subheader("Network Statistics Summary")
    st.dataframe(network_stats.T, use_container_width=True)
