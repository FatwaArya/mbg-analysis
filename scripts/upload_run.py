#!/usr/bin/env python3
import json
import subprocess
import sys
import os
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # FIX: allow importing runtime from repo root.
from runtime import RUNTIME

BUCKET = "s3://mbg-scraper-network-20260419071440"
DATA_DIR = RUNTIME.data_dir  # FIX: centralize runtime data path.
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def run_s3cmd(args, retry=True):
    """Execute s3cmd command with retry logic"""
    for attempt in range(MAX_RETRIES if retry else 1):
        try:
            cmd = ["s3cmd"] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return result.stdout
            
            # If not last attempt, retry
            if retry and attempt < MAX_RETRIES - 1:
                print(f"    Retry {attempt + 1}/{MAX_RETRIES - 1} after {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise Exception(f"s3cmd failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            if retry and attempt < MAX_RETRIES - 1:
                print(f"    Timeout, retry {attempt + 1}/{MAX_RETRIES - 1}...")
                time.sleep(RETRY_DELAY)
            else:
                raise Exception("s3cmd timeout")
        except Exception as e:
            if retry and attempt < MAX_RETRIES - 1:
                print(f"    Error: {e}, retry {attempt + 1}/{MAX_RETRIES - 1}...")
                time.sleep(RETRY_DELAY)
            else:
                raise
    
    raise Exception("Upload failed after all retries")

def upload_file(local_path, remote_path):
    """Upload file to Spaces with retry and verification"""
    print(f"  Uploading {os.path.basename(local_path)}...")
    run_s3cmd(["put", local_path, f"{BUCKET}/{remote_path}"])
    print(f"    ✓ {remote_path}")

def cleanup_partial_upload(run_id):
    """Clean up partial upload on failure"""
    try:
        print(f"  Cleaning up partial upload for {run_id}...")
        run_s3cmd(["del", "--recursive", f"{BUCKET}/runs/{run_id}/"], retry=False)
        print("    ✓ Cleanup complete")
    except:
        print("    ⚠ Cleanup failed (may need manual cleanup)")

def upload_run():
    """Upload timestamped run to Spaces"""
    
    # Read metadata
    metadata_path = f"{DATA_DIR}/output/metadata.json"
    if not os.path.exists(metadata_path):
        print("✗ metadata.json not found. Run generate_manifest.py first.")
        sys.exit(1)
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    run_id = metadata["run_id"]
    print(f"Uploading run: {run_id}")
    
    uploaded_files = []
    
    try:
        # Upload data files
        for file_key, file_info in metadata["files"].items():
            filename = file_info["path"].split("/")[-1]
            local_path = f"{DATA_DIR}/output/{filename}"
            remote_path = f"runs/{run_id}/{filename}"
            
            if os.path.exists(local_path):
                upload_file(local_path, remote_path)
                uploaded_files.append(remote_path)
            else:
                print(f"  ⚠ Skipping {filename} (not found)")
        
        # Upload metadata
        upload_file(metadata_path, f"runs/{run_id}/metadata.json")
        uploaded_files.append(f"runs/{run_id}/metadata.json")
        
        # Generate and upload latest_run.json manifest
        latest_manifest = {
            "run_id": run_id,
            "timestamp": metadata["timestamp"],
            "git_commit": metadata["git_commit"],
            "duration_seconds": metadata["duration_seconds"],
            "status": metadata["status"],
            "files": metadata["files"],
            "stats": metadata["stats"]
        }
        
        latest_path = f"{DATA_DIR}/output/latest_run.json"
        with open(latest_path, 'w') as f:
            json.dump(latest_manifest, f, indent=2)
        
        upload_file(latest_path, "latest_run.json")
        
        print(f"✓ Upload complete: {BUCKET}/runs/{run_id}/")
        print(f"  Files: {len(metadata['files'])}")
        print(f"  Total tweets: {metadata['stats'].get('total_tweets', 0):,}")
        
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        cleanup_partial_upload(run_id)
        sys.exit(1)

if __name__ == "__main__":
    try:
        upload_run()
    except KeyboardInterrupt:
        print("\n✗ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        sys.exit(1)
