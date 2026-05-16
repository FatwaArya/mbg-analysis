#!/usr/bin/env python3
"""Co-Reply Network — Build user-user network from shared parent replies.

If user A and user B both reply to the same parent post, they share a connection.
The weight = number of shared parents. This reveals echo chambers and coordinated behavior.
"""
import pandas as pd
import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix
from collections import defaultdict
import time

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR
MIN_SHARED_PARENTS = 2
MIN_USER_REPLIES = 3

print("Loading data...")
t0 = time.time()
df = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv",
                 usecols=["id", "user_screen_name", "user_id", "parent_id",
                          "favorite_count", "retweet_count", "sentiment_label"])
df["id"] = df["id"].astype(str)
df["parent_id"] = df["parent_id"].astype(str)
df["user"] = df["user_screen_name"].fillna(df["user_id"].astype(str))
df = df[df["parent_id"].notna() & (df["parent_id"] != "nan")]
print(f"  Loaded {len(df):,} rows, {df['user'].nunique():,} users ({time.time()-t0:.1f}s)")

# ── Filter to active users ──────────────────────────────────────────
print("\n1. Filtering to active users...")
user_parent_counts = df.groupby("user")["parent_id"].nunique()
active_users = user_parent_counts[user_parent_counts >= MIN_USER_REPLIES].index
df_active = df[df["user"].isin(active_users)]
print(f"  Active users (>= {MIN_USER_REPLIES} parents): {len(active_users):,}")
print(f"  Active rows: {len(df_active):,}")

# ── Build user-parent mapping ───────────────────────────────────────
print("\n2. Building user-parent mapping...")
user_parents = df_active.groupby("user")["parent_id"].apply(set).to_dict()
parent_users = defaultdict(set)
for user, parents in user_parents.items():
    for parent in parents:
        parent_users[parent].add(user)

print(f"  Unique parents with active replies: {len(parent_users):,}")

# ── Build co-reply edges ────────────────────────────────────────────
print("\n3. Building co-reply edges...")
edge_counts = defaultdict(int)
for parent, users in parent_users.items():
    users_list = list(users)
    if len(users_list) < 2:
        continue
    for i in range(len(users_list)):
        for j in range(i + 1, len(users_list)):
            u1, u2 = sorted([users_list[i], users_list[j]])
            edge_counts[(u1, u2)] += 1

print(f"  Raw edge pairs: {len(edge_counts):,}")

# Filter by minimum shared parents
edges_filtered = {k: v for k, v in edge_counts.items() if v >= MIN_SHARED_PARENTS}
print(f"  Edges with >= {MIN_SHARED_PARENTS} shared parents: {len(edges_filtered):,}")

# ── Build Graph ─────────────────────────────────────────────────────
print("\n4. Building network graph...")
G = nx.Graph()
for (u1, u2), weight in edges_filtered.items():
    G.add_edge(u1, u2, weight=weight)

print(f"  Nodes: {G.number_of_nodes():,}")
print(f"  Edges: {G.number_of_edges():,}")

# ── Community Detection ─────────────────────────────────────────────
print("\n5. Detecting communities (Louvain)...")
try:
    import community as community_louvain
    partition = community_louvain.best_partition(G, weight="weight", random_state=42)
    print(f"  Found {len(set(partition.values()))} communities")
except ImportError:
    print("  python-louvain not installed, using connected components")
    partition = {}
    for i, comp in enumerate(nx.connected_components(G)):
        for node in comp:
            partition[node] = i
    print(f"  Found {len(set(partition.values()))} components")

# ── Node Attributes ─────────────────────────────────────────────────
print("\n6. Computing node attributes...")
user_sentiment = df_active.groupby("user")["sentiment_label"].agg(
    neg_pct=lambda x: (x == "negative").mean() * 100,
    neu_pct=lambda x: (x == "neutral").mean() * 100,
    pos_pct=lambda x: (x == "positive").mean() * 100,
    reply_count="count"
).to_dict("index")

user_engagement = df_active.groupby("user").agg(
    avg_fav=("favorite_count", "mean"),
    total_fav=("favorite_count", "sum"),
    avg_rt=("retweet_count", "mean"),
    total_rt=("retweet_count", "sum"),
).to_dict("index")

# ── Save Outputs ────────────────────────────────────────────────────
print(f"\n7. Saving outputs...")

# Edges
edges_df = pd.DataFrame([
    {"user1": u1, "user2": u2, "shared_parents": w}
    for (u1, u2), w in edges_filtered.items()
])
edges_df.to_csv(f"{OUTPUT_DIR}/co_reply_edges.csv", index=False)
print(f"  Saved → co_reply_edges.csv ({len(edges_df):,} edges)")

# Nodes with attributes
nodes_data = []
for node in G.nodes():
    comm = partition.get(node, -1)
    degree = G.degree(node, weight="weight")
    sent = user_sentiment.get(node, {})
    eng = user_engagement.get(node, {})
    nodes_data.append({
        "user": node,
        "community": comm,
        "weighted_degree": degree,
        "unweighted_degree": G.degree(node),
        "reply_count": sent.get("reply_count", 0),
        "neg_pct": sent.get("neg_pct", 0),
        "neu_pct": sent.get("neu_pct", 0),
        "pos_pct": sent.get("pos_pct", 0),
        "avg_fav": eng.get("avg_fav", 0),
        "total_fav": eng.get("total_fav", 0),
        "avg_rt": eng.get("avg_rt", 0),
        "total_rt": eng.get("total_rt", 0),
    })

nodes_df = pd.DataFrame(nodes_data)
nodes_df.to_csv(f"{OUTPUT_DIR}/co_reply_nodes.csv", index=False)
print(f"  Saved → co_reply_nodes.csv ({len(nodes_df):,} nodes)")

# Network stats
components = list(nx.connected_components(G))
component_sizes = [len(c) for c in components]
network_stats = pd.DataFrame([{
    "num_nodes": G.number_of_nodes(),
    "num_edges": G.number_of_edges(),
    "num_communities": len(set(partition.values())),
    "num_components": len(components),
    "largest_component_size": max(component_sizes) if component_sizes else 0,
    "avg_degree": round(np.mean([G.degree(n) for n in G.nodes()]), 2),
    "avg_weighted_degree": round(np.mean([G.degree(n, weight="weight") for n in G.nodes()]), 2),
    "density": round(nx.density(G), 6),
    "avg_clustering": round(nx.average_clustering(G), 4),
}])
network_stats.to_csv(f"{OUTPUT_DIR}/co_reply_network_stats.csv", index=False)
print(f"  Saved → co_reply_network_stats.csv")

# Community summary
comm_summary = nodes_df.groupby("community").agg(
    size=("user", "count"),
    avg_reply_count=("reply_count", "mean"),
    avg_neg_pct=("neg_pct", "mean"),
    avg_pos_pct=("pos_pct", "mean"),
    avg_weighted_degree=("weighted_degree", "mean"),
).reset_index()
comm_summary = comm_summary.sort_values("size", ascending=False)
comm_summary.to_csv(f"{OUTPUT_DIR}/co_reply_communities.csv", index=False)
print(f"  Saved → co_reply_communities.csv ({len(comm_summary)} communities)")

print(f"\n=== CO-REPLY NETWORK COMPLETE ({time.time()-t0:.1f}s) ===")
print(f"  Top 10 communities by size:")
print(comm_summary.head(10).to_string(index=False))
