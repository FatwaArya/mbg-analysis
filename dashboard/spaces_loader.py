"""
Spaces Data Loader - Fetch pipeline data from DigitalOcean Spaces with local fallback
"""
import json
import subprocess
import pandas as pd
import streamlit as st
from pathlib import Path
import tempfile
import os

BUCKET = "s3://mbg-scraper-network-20260419071440"
LOCAL_DATA = "/opt/mbg/data"
CACHE_DIR = "/tmp/mbg_spaces_cache"

def run_s3cmd(args):
    """Execute s3cmd command"""
    try:
        cmd = ["s3cmd"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        return result.stdout
    except:
        return None

@st.cache_data(ttl=300)
def fetch_latest_manifest():
    """Fetch latest_run.json from Spaces"""
    try:
        output = run_s3cmd(["get", f"{BUCKET}/latest_run.json", "-"])
        if output:
            return json.loads(output)
    except:
        pass
    return None

def download_csv_from_spaces(remote_path):
    """Download CSV from Spaces to memory"""
    try:
        output = run_s3cmd(["get", f"{BUCKET}/{remote_path}", "-"])
        if output:
            from io import StringIO
            return pd.read_csv(StringIO(output))
    except:
        pass
    return None

@st.cache_data(ttl=600)
def load_with_fallback(dataset_name):
    """
    Load dataset with Spaces → Local fallback
    
    Args:
        dataset_name: One of 'tweets_with_sentiment', 'tweets_with_topics', 'topic_info'
    
    Returns:
        tuple: (dataframe, source, run_info)
        source: 'spaces', 'local', or 'error'
        run_info: dict with run_id, timestamp, etc. (None if local)
    """
    
    # Map dataset names to filenames
    filename_map = {
        "tweets_with_sentiment": "tweets_with_sentiment.csv",
        "tweets_with_topics": "tweets_with_topics.csv",
        "topic_info": "topic_info.csv"
    }
    
    if dataset_name not in filename_map:
        return None, "error", None
    
    filename = filename_map[dataset_name]
    
    # Try Spaces first
    spaces_error = None
    try:
        manifest = fetch_latest_manifest()
        if manifest:
            file_info = manifest["files"].get(dataset_name)
            if file_info:
                remote_path = file_info["path"]
                df = download_csv_from_spaces(remote_path)
                if df is not None:
                    run_info = {
                        "run_id": manifest["run_id"],
                        "timestamp": manifest["timestamp"],
                        "git_commit": manifest.get("git_commit", "unknown"),
                        "duration_seconds": manifest.get("duration_seconds", 0),
                        "stats": manifest.get("stats", {})
                    }
                    return df, "spaces", run_info
                else:
                    spaces_error = "Failed to download CSV from Spaces"
            else:
                spaces_error = f"Dataset {dataset_name} not found in manifest"
        else:
            spaces_error = "Could not fetch latest_run.json from Spaces"
    except Exception as e:
        spaces_error = f"Spaces error: {str(e)}"
    
    # Fallback to local files
    local_path = f"{LOCAL_DATA}/output/{filename}"
    if os.path.exists(local_path):
        try:
            df = pd.read_csv(local_path)
            # Show warning about fallback
            if spaces_error:
                st.warning(f"⚠️ Using local files (Spaces unavailable: {spaces_error})")
            return df, "local", None
        except Exception as e:
            st.error(f"❌ Failed to load local file: {e}")
    else:
        st.error(f"❌ Data not available in Spaces or locally. Spaces error: {spaces_error}")
    
    return None, "error", None

def get_connection_status():
    """Check Spaces connectivity and return status"""
    manifest = fetch_latest_manifest()
    if manifest:
        return "spaces", manifest
    
    # Check if local files exist
    if os.path.exists(f"{LOCAL_DATA}/output/tweets_with_sentiment.csv"):
        return "local", None
    
    return "offline", None

def format_run_info(run_info):
    """Format run info for display"""
    if not run_info:
        return "Local files (no run info)"
    
    from datetime import datetime
    try:
        ts = datetime.fromisoformat(run_info["timestamp"])
        ts_str = ts.strftime("%Y-%m-%d %H:%M")
    except:
        ts_str = run_info["timestamp"]
    
    duration = run_info.get("duration_seconds", 0)
    duration_str = f"{duration//60}m {duration%60}s" if duration > 0 else "unknown"
    
    return f"""
**Run ID:** `{run_info['run_id']}`  
**Timestamp:** {ts_str}  
**Duration:** {duration_str}  
**Git:** `{run_info.get('git_commit', 'unknown')}`
"""
