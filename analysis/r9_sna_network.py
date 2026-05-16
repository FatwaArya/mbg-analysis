#!/usr/bin/env python3
"""SNA — Reply Network Analysis with centrality metrics (optimized for large graphs)."""
import pandas as pd
import numpy as np
import networkx as nx
import time

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR
MIN_INTERACTIONS = 2

print("Loading data...")
t0 = time.time()
replies = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv",
                      usecols=["id", "user_screen_name", "user_id", "parent_id",
                               "favorite_count", "retweet_count", "reply_count",
                               "sentiment_label", "depth"])
replies["id"] = replies["id"].astype(str)
replies["parent_id"] = replies["parent_id"].astype(str)
replies["user"] = replies["user_screen_name"].fillna(replies["user_id"].astype(str))
print(f"  Replies: {len(replies):,} ({time.time()-t0:.1f}s)")

# ── Build Network: reply_user → parent_id ───────────────────────────
print("\n1. Building reply network...")
replies["parent_user"] = replies["parent_id"].fillna("unknown")

edges_df = replies.groupby(["user", "parent_user"]).size().reset_index(name="weight")
edges_df = edges_df[edges_df["user"] != edges_df["parent_user"]]
edges_df = edges_df[edges_df["parent_user"] != "unknown"]

print(f"  Raw edges: {len(edges_df):,}")

# ── Centrality Metrics (computed from edges directly for speed) ─────
print("\n2. Computing centrality metrics...")
in_degree = edges_df.groupby("parent_user")["weight"].sum().to_dict()
out_degree = edges_df.groupby("user")["weight"].sum().to_dict()

all_users = set(in_degree.keys()) | set(out_degree.keys())
print(f"  Total unique nodes: {len(all_users):,}")

# Build graph for PageRank and betweenness (filter to active users)
active_users = set()
for u, d in in_degree.items():
    if d >= MIN_INTERACTIONS:
        active_users.add(u)
for u, d in out_degree.items():
    if d >= MIN_INTERACTIONS:
        active_users.add(u)

active_edges = edges_df[(edges_df["user"].isin(active_users)) & (edges_df["parent_user"].isin(active_users))]
print(f"  Active users (>= {MIN_INTERACTIONS} interactions): {len(active_users):,}")
print(f"  Active edges: {len(active_edges):,}")

G = nx.DiGraph()
for _, row in active_edges.iterrows():
    G.add_edge(row["user"], row["parent_user"], weight=row["weight"])

print(f"  Graph nodes: {G.number_of_nodes():,}")
print(f"  Graph edges: {G.number_of_edges():,}")

print("   PageRank (active subgraph)...")
pagerank = nx.pagerank(G, weight="weight", max_iter=100, tol=1e-06)
print("   Betweenness centrality (sampled)...")
sample_k = min(500, G.number_of_nodes())
betweenness = nx.betweenness_centrality(G, weight="weight", k=sample_k)

# ── Build Full Centrality Table ─────────────────────────────────────
print("\n3. Building centrality table...")
centrality = pd.DataFrame({
    "user": list(all_users),
    "in_degree": [in_degree.get(u, 0) for u in all_users],
    "out_degree": [out_degree.get(u, 0) for u in all_users],
    "betweenness": [betweenness.get(u, 0) for u in all_users],
    "pagerank": [pagerank.get(u, 0) for u in all_users],
})
centrality["in_degree_centrality"] = centrality["in_degree"] / max(len(all_users) - 1, 1)
centrality["out_degree_centrality"] = centrality["out_degree"] / max(len(all_users) - 1, 1)

# ── Network Stats ───────────────────────────────────────────────────
print("\n4. Computing network statistics...")
components = list(nx.weakly_connected_components(G))
component_sizes = [len(c) for c in components]
largest_component = max(component_sizes) if component_sizes else 0

density = nx.density(G)
avg_clustering = nx.average_clustering(G.to_undirected())

network_stats = pd.DataFrame([{
    "num_nodes": G.number_of_nodes(),
    "num_edges": G.number_of_edges(),
    "density": round(density, 8),
    "num_weak_components": len(component_sizes),
    "largest_component_size": largest_component,
    "avg_clustering_coefficient": round(avg_clustering, 6),
    "avg_in_degree": round(np.mean(list(in_degree.values())), 4),
    "avg_out_degree": round(np.mean(list(out_degree.values())), 4),
    "max_in_degree": max(in_degree.values()) if in_degree else 0,
    "max_out_degree": max(out_degree.values()) if out_degree else 0,
}])

# ── Save Outputs ────────────────────────────────────────────────────
print(f"\nSaving outputs...")
edges_df.to_csv(f"{OUTPUT_DIR}/reply_network_edges.csv", index=False)
print(f"  Saved → reply_network_edges.csv ({len(edges_df):,} edges)")

centrality.to_csv(f"{OUTPUT_DIR}/user_centrality.csv", index=False)
print(f"  Saved → user_centrality.csv ({len(centrality):,} users)")

network_stats.to_csv(f"{OUTPUT_DIR}/network_stats.csv", index=False)
print(f"  Saved → network_stats.csv")

print(f"\n=== SNA COMPLETE ({time.time()-t0:.1f}s) ===")
print(f"  Top 10 by PageRank:")
top_pr = centrality.nlargest(10, "pagerank")[["user", "pagerank", "in_degree", "out_degree"]]
print(top_pr.to_string(index=False))
