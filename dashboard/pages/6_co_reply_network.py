import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Co-Reply Network  MBG", page_icon=None, layout="wide")
require_auth()

st.title("Co-Reply Network Analysis")
st.caption("Users who reply to the same parents form connections  revealing echo chambers, coordinated behavior, and community structure")
st.markdown("---")

edges = load_reply_dataset("co_reply_edges")
nodes = load_reply_dataset("co_reply_nodes")
network_stats = load_reply_dataset("co_reply_network_stats")
communities = load_reply_dataset("co_reply_communities")

if nodes is None or edges is None:
    st.error("Co-reply network data not available. Run r12_co_reply_network.py first.")
    st.stop()

if network_stats is not None and len(network_stats) > 0:
    stats = network_stats.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Users in Network", f"{int(stats['num_nodes']):,}")
    c2.metric("Connections", f"{int(stats['num_edges']):,}")
    c3.metric("Communities", f"{int(stats['num_communities']):,}")
    c4.metric("Largest Community", f"{int(stats['largest_component_size']):,}")
    c5.metric("Avg Clustering", f"{stats['avg_clustering']:.4f}")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Users in Network", f"{len(nodes):,}")
    c2.metric("Connections", f"{len(edges):,}")
    c3.metric("Communities", f"{nodes['community'].nunique():,}")

st.markdown("---")

st.subheader("Network Graph (Force-Directed Layout)")
st.caption("Nodes = users, Edges = shared parent replies. Colored by community. Larger nodes = more connections.")

@st.cache_data
def load_layout():
    path = "/opt/mbg/data/analysis/co_reply_layout.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

layout = load_layout()

if layout is not None and len(layout) > 0:
    top_n = st.slider("Number of nodes to display", 100, len(layout), 500, step=100)
    display = layout.nlargest(top_n, "weighted_degree")

    sampled_edges = edges[(edges["user1"].isin(display["user"])) & (edges["user2"].isin(display["user"]))]
    sampled_edges = sampled_edges.head(3000)

    edge_x, edge_y = [], []
    pos_map = dict(zip(display["user"], zip(display["x"], display["y"])))
    for _, edge in sampled_edges.iterrows():
        x0, y0 = pos_map.get(edge["user1"], (0, 0))
        x1, y1 = pos_map.get(edge["user2"], (0, 0))
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = display["x"].tolist()
    node_y = display["y"].tolist()
    node_colors = display["color"].tolist()
    node_sizes = [max(5, min(s / 5, 30)) for s in display["weighted_degree"]]
    node_texts = [f"{u}<br>Degree: {d:.0f}<br>Community: {c}" for u, d, c in zip(display["user"], display["weighted_degree"], display["community"])]

    fig_net = go.Figure()
    fig_net.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.5, color="#888"), hoverinfo="none", showlegend=False))
    fig_net.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers",
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=0.5, color="white")),
        text=node_texts, hoverinfo="text", showlegend=False))
    fig_net.update_layout(
        hovermode="closest", margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)", height=600
    )
    st.plotly_chart(fig_net, use_container_width=True)
else:
    st.warning("Pre-computed layout not found. Run `scripts/compute_network_layout.py` on the VPS.")

st.markdown("---")

st.subheader("Community Analysis")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Community Size Distribution")
    top_comms = communities.nlargest(20, "size")
    fig_comm = px.bar(top_comms, x="community", y="size",
                      labels={"community": "Community ID", "size": "Number of Users"},
                      color="size", color_continuous_scale="Viridis")
    fig_comm.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig_comm, use_container_width=True)

with col2:
    st.markdown("#### Community Size Histogram (Log)")
    fig_hist = px.histogram(communities, x="size", nbins=30,
                            labels={"size": "Community Size", "count": "Number of Communities"},
                            color_discrete_sequence=["#e74c3c"], log_y=True)
    fig_hist.update_layout(bargap=0.05, showlegend=False, height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("#### Community Sentiment Profiles")
fig_sent = px.scatter(
    communities, x="avg_neg_pct", y="avg_pos_pct",
    size="size", color="size", color_continuous_scale="Reds",
    labels={"avg_neg_pct": "Avg Negative %", "avg_pos_pct": "Avg Positive %", "size": "Community Size"},
    hover_data=["community", "avg_reply_count", "avg_weighted_degree"],
    size_max=50
)
fig_sent.update_layout(height=400, margin=dict(t=10, b=10))
st.plotly_chart(fig_sent, use_container_width=True)

st.markdown("---")

st.subheader("Top Communities")

tab1, tab2, tab3 = st.tabs(["By Size", "By Engagement", "By Sentiment"])

with tab1:
    st.dataframe(
        communities.nlargest(30, "size")[["community", "size", "avg_reply_count", "avg_neg_pct", "avg_pos_pct", "avg_weighted_degree"]],
        use_container_width=True,
        column_config={
            "community": "ID", "size": "Users",
            "avg_reply_count": st.column_config.NumberColumn("Avg Replies", format="%.1f"),
            "avg_neg_pct": st.column_config.NumberColumn("Neg %", format="%.1f"),
            "avg_pos_pct": st.column_config.NumberColumn("Pos %", format="%.1f"),
            "avg_weighted_degree": st.column_config.NumberColumn("Avg Connections", format="%.1f"),
        }
    )

with tab2:
    st.dataframe(
        communities.nlargest(30, "avg_weighted_degree")[["community", "size", "avg_weighted_degree", "avg_reply_count", "avg_neg_pct"]],
        use_container_width=True,
        column_config={
            "community": "ID", "size": "Users",
            "avg_weighted_degree": st.column_config.NumberColumn("Avg Connections", format="%.1f"),
            "avg_reply_count": st.column_config.NumberColumn("Avg Replies", format="%.1f"),
            "avg_neg_pct": st.column_config.NumberColumn("Neg %", format="%.1f"),
        }
    )

with tab3:
    st.dataframe(
        communities[communities["avg_pos_pct"] > 20].nlargest(30, "avg_pos_pct")[["community", "size", "avg_pos_pct", "avg_neg_pct", "avg_reply_count"]],
        use_container_width=True,
        column_config={
            "community": "ID", "size": "Users",
            "avg_pos_pct": st.column_config.NumberColumn("Pos %", format="%.1f"),
            "avg_neg_pct": st.column_config.NumberColumn("Neg %", format="%.1f"),
            "avg_reply_count": st.column_config.NumberColumn("Avg Replies", format="%.1f"),
        }
    )

st.markdown("---")

st.subheader("Ego Network Explorer")
st.caption("Select a user to see their direct connections in the co-reply network")

user_options = nodes.nlargest(100, "weighted_degree")["user"].tolist()
selected_user = st.selectbox("Select a user", user_options)

if selected_user:
    user_edges = edges[(edges["user1"] == selected_user) | (edges["user2"] == selected_user)]
    ego_users = set()
    for _, e in user_edges.iterrows():
        if e["user1"] == selected_user:
            ego_users.add(e["user2"])
        else:
            ego_users.add(e["user1"])

    ego_nodes = nodes[nodes["user"].isin(ego_users | {selected_user})]
    ego_edges = edges[(edges["user1"].isin(ego_users | {selected_user})) & (edges["user2"].isin(ego_users | {selected_user}))]

    c1e, c2e, c3e = st.columns(3)
    c1e.metric("Direct Connections", len(ego_users))
    c2e.metric("Ego Network Edges", len(ego_edges))
    c3e.metric("Communities in Ego", ego_nodes["community"].nunique())

    np.random.seed(42)
    ego_positions = {selected_user: (0, 0)}
    for u in ego_users:
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(0.5, 1)
        ego_positions[u] = (radius * np.cos(angle), radius * np.sin(angle))

    ego_edge_x, ego_edge_y = [], []
    for _, e in ego_edges.iterrows():
        x0, y0 = ego_positions.get(e["user1"], (0, 0))
        x1, y1 = ego_positions.get(e["user2"], (0, 0))
        ego_edge_x.extend([x0, x1, None])
        ego_edge_y.extend([y0, y1, None])

    ego_node_x = [ego_positions[u][0] for u in ego_nodes["user"]]
    ego_node_y = [ego_positions[u][1] for u in ego_nodes["user"]]
    # Build community color map from layout or nodes
    if layout is not None:
        ego_colors_map = dict(zip(layout["community"], layout["color"]))
    else:
        comm_colors = px.colors.qualitative.Set3
        ego_colors_map = {c: comm_colors[i % len(comm_colors)] for i, c in enumerate(ego_nodes["community"].unique())}

    ego_node_colors = [ego_colors_map.get(ego_nodes[ego_nodes["user"] == u]["community"].values[0], "#e74c3c") for u in ego_nodes["user"]]
    ego_node_sizes = [20 if u == selected_user else max(5, ego_nodes[ego_nodes["user"] == u]["weighted_degree"].values[0] / 5) for u in ego_nodes["user"]]

    fig_ego = go.Figure()
    fig_ego.add_trace(go.Scatter(x=ego_edge_x, y=ego_edge_y, mode="lines",
        line=dict(width=1, color="#888"), hoverinfo="none", showlegend=False))
    fig_ego.add_trace(go.Scatter(x=ego_node_x, y=ego_node_y, mode="markers",
        marker=dict(size=ego_node_sizes, color=ego_node_colors, line=dict(width=1, color="white")),
        text=ego_nodes["user"], hoverinfo="text", showlegend=False))
    fig_ego.update_layout(
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)", height=400
    )
    st.plotly_chart(fig_ego, use_container_width=True)

st.markdown("---")

if network_stats is not None and len(network_stats) > 0:
    st.subheader("Network Statistics Summary")
    st.dataframe(network_stats.T, use_container_width=True)
