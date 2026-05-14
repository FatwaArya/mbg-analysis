#!/bin/bash
# Start full reply pipeline on VPS
# Run this from local machine

set -e

VPS="root@206.189.157.179"
KEY="~/.ssh/mbg_scraper_do_ed25519"

echo "=== MBG Reply Pipeline - Full Dataset ==="
echo "This will process 509k replies (~5-6 hours)"
echo ""

# Check if full dataset already exists on VPS
echo "[1/4] Checking if dataset exists on VPS..."
EXISTS=$(ssh -i "$KEY" "$VPS" "test -f /opt/mbg/data/consolidated/replies_all_dedup.jsonl && echo 'yes' || echo 'no'")

if [ "$EXISTS" = "no" ]; then
    echo "[2/4] Downloading full dataset from DO Spaces to VPS..."
    ssh -i "$KEY" "$VPS" "s3cmd get s3://mbg-scraper-network-20260419071440/replies_all_dedup.jsonl /opt/mbg/data/consolidated/replies_all_dedup.jsonl"
    echo "✓ Downloaded (276MB)"
else
    echo "✓ Dataset already exists on VPS"
fi

echo "[3/4] Starting pipeline in screen session..."
ssh -i "$KEY" "$VPS" "screen -dmS reply_pipeline bash -c 'cd /opt/mbg && ./scripts/replies/run_reply_pipeline.sh data/consolidated/replies_all_dedup.jsonl'"
echo "✓ Pipeline started in screen session 'reply_pipeline'"

echo "[4/4] Setup complete!"
echo ""
echo "Monitor progress:"
echo "  ssh -i $KEY $VPS 'tail -f /opt/mbg/logs/reply_pipeline_*.log'"
echo ""
echo "Reattach to screen:"
echo "  ssh -i $KEY $VPS"
echo "  screen -r reply_pipeline"
echo ""
echo "Expected completion: ~5-6 hours"
