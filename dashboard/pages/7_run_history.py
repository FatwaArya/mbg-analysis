import streamlit as st
import pandas as pd
import subprocess
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Run History  MBG", page_icon=None, layout="wide")
require_auth()

BUCKET = "s3://mbg-scraper-network-20260419071440"

st.title("Pipeline Run History")
st.caption("View all historical pipeline runs and their metadata")
st.markdown("---")

@st.cache_data(ttl=60)
def list_runs():
    """List all runs from Spaces"""
    try:
        cmd = ["s3cmd", "ls", f"{BUCKET}/runs/"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return []
        
        # Parse output: DIR s3://bucket/runs/20260430_174500/
        runs = []
        for line in result.stdout.strip().split('\n'):
            if 'DIR' in line and '/runs/' in line:
                run_id = line.split('/runs/')[-1].strip('/')
                if run_id:
                    runs.append(run_id)
        
        return sorted(runs, reverse=True)
    except:
        return []

@st.cache_data(ttl=300)
def fetch_run_metadata(run_id):
    """Fetch metadata for a specific run"""
    try:
        cmd = ["s3cmd", "get", f"{BUCKET}/runs/{run_id}/metadata.json", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return None

# List all runs
runs = list_runs()

if not runs:
    st.warning("No runs found in Spaces, or unable to connect.")
    st.stop()

st.success(f"Found {len(runs)} pipeline runs")

# Build metadata table
run_data = []
for run_id in runs:
    metadata = fetch_run_metadata(run_id)
    if metadata:
        stats = metadata.get("stats", {})
        sentiment = stats.get("sentiment", {})
        total = stats.get("total_tweets", 0)
        
        run_data.append({
            "Run ID": run_id,
            "Timestamp": metadata.get("timestamp", "")[:16],
            "Duration": f"{metadata.get('duration_seconds', 0)//60}m",
            "Tweets": f"{total:,}",
            "Negative %": f"{sentiment.get('negative', 0)/total*100:.1f}%" if total > 0 else "N/A",
            "Positive %": f"{sentiment.get('positive', 0)/total*100:.1f}%" if total > 0 else "N/A",
            "Topics": stats.get("topics_discovered", 0),
            "Git": metadata.get("git_commit", "")[:7],
            "Status": metadata.get("status", "unknown")
        })
    else:
        run_data.append({
            "Run ID": run_id,
            "Timestamp": "N/A",
            "Duration": "N/A",
            "Tweets": "N/A",
            "Negative %": "N/A",
            "Positive %": "N/A",
            "Topics": "N/A",
            "Git": "N/A",
            "Status": "unknown"
        })

df = pd.DataFrame(run_data)

# Display table
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")

# Run selector for detailed view
st.markdown("### View Run Details")
selected_run = st.selectbox("Select a run to view details:", runs)

if selected_run:
    metadata = fetch_run_metadata(selected_run)
    
    if metadata:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Run Information")
            st.json({
                "run_id": metadata["run_id"],
                "timestamp": metadata["timestamp"],
                "duration_seconds": metadata["duration_seconds"],
                "git_commit": metadata["git_commit"],
                "status": metadata["status"]
            })
        
        with col2:
            st.markdown("#### Statistics")
            st.json(metadata.get("stats", {}))
        
        st.markdown("#### Files")
        files_df = []
        for name, info in metadata.get("files", {}).items():
            files_df.append({
                "Dataset": name,
                "Rows": f"{info['rows']:,}",
                "Size (MB)": info['size_mb'],
                "MD5": info['md5'],
                "Path": info['path']
            })
        
        if files_df:
            st.dataframe(pd.DataFrame(files_df), use_container_width=True, hide_index=True)
        
        # Download links
        st.markdown("#### Download Files")
        for name, info in metadata.get("files", {}).items():
            filename = info['path'].split('/')[-1]
            st.code(f"s3cmd get {BUCKET}/{info['path']} {filename}", language="bash")
    else:
        st.error(f"Could not load metadata for run {selected_run}")
