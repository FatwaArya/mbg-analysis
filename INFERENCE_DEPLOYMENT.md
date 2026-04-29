# MBG IndoBERT Inference Deployment

## Overview

This document describes the deployment of a DigitalOcean droplet for running batch inference on 124k tweets about Indonesia's Makan Bergizi Gratis (MBG) program using a fine-tuned IndoBERT model.

## Infrastructure

### Droplet Specifications
- **Name**: mbg-inference
- **Region**: sgp1 (Singapore)
- **Size**: s-4vcpu-8gb (4 vCPUs, 8GB RAM, 160GB disk)
- **OS**: Ubuntu 22.04 LTS
- **Cost**: ~$48/month (prorated for actual usage)

### Directory Structure
```
/opt/mbg/
├── model/              # Fine-tuned IndoBERT model files
├── data/
│   ├── raw/           # Input tweet corpus CSV
│   └── output/        # Filtered results
├── scripts/           # Inference script
└── venv/             # Python virtual environment
```

## Data Sources

### Model
- **Location**: `s3://mbg-scraper-network-20260419071440/models/mbg-indobert-finetuned/`
- **Type**: BertForSequenceClassification (IndoBERT fine-tuned)
- **Task**: Binary classification (RELEVANT vs NOT_RELEVANT)

### Dataset
- **Location**: `s3://mbg-scraper-network-20260419071440/data/`
- **Size**: ~124,000 tweets
- **Content**: Indonesian tweets about MBG program

## Inference Script

### Purpose
The `inference.py` script classifies tweets as RELEVANT or NOT_RELEVANT to the MBG program.

### Key Features
- **Batch Processing**: Processes 64 tweets at a time for efficiency
- **Memory Efficient**: Streams data to handle large datasets
- **Progress Tracking**: Uses tqdm for real-time progress monitoring
- **Confidence Scoring**: Provides prediction confidence for each tweet

### Output Files
1. **tweets_relevant.csv**: Tweets classified as RELEVANT
2. **tweets_rejected.csv**: Tweets classified as NOT_RELEVANT
3. **tweets_borderline.csv**: Low-confidence predictions (< 0.80 confidence)

### Performance
- **Expected Runtime**: 45-90 minutes on 4vCPU droplet
- **Throughput**: ~1,500-2,500 tweets/minute

## Deployment Steps

### 1. Infrastructure Setup
```bash
# Create droplet
doctl compute droplet create mbg-inference \
  --region sgp1 \
  --size s-4vcpu-8gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys <SSH_KEY_ID> \
  --wait
```

### 2. Bootstrap Environment
```bash
# Install system dependencies
apt-get update && apt-get install -y python3-pip python3-venv awscli unzip

# Create project structure
mkdir -p /opt/mbg/{model,data/raw,data/output,scripts}

# Setup Python environment
python3 -m venv /opt/mbg/venv
source /opt/mbg/venv/bin/activate
pip install transformers torch pandas tqdm
```

### 3. Download Data
```bash
# Configure DO Spaces access
aws configure set aws_access_key_id $DO_SPACES_KEY
aws configure set aws_secret_access_key $DO_SPACES_SECRET

# Download model and data
ENDPOINT="https://sgp1.digitaloceanspaces.com"
BUCKET="mbg-scraper-network-20260419071440"

aws s3 cp s3://$BUCKET/models/mbg-indobert-finetuned/ /opt/mbg/model/ \
  --recursive --endpoint-url $ENDPOINT

aws s3 cp s3://$BUCKET/data/ /opt/mbg/data/raw/ \
  --recursive --endpoint-url $ENDPOINT
```

### 4. Run Inference
```bash
# Upload inference script
scp inference.py root@<DROPLET_IP>:/opt/mbg/scripts/

# Run in background
ssh root@<DROPLET_IP>
source /opt/mbg/venv/bin/activate
nohup python /opt/mbg/scripts/inference.py > /opt/mbg/inference.log 2>&1 &

# Monitor progress
tail -f /opt/mbg/inference.log
```

### 5. Upload Results
```bash
# Upload filtered results back to Spaces
aws s3 cp /opt/mbg/data/output/ s3://$BUCKET/output/ \
  --recursive --endpoint-url $ENDPOINT
```

### 6. Cleanup
```bash
# Destroy droplet to stop billing
doctl compute droplet delete mbg-inference --force
```

## Monitoring

### Check Process Status
```bash
ssh root@<DROPLET_IP> "ps aux | grep inference.py"
```

### View Logs
```bash
ssh root@<DROPLET_IP> "tail -f /opt/mbg/inference.log"
```

### Check Disk Usage
```bash
ssh root@<DROPLET_IP> "df -h /opt/mbg"
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| SSH connection refused | Wait 60s after droplet creation |
| Spaces access denied | Verify DO_SPACES_KEY and DO_SPACES_SECRET |
| OOM killed | Upgrade to s-8vcpu-16gb size |
| No CSV found | Verify Spaces bucket path |
| Model loading error | Ensure all model files downloaded |

### Error Recovery
If inference fails mid-run, the script can be modified to resume from a checkpoint by adding offset logic to skip already-processed batches.

## Cost Estimation

- **Droplet**: $0.071/hour × ~2 hours = ~$0.14
- **Spaces Storage**: Negligible (existing data)
- **Spaces Transfer**: Free (same region)
- **Total**: ~$0.14 for one-time inference run

## Security Notes

- SSH access restricted to authorized keys only
- DO Spaces credentials stored in environment variables (not committed)
- Droplet destroyed after use to minimize exposure
- All data transfer within sgp1 region (no external egress)

## Next Steps

After inference completes:
1. Download results from Spaces
2. Analyze RELEVANT tweets for insights
3. Review BORDERLINE cases for model improvement
4. Destroy droplet to stop billing
5. Archive results for future reference
