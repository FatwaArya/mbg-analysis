#!/bin/bash

SSH_KEY="$HOME/.ssh/mbg_scraper_do_ed25519"
DROPLET_IP="159.223.94.187"
LOG_PATH="/opt/mbg/inference.log"

if [ "$1" == "watch" ]; then
  echo "Watching inference progress (Ctrl+C to exit)..."
  ssh -i "$SSH_KEY" root@"$DROPLET_IP" "tail -f $LOG_PATH"
else
  echo "=== MBG Inference Monitor ==="
  echo "Droplet: $DROPLET_IP"
  echo ""

  # Check if process is running
  echo "Checking process status..."
  ssh -i "$SSH_KEY" root@"$DROPLET_IP" "ps aux | grep '[i]nference.py'" || echo "Process not found"
  echo ""

  # Show latest log entries
  echo "=== Latest Progress ==="
  ssh -i "$SSH_KEY" root@"$DROPLET_IP" "tail -30 $LOG_PATH"
  echo ""

  # Check output files
  echo "=== Output Files ==="
  ssh -i "$SSH_KEY" root@"$DROPLET_IP" "ls -lh /opt/mbg/data/output/ 2>/dev/null || echo 'No output files yet'"
  echo ""
  echo "Run './scripts/monitor_inference.sh watch' to follow live progress"
fi
