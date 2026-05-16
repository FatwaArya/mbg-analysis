#!/usr/bin/env python3
"""SNA — Reply Network Analysis with centrality metrics."""
import pandas as pd
import numpy as np
import networkx as nx
from collections import Counter
import time

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
t0 = time.time()
replies = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv",
                      usecols=["id", "user_screen_name", "user_id", "parent_id",
                               "favorite_count", "retweet_count", "reply_count",
                               "sentiment_label", "depth"])
replies["id"] = replies["id"].astype(str)
replies["parent_id"] = replies["parent_id"].astype(str)
replies["user"] = replies["user_screen_name"].fillna(replies["user_id"].astype(str))

corpus = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv",
                     usecols=["id", "user_screen_name", "user_id", "parent_id", "tweet_type"],
                     dtype={"id": str, "user_id": str, "parent_id": str})
corpus["user"] = corpus["user_screen_name"].fillna(corpus["user_id"].astype(str))

print(f"  Replies: {len(replies):,}, Corpus: {len(corpus):,} ({time.time()-t0:.1f}s)")

# ── Build Network: reply_user → parent_user ─────────────────────────
print("\n1. Building reply network...")
parent_users = corpus.set_index("id")["user"]
replies["parent_user"] = replies["parent_id"].map(parent_users)
replies["parent_user"] = replies["parent_user"].fillna("unknown")

edges = replies.groupby(["user", "parent_user"]).size().reset_index(name="weight")
edges = edges[edges["user"] != edges["parent_user"]]
edges = edges[edges["parent_user"] != "unknown"]

G = nx.DiGraph()
for _, row in edges.iterrows():
    G.add_edge(row["user"], row["parent_user"], weight=row["weight"])

print(f"  Nodes: {G.number_of_nodes():,}")
print(f"  Edges: {G.number_of_edges():,}")

# ── Centrality Metrics ──────────────────────────────────────────────
print("\n2. Computing centrality metrics...")
print("   In-degree centrality...")
in_degree = dict(G.in_degree(weight="weight"))
print("   Out-degree centrality...")
out_degree = dict(G.out_degree(weight="weight"))
print("   Betweenness centrality...")
betweenness = nx.betweenness_centrality(G, weight="weight", k=min(5000, G.number_of_nodes()))
print("   PageRank...")
pagerank = nx.pagerank(G, weight="weight")

all_users = set(in_degree.keys()) | set(out_degree.keys())
centrality = pd.DataFrame({
    "user": list(all_users),
    "in_degree": [in_degree.get(u, 0) for u in all_users],
    "out_degree": [out_degree.get(u, 0) for u in all_users],
    "betweenness": [betweenness.get(u, 0) for u in all_users],
    "pagerank": [pagerank.get(u, 0) for u in all_users],
})
centrality["in_degree_centrality"] = centrality["in_degree"] / max(G.number_of_nodes() - 1, 1)
centrality["out_degree_centrality"] = centrality["out_degree"] / max(G.number_of_nodes() - 1, 1)

# ── Network Stats ───────────────────────────────────────────────────
print("\n3. Computing network statistics...")
components = nx.weakly_connected_components(G)
component_sizes = [len(c) for c in components]
largest_component = max(component_sizes)

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
edges.to_csv(f"{OUTPUT_DIR}/reply_network_edges.csv", index=False)
print(f"  Saved → reply_network_edges.csv ({len(edges):,} edges)")

centrality.to_csv(f"{OUTPUT_DIR}/user_centrality.csv", index=False)
print(f"  Saved → user_centrality.csv ({len(centrality):,} users)")

network_stats.to_csv(f"{OUTPUT_DIR}/network_stats.csv", index=False)
print(f"  Saved → network_stats.csv")

print(f"\n=== SNA COMPLETE ({time.time()-t0:.1f}s) ===")
print(f"  Top 10 by PageRank:")
top_pr = centrality.nlargest(10, "pagerank")[["user", "pagerank", "in_degree", "out_degree"]]
print(top_pr.to_string(index=False))
