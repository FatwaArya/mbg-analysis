"""
Pre-compute co-reply network layout positions and save to CSV.
Run once after network analysis is generated.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import sys, os

DATA_DIR = "/opt/mbg/data/analysis"
OUTPUT_FILE = os.path.join(DATA_DIR, "co_reply_layout.csv")
TOP_N = 500
MAX_EDGES = 3000

print("Loading network data...")
edges = pd.read_csv(os.path.join(DATA_DIR, "co_reply_edges.csv"))
nodes = pd.read_csv(os.path.join(DATA_DIR, "co_reply_nodes.csv"))

print(f"Total nodes: {len(nodes)}, Total edges: {len(edges)}")

top_users = nodes.nlargest(TOP_N, "weighted_degree")["user"].tolist()
sampled_nodes = nodes[nodes["user"].isin(top_users)].copy()
sampled_edges = edges[(edges["user1"].isin(top_users)) & (edges["user2"].isin(top_users))]

comm_colors = px.colors.qualitative.Set3
comm_map = {c: comm_colors[i % len(comm_colors)] for i, c in enumerate(sampled_nodes["community"].unique())}

print(f"Sampled: {len(sampled_nodes)} nodes, {len(sampled_edges)} edges")
print(f"Communities: {sampled_nodes['community'].nunique()}")

np.random.seed(42)
user_community = dict(zip(sampled_nodes["user"], sampled_nodes["community"]))
community_centers = {}
for comm in sampled_nodes["community"].unique():
    angle = comm * 2 * np.pi / sampled_nodes["community"].nunique()
    community_centers[comm] = (np.cos(angle), np.sin(angle))

user_positions = {}
for u in top_users:
    cx, cy = community_centers[user_community[u]]
    user_positions[u] = (cx + np.random.uniform(-0.3, 0.3), cy + np.random.uniform(-0.3, 0.3))

print("Running force-directed layout (10 iterations)...")
for iteration in range(10):
    forces = {u: [0.0, 0.0] for u in top_users}
    for _, edge in sampled_edges.head(MAX_EDGES).iterrows():
        u1, u2 = edge["user1"], edge["user2"]
        if u1 in user_positions and u2 in user_positions:
            x1, y1 = user_positions[u1]
            x2, y2 = user_positions[u2]
            dx, dy = x2 - x1, y2 - y1
            dist = max(np.sqrt(dx**2 + dy**2), 0.01)
            force = dist * 0.02 * min(edge["shared_parents"], 5)
            forces[u1][0] += force * dx
            forces[u1][1] += force * dy
            forces[u2][0] -= force * dx
            forces[u2][1] -= force * dy
    users_list = list(user_positions.keys())
    for i in range(0, len(users_list), 5):
        for j in range(i + 1, len(users_list), 5):
            u1, u2 = users_list[i], users_list[j]
            x1, y1 = user_positions[u1]
            x2, y2 = user_positions[u2]
            dx, dy = x2 - x1, y2 - y1
            dist = max(np.sqrt(dx**2 + dy**2), 0.01)
            force = 0.3 / dist
            forces[u1][0] -= force * dx
            forces[u1][1] -= force * dy
            forces[u2][0] += force * dx
            forces[u2][1] += force * dy
    for u in top_users:
        user_positions[u] = (
            user_positions[u][0] + forces[u][0] * 0.1,
            user_positions[u][1] + forces[u][1] * 0.1
        )
    if iteration % 2 == 0:
        print(f"  Iteration {iteration+1}/10 done")

layout_rows = []
for u in top_users:
    layout_rows.append({
        "user": u,
        "x": user_positions[u][0],
        "y": user_positions[u][1],
        "community": user_community[u],
        "color": comm_map[user_community[u]],
        "weighted_degree": nodes[nodes["user"] == u]["weighted_degree"].values[0],
    })

layout_df = pd.DataFrame(layout_rows)
layout_df.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved layout to {OUTPUT_FILE} ({len(layout_df)} nodes)")
print(f"X range: [{layout_df['x'].min():.3f}, {layout_df['x'].max():.3f}]")
print(f"Y range: [{layout_df['y'].min():.3f}, {layout_df['y'].max():.3f}]")
