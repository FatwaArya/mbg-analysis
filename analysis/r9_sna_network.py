#!/usr/bin/env python3
"""SNA — Reply Network Analysis (per user group).

Directed graph: nodes = users, edges = reply_user → parent_user (weighted by interaction count)
- Global metrics: avg degree, avg shortest path, diameter, clustering coefficient, communities
- Community detection: Louvain
- Per community: closeness centrality, betweenness centrality
- Identify 2 polarized communities per group (politician-heavy)
- Per polarized community: top node by in-degree, betweenness, closeness
- Sampling: fold-based with consistency check for large graphs
"""
import pandas as pd
import numpy as np
import networkx as nx
import time
import os
import logging
from collections import defaultdict

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR
REPLIES_FILE = f"{ANALYSIS_DIR}/replies_with_sentiment.csv"
USER_GROUPS_FILE = f"{ANALYSIS_DIR}/user_groups.csv"

# Sampling parameters
FOLD_BASED_SAMPLE_NODES = 500
N_FOLDS = 5
LARGE_GRAPH_THRESHOLD = 1000  # nodes
MIN_INTERACTIONS = 2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Try Louvain import ──
try:
    import community as community_louvain
    HAS_LOUVAIN = True
except ImportError:
    HAS_LOUVAIN = False
    log.warning("python-louvain not installed; falling back to connected components")


def fold_based_sample(G, n_folds=N_FOLDS, seed=42):
    """Fold-based sampling with consistency check."""
    rng = np.random.RandomState(seed)
    nodes = list(G.nodes())
    rng.shuffle(nodes)

    fold_size = max(1, len(nodes) // n_folds)
    folds = [nodes[i * fold_size:(i + 1) * fold_size] for i in range(n_folds)]
    if len(nodes) % n_folds != 0:
        folds[-1].extend(nodes[n_folds * fold_size:])

    fold_metrics = []
    fold_graphs = []

    for i, fold_nodes in enumerate(folds):
        subG = G.subgraph(fold_nodes).copy()
        if subG.number_of_nodes() < 10:
            continue
        largest_cc = max(nx.weakly_connected_components(subG), key=len)
        subG = subG.subgraph(largest_cc).copy()
        if subG.number_of_nodes() < 10:
            continue

        fold_graphs.append(subG)
        fold_metrics.append({
            "fold": i,
            "nodes": subG.number_of_nodes(),
            "edges": subG.number_of_edges(),
            "density": nx.density(subG),
            "avg_clustering": nx.average_clustering(subG.to_undirected()),
        })

    if not fold_metrics:
        return G, None

    metrics_df = pd.DataFrame(fold_metrics)
    cv_density = metrics_df["density"].std() / max(metrics_df["density"].mean(), 1e-10)
    cv_clustering = metrics_df["avg_clustering"].std() / max(metrics_df["avg_clustering"].mean(), 1e-10)
    consistent = cv_density < 0.3 and cv_clustering < 0.3

    log.info(f"  Fold-based sampling: {len(fold_metrics)} folds, "
             f"CV_density={cv_density:.3f}, CV_clustering={cv_clustering:.3f}, "
             f"consistent={consistent}")

    best_fold = max(fold_graphs, key=lambda g: g.number_of_nodes())
    return best_fold, metrics_df


def detect_communities(G):
    """Louvain community detection with connected components fallback."""
    if HAS_LOUVAIN:
        partition = community_louvain.best_partition(G.to_undirected(), weight="weight", random_state=42)
    else:
        partition = {}
        for i, comp in enumerate(nx.connected_components(G.to_undirected())):
            for node in comp:
                partition[node] = i
    return partition


def compute_per_community_centrality(G, partition, sample_k=None):
    """Compute closeness and betweenness centrality per community."""
    communities = defaultdict(list)
    for node, comm_id in partition.items():
        communities[comm_id].append(node)

    community_centrality = []

    for comm_id, members in communities.items():
        if len(members) < 2:
            continue

        subG = G.subgraph(members).copy()
        if subG.number_of_nodes() < 2:
            continue

        k = sample_k if sample_k and len(members) > sample_k else None
        betweenness = nx.betweenness_centrality(subG, weight="weight", k=k)

        try:
            if nx.is_weakly_connected(subG):
                closeness = nx.closeness_centrality(subG, distance="weight")
            else:
                closeness = {}
                for comp in nx.weakly_connected_components(subG):
                    comp_sub = subG.subgraph(comp)
                    if len(comp_sub) > 1:
                        cc = nx.closeness_centrality(comp_sub, distance="weight")
                        closeness.update(cc)
        except Exception:
            closeness = {n: 0.0 for n in members}

        for node in members:
            community_centrality.append({
                "user": node,
                "community": comm_id,
                "betweenness_centrality": betweenness.get(node, 0.0),
                "closeness_centrality": closeness.get(node, 0.0),
            })

    return pd.DataFrame(community_centrality)


def identify_polarized_communities(G, partition, user_groups_df=None, group_label=None):
    """Identify 2 most polarized communities per group."""
    communities = defaultdict(list)
    for node, comm_id in partition.items():
        communities[comm_id].append(node)

    comm_scores = []
    for comm_id, members in communities.items():
        subG = G.subgraph(members).copy()
        if subG.number_of_nodes() < 2:
            continue

        internal_density = nx.density(subG)
        in_degree = dict(subG.in_degree(weight="weight"))
        avg_in_degree = np.mean(list(in_degree.values())) if in_degree else 0

        n_politicians = 0
        if user_groups_df is not None and "user_type" in user_groups_df.columns:
            group_users = user_groups_df[user_groups_df["group"] == group_label]
            politicians = set(group_users[group_users["user_type"] == "politician"]["user"])
            n_politicians = len(set(members) & politicians)

        cross_edges = 0
        total_edges = 0
        for u, v in subG.edges():
            total_edges += 1
            if partition.get(v) != comm_id:
                cross_edges += 1
        cross_ratio = cross_edges / max(total_edges, 1)

        polarization_score = internal_density * (1 - cross_ratio) * (1 + n_politicians / max(len(members), 1))

        comm_scores.append({
            "community": comm_id,
            "size": len(members),
            "internal_density": internal_density,
            "n_politicians": n_politicians,
            "cross_community_ratio": cross_ratio,
            "polarization_score": polarization_score,
            "avg_in_degree": avg_in_degree,
        })

    if not comm_scores:
        return pd.DataFrame(), {}

    scores_df = pd.DataFrame(comm_scores)
    scores_df = scores_df.sort_values("polarization_score", ascending=False)
    top2 = scores_df.head(2)

    return scores_df, {comm_id: row.to_dict() for comm_id, row in top2.iterrows()}


def analyze_graph(G, group_label, user_groups_df=None):
    """Full analysis of a single reply network graph."""
    log.info(f"\n{'='*60}")
    log.info(f"Analyzing group: {group_label}")
    log.info(f"{'='*60}")

    results = {}

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    results["num_nodes"] = n_nodes
    results["num_edges"] = n_edges
    results["density"] = nx.density(G)
    results["avg_clustering"] = nx.average_clustering(G.to_undirected())

    in_degrees = [d for _, d in G.in_degree(weight="weight")]
    out_degrees = [d for _, d in G.out_degree(weight="weight")]
    results["avg_in_degree"] = np.mean(in_degrees) if in_degrees else 0
    results["avg_out_degree"] = np.mean(out_degrees) if out_degrees else 0
    results["avg_degree"] = (results["avg_in_degree"] + results["avg_out_degree"]) / 2

    # ── Sampling for large graphs ──
    if n_nodes > LARGE_GRAPH_THRESHOLD:
        log.info(f"  Graph too large ({n_nodes} nodes), applying fold-based sampling...")
        sampled_G, fold_metrics = fold_based_sample(G)
        if sampled_G is not None and sampled_G.number_of_nodes() < n_nodes:
            G = sampled_G
            n_nodes = G.number_of_nodes()
            n_edges = G.number_of_edges()
            log.info(f"  Using sampled graph: {n_nodes} nodes, {n_edges} edges")

    # ── Connected components ──
    wccs = list(nx.weakly_connected_components(G))
    results["num_weak_components"] = len(wccs)
    results["largest_component_size"] = max(len(c) for c in wccs) if wccs else 0

    # ── Avg shortest path and diameter (on largest WCC) ──
    if wccs:
        largest_cc = max(wccs, key=len)
        largest_cc_sub = G.subgraph(largest_cc).to_undirected()
        if nx.is_connected(largest_cc_sub) and largest_cc_sub.number_of_nodes() > 1:
            try:
                avg_sp = nx.average_shortest_path_length(largest_cc_sub, weight="weight")
                diameter = nx.diameter(largest_cc_sub, weight="weight")
                results["avg_shortest_path"] = avg_sp
                results["diameter"] = diameter
                log.info(f"  Avg shortest path: {avg_sp:.4f}, Diameter: {diameter}")
            except Exception as e:
                log.warning(f"  Could not compute shortest path/diameter: {e}")
                results["avg_shortest_path"] = np.nan
                results["diameter"] = np.nan
        else:
            results["avg_shortest_path"] = np.nan
            results["diameter"] = np.nan
    else:
        results["avg_shortest_path"] = np.nan
        results["diameter"] = np.nan

    # ── Community detection ──
    log.info("  Detecting communities (Louvain)...")
    partition = detect_communities(G)
    n_communities = len(set(partition.values()))
    results["num_communities"] = n_communities
    log.info(f"  Found {n_communities} communities")

    # ── Per-community centrality ──
    log.info("  Computing per-community centrality...")
    sample_k = min(500, n_nodes) if n_nodes > 2000 else None
    comm_centrality = compute_per_community_centrality(G, partition, sample_k=sample_k)

    # ── Identify polarized communities ──
    log.info("  Identifying polarized communities...")
    comm_scores, polarized_comms = identify_polarized_communities(
        G, partition, user_groups_df, group_label
    )

    # ── Top nodes per polarized community ──
    polarized_top_nodes = []
    for comm_id, comm_info in polarized_comms.items():
        members = [n for n, c in partition.items() if c == comm_id]
        subG = G.subgraph(members).copy()

        in_degree = dict(subG.in_degree(weight="weight"))
        top_in_degree = max(in_degree.items(), key=lambda x: x[1]) if in_degree else (None, 0)

        betweenness = nx.betweenness_centrality(subG, weight="weight", k=min(500, len(members)))
        top_betweenness = max(betweenness.items(), key=lambda x: x[1]) if betweenness else (None, 0)

        try:
            if nx.is_weakly_connected(subG):
                closeness = nx.closeness_centrality(subG, distance="weight")
            else:
                closeness = {}
                for comp in nx.weakly_connected_components(subG):
                    cc_sub = subG.subgraph(comp)
                    if len(cc_sub) > 1:
                        cc = nx.closeness_centrality(cc_sub, distance="weight")
                        closeness.update(cc)
        except Exception:
            closeness = {n: 0.0 for n in members}
        top_closeness = max(closeness.items(), key=lambda x: x[1]) if closeness else (None, 0)

        polarized_top_nodes.append({
            "group": group_label,
            "community": comm_id,
            "polarization_score": comm_info.get("polarization_score", 0),
            "community_size": comm_info.get("size", len(members)),
            "top_in_degree_user": top_in_degree[0],
            "top_in_degree_value": top_in_degree[1],
            "top_betweenness_user": top_betweenness[0],
            "top_betweenness_value": top_betweenness[1],
            "top_closeness_user": top_closeness[0],
            "top_closeness_value": top_closeness[1],
        })

    results["group"] = group_label
    return results, comm_centrality, comm_scores, polarized_top_nodes, partition


def main():
    t0 = time.time()

    # ── Load reply data ──
    log.info("Loading reply data...")
    if not os.path.exists(REPLIES_FILE):
        log.error(f"Replies file not found: {REPLIES_FILE}")
        raise FileNotFoundError(f"Required: {REPLIES_FILE}")

    replies = pd.read_csv(REPLIES_FILE,
                          usecols=["id", "user_screen_name", "user_id", "parent_id",
                                   "favorite_count", "retweet_count", "reply_count",
                                   "sentiment_label", "depth"])
    replies["id"] = replies["id"].astype(str)
    replies["parent_id"] = replies["parent_id"].astype(str)
    replies["user"] = replies["user_screen_name"].fillna(replies["user_id"].astype(str))
    log.info(f"  Loaded {len(replies):,} replies")

    # Determine group column if available
    if "group" in replies.columns:
        groups = replies["group"].unique()
    else:
        replies["group"] = "all"
        groups = ["all"]

    # Load user groups metadata (for polarized community detection)
    user_groups_df = None
    if os.path.exists(USER_GROUPS_FILE):
        user_groups_df = pd.read_csv(USER_GROUPS_FILE)
        log.info(f"  Loaded {len(user_groups_df):,} user group records")

    log.info(f"Found {len(groups)} user groups: {list(groups)}")

    all_global_stats = []
    all_comm_centrality = []
    all_comm_scores = []
    all_polarized_top = []
    all_partitions = {}

    for group_label in groups:
        group_data = replies[replies["group"] == group_label]

        # ── Build directed graph: reply_user → parent_user ──
        group_data["parent_user"] = group_data["parent_id"].fillna("unknown")
        edges_df = group_data.groupby(["user", "parent_user"]).size().reset_index(name="weight")
        edges_df = edges_df[edges_df["user"] != edges_df["parent_user"]]
        edges_df = edges_df[edges_df["parent_user"] != "unknown"]

        # Filter to active users (>= MIN_INTERACTIONS)
        in_degree = edges_df.groupby("parent_user")["weight"].sum().to_dict()
        out_degree = edges_df.groupby("user")["weight"].sum().to_dict()
        active_users = set()
        for u, d in in_degree.items():
            if d >= MIN_INTERACTIONS:
                active_users.add(u)
        for u, d in out_degree.items():
            if d >= MIN_INTERACTIONS:
                active_users.add(u)

        active_edges = edges_df[(edges_df["user"].isin(active_users)) & (edges_df["parent_user"].isin(active_users))]

        G = nx.DiGraph()
        for _, row in active_edges.iterrows():
            G.add_edge(row["user"], row["parent_user"], weight=row["weight"])

        log.info(f"\nGroup '{group_label}': {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

        if G.number_of_nodes() == 0:
            continue

        results, comm_centrality, comm_scores, polarized_top, partition = analyze_graph(
            G, group_label, user_groups_df
        )

        all_global_stats.append(results)
        if not comm_centrality.empty:
            comm_centrality["group"] = group_label
            all_comm_centrality.append(comm_centrality)
        if not comm_scores.empty:
            comm_scores["group"] = group_label
            all_comm_scores.append(comm_scores)
        all_polarized_top.extend(polarized_top)
        all_partitions[group_label] = partition

        # Save edges per group
        active_edges.to_csv(f"{OUTPUT_DIR}/reply_network_edges_{group_label}.csv", index=False)

    # ── Save outputs ──
    log.info(f"\n{'='*60}")
    log.info("Saving outputs...")
    log.info(f"{'='*60}")

    global_stats_df = pd.DataFrame(all_global_stats)
    global_stats_df.to_csv(f"{OUTPUT_DIR}/sna_global_stats.csv", index=False)
    log.info(f"  Saved → sna_global_stats.csv ({len(global_stats_df)} groups)")

    if all_comm_centrality:
        comm_centrality_df = pd.concat(all_comm_centrality, ignore_index=True)
        comm_centrality_df.to_csv(f"{OUTPUT_DIR}/sna_community_centrality.csv", index=False)
        log.info(f"  Saved → sna_community_centrality.csv ({len(comm_centrality_df)} nodes)")

    if all_comm_scores:
        comm_scores_df = pd.concat(all_comm_scores, ignore_index=True)
        comm_scores_df.to_csv(f"{OUTPUT_DIR}/sna_community_scores.csv", index=False)
        log.info(f"  Saved → sna_community_scores.csv ({len(comm_scores_df)} communities)")

    if all_polarized_top:
        polarized_df = pd.DataFrame(all_polarized_top)
        polarized_df.to_csv(f"{OUTPUT_DIR}/sna_polarized_top_nodes.csv", index=False)
        log.info(f"  Saved → sna_polarized_top_nodes.csv ({len(polarized_df)} entries)")

    log.info(f"\n=== SNA COMPLETE ({time.time()-t0:.1f}s) ===")


if __name__ == "__main__":
    main()
