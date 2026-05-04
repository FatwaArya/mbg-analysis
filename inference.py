#!/usr/bin/env python3
"""
MBG Relevance Filtering Inference Script

This script loads a fine-tuned IndoBERT model and filters a corpus of tweets
about Indonesia's Makan Bergizi Gratis (MBG) program, classifying each tweet
as RELEVANT or NOT_RELEVANT.

Usage:
    python inference.py

Environment:
    - Runtime config: runtime.py (RUNTIME_MODE=droplet|colab)
    - Model path and data paths come from shared runtime config

Output Files:
    - tweets_relevant.csv: Tweets classified as RELEVANT
    - tweets_rejected.csv: Tweets classified as NOT_RELEVANT
    - tweets_borderline.csv: Low-confidence predictions (< 0.80)

Author: MBG Analysis Team
Date: 2026-04-28
"""

import os
import glob
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from runtime import RUNTIME

# ── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH = RUNTIME.model_dir  # FIX: centralize runtime model path.
DATA_DIR = RUNTIME.raw_dir  # FIX: centralize runtime input path.
OUTPUT_DIR = RUNTIME.output_dir  # FIX: centralize runtime output path.
BATCH_SIZE = RUNTIME.inference_batch_size  # FIX: runtime-specific batch size.
MAX_LENGTH = 128  # Maximum token length for BERT input

# ── Setup ────────────────────────────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Label mapping from model output
id2label = {0: "NOT_RELEVANT", 1: "RELEVANT"}


def load_model():
    """
    Load the fine-tuned IndoBERT model and tokenizer.
    
    Returns:
        tuple: (tokenizer, model) ready for inference
    """
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.to(RUNTIME.device)  # FIX: move model to selected runtime device.
    model.eval()  # Set to evaluation mode (disables dropout)
    return tokenizer, model


def predict_batch(texts: list[str], tokenizer, model) -> list[dict]:
    """
    Run batch inference on a list of tweet texts.
    
    Args:
        texts: List of tweet text strings
        tokenizer: Loaded tokenizer
        model: Loaded classification model
        
    Returns:
        List of dicts with keys:
            - predicted_label: "RELEVANT" or "NOT_RELEVANT"
            - predicted_confidence: Float between 0 and 1
    """
    # Tokenize input texts
    inputs = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
        return_tensors="pt"
    )
    # FIX: move tokenized tensors to selected runtime device for GPU inference.
    inputs = {k: v.to(RUNTIME.device) for k, v in inputs.items()}
    
    # Run inference without gradient computation (faster)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)
        preds = torch.argmax(probs, dim=-1).cpu().tolist()
        scores = probs.max(dim=-1).values.cpu().tolist()
    
    # Format results
    return [
        {
            "predicted_label": id2label[p],
            "predicted_confidence": round(s, 4)
        }
        for p, s in zip(preds, scores)
    ]


def find_corpus_csv() -> str:
    """
    Find the main corpus CSV file in the data directory.
    
    Returns:
        str: Path to the largest CSV file (assumed to be the main corpus)
        
    Raises:
        FileNotFoundError: If no CSV files found
    """
    csv_files = glob.glob(f"{DATA_DIR}/*.csv")
    if not csv_files:
        raise FileNotFoundError(f"No CSV found in {DATA_DIR}")
    
    # Use largest CSV as main corpus
    corpus_path = max(csv_files, key=os.path.getsize)
    print(f"Loading corpus: {corpus_path}")
    return corpus_path


def load_corpus(corpus_path: str) -> pd.DataFrame:
    """
    Load and prepare the tweet corpus for inference.
    
    Args:
        corpus_path: Path to the CSV file
        
    Returns:
        DataFrame with cleaned data ready for inference
    """
    df = pd.read_csv(corpus_path, low_memory=False)
    print(f"Total tweets: {len(df):,}")
    
    # Identify text column (usually named "text" or second column)
    text_col = "text" if "text" in df.columns else df.columns[1]
    
    # Remove rows with missing text
    df = df.dropna(subset=[text_col])
    df = df.reset_index(drop=True)
    
    print(f"After removing nulls: {len(df):,}")
    return df, text_col


def run_inference(df: pd.DataFrame, text_col: str, tokenizer, model) -> pd.DataFrame:
    """
    Run batch inference on the entire corpus.
    
    Args:
        df: DataFrame containing tweets
        text_col: Name of the column containing tweet text
        tokenizer: Loaded tokenizer
        model: Loaded model
        
    Returns:
        DataFrame with added columns: predicted_label, predicted_confidence
    """
    print(f"Running inference (batch_size={BATCH_SIZE})...")
    all_results = []
    
    # Process in batches for memory efficiency
    for i in tqdm(range(0, len(df), BATCH_SIZE)):
        batch_texts = df[text_col].iloc[i:i+BATCH_SIZE].tolist()
        results = predict_batch(batch_texts, tokenizer, model)
        all_results.extend(results)
    
    # Add predictions to dataframe
    results_df = pd.DataFrame(all_results)
    df = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    
    return df


def save_results(df: pd.DataFrame):
    """
    Split and save results into separate files.
    
    Args:
        df: DataFrame with predictions
        
    Saves three CSV files:
        - tweets_relevant.csv: RELEVANT tweets
        - tweets_rejected.csv: NOT_RELEVANT tweets
        - tweets_borderline.csv: Low confidence predictions
    """
    # Split by prediction
    relevant = df[df["predicted_label"] == "RELEVANT"]
    rejected = df[df["predicted_label"] == "NOT_RELEVANT"]
    
    # Identify borderline cases (low confidence)
    borderline = df[df["predicted_confidence"] < 0.80]
    
    # Save to files
    relevant.to_csv(f"{OUTPUT_DIR}/tweets_relevant.csv", index=False)
    rejected.to_csv(f"{OUTPUT_DIR}/tweets_rejected.csv", index=False)
    borderline.to_csv(f"{OUTPUT_DIR}/tweets_borderline.csv", index=False)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"RELEVANT   : {len(relevant):,} ({len(relevant)/len(df)*100:.1f}%)")
    print(f"REJECTED   : {len(rejected):,} ({len(rejected)/len(df)*100:.1f}%)")
    print(f"BORDERLINE : {len(borderline):,} (confidence < 0.80)")
    print(f"Output     : {OUTPUT_DIR}")
    print(f"{'='*50}")


def main():
    """Main execution flow."""
    # Load model
    tokenizer, model = load_model()
    
    # Load corpus
    corpus_path = find_corpus_csv()
    df, text_col = load_corpus(corpus_path)
    
    # Run inference
    df = run_inference(df, text_col, tokenizer, model)
    
    # Save results
    save_results(df)


if __name__ == "__main__":
    main()
