import json
import os
import time

import anthropic
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(".env")

API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not API_KEY or API_KEY == "your_api_key_here":
    raise ValueError("ANTHROPIC_API_KEY is missing in .env")

base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()
if not base_url or base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost"):
    base_url = "https://api.anthropic.com"

client = anthropic.Anthropic(api_key=API_KEY, base_url=base_url)

# This is the same for every request — will be cached after first call
SYSTEM_PROMPT = """You are an expert annotator for an academic public health
research project studying public discourse about Indonesia's Makan Bergizi
Gratis (MBG) program.

The MBG program is a government-funded free nutritious school meal initiative
launched in 2025, managed by Badan Gizi Nasional (BGN). It provides free
meals to students across Indonesian schools.

Your task is to label each tweet as RELEVANT or NOT_RELEVANT based on whether
it genuinely discusses the MBG program.

RELEVANT tweets discuss any of:
- Food quality, taste, nutrition, or portion size of MBG meals
- Distribution logistics, school coverage, delivery schedule
- Government policy, budget allocation, program implementation
- Student, parent, or teacher reactions and experiences
- Criticism or praise directed at the program
- Comparisons of MBG to other programs or to before the program
- International or media coverage of the MBG program
- Corruption, misuse, or accountability concerns about MBG
- Program expansion, changes, or announcements

NOT_RELEVANT tweets include:
- Use of "MBG" or "BGN" to mean a completely different organization or product
- Tweets mentioning the keyword only in passing with no MBG program context
- Spam, promotional, or bot-generated content
- Tweets about food, nutrition, or school in general with no MBG connection
- Tweets where the keyword appears in an unrelated sentence

IMPORTANT RULES:
- English tweets CAN be relevant if they discuss MBG in context
- Sarcasm or criticism of MBG is still RELEVANT — it is genuine discourse
- Short tweets can be relevant if the context is clear
- When genuinely uncertain, label as RELEVANT to avoid false negatives
- Respond ONLY with valid JSON, no other text

Response format:
{
  "label": "RELEVANT" or "NOT_RELEVANT",
  "confidence": "high", "medium", or "low",
  "reason": "one sentence explaining your decision"
}"""

MODEL = "claude-haiku-4-5-20251001"
POLL_SECONDS = 10
BATCH_ID_PATH = "data/processed/haiku_batch_id.txt"


def default_result(tweet_id: str, reason: str, error: str, raw_response: str = "") -> dict:
    return {
        "tweet_id": tweet_id,
        "label": "RELEVANT",
        "confidence": "low",
        "reason": reason,
        "raw_response": raw_response,
        "error": error,
    }


def build_requests(df: pd.DataFrame) -> tuple[list[dict], dict[str, str]]:
    requests = []
    id_map: dict[str, str] = {}
    for i, row in df.iterrows():
        custom_id = f"tweet_{i}"
        id_map[custom_id] = str(row["id"])
        requests.append(
            {
                "custom_id": custom_id,
                "params": {
                    "model": MODEL,
                    "max_tokens": 150,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Annotate this tweet:\n\n{str(row['text'])[:512]}",
                        }
                    ],
                },
            }
        )
    return requests, id_map


def poll_batch(batch_id: str, total: int):
    with tqdm(total=total, desc="Batch progress", unit="tweet") as pbar:
        while True:
            batch = client.beta.messages.batches.retrieve(batch_id)
            counts = batch.request_counts
            done = counts.succeeded + counts.errored + counts.canceled + counts.expired
            pbar.n = done
            pbar.set_postfix(
                succeeded=counts.succeeded,
                processing=counts.processing,
                errored=counts.errored,
            )
            pbar.refresh()

            if batch.processing_status == "ended":
                break
            time.sleep(POLL_SECONDS)
    return batch


def extract_text_content(message) -> str:
    parts = []
    for block in message.content:
        if getattr(block, "type", "") == "text":
            parts.append(getattr(block, "text", ""))
    return "\n".join(parts).strip()


def parse_annotation_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def parse_batch_results(batch_id: str, total: int, id_map: dict[str, str]) -> list[dict]:
    results = []
    stream = client.beta.messages.batches.results(batch_id)

    for item in tqdm(stream, total=total, desc="Reading batch results", unit="tweet"):
        tweet_id = id_map.get(str(item.custom_id), str(item.custom_id))
        result_type = item.result.type

        if result_type == "succeeded":
            raw = extract_text_content(item.result.message)
            try:
                parsed = parse_annotation_json(raw)
                parsed["tweet_id"] = tweet_id
                parsed["raw_response"] = raw
                parsed["error"] = None
                results.append(parsed)
            except json.JSONDecodeError:
                results.append(
                    default_result(
                        tweet_id,
                        "parse error — defaulting to RELEVANT",
                        "json_parse_error",
                        raw,
                    )
                )
        else:
            error_msg = (
                item.result.error.message if hasattr(item.result, "error") else f"batch_{result_type}"
            )
            results.append(
                default_result(
                    tweet_id,
                    "api error — defaulting to RELEVANT",
                    error_msg,
                )
            )
    return results


def main():
    df = pd.read_csv("data/processed/tweets_sample_10k.csv")
    df["id"] = df["id"].astype(str)
    print(f"Submitting {len(df)} tweets to Claude Haiku Batch API...\n")

    requests, id_map = build_requests(df)

    batch_id = None
    if os.path.exists(BATCH_ID_PATH):
        with open(BATCH_ID_PATH, "r", encoding="utf-8") as f:
            existing_batch_id = f.read().strip()
        if existing_batch_id:
            batch_id = existing_batch_id
            print(f"Reusing existing batch: {batch_id}")

    if not batch_id:
        batch = client.beta.messages.batches.create(requests=requests)
        batch_id = batch.id
        with open(BATCH_ID_PATH, "w", encoding="utf-8") as f:
            f.write(batch_id + "\n")
        print(f"Batch created: {batch_id}")

    final_batch = poll_batch(batch_id, len(df))
    counts = final_batch.request_counts
    print(
        f"Batch ended. succeeded={counts.succeeded}, errored={counts.errored}, "
        f"canceled={counts.canceled}, expired={counts.expired}"
    )

    results = parse_batch_results(batch_id, len(df), id_map)
    errors = sum(1 for r in results if r["error"])

    # Merge results back to original dataframe
    results_df = pd.DataFrame(results)
    results_df["tweet_id"] = results_df["tweet_id"].astype(str)
    df = df.merge(results_df, left_on="id", right_on="tweet_id", how="left")

    # Save full annotated sample
    df.to_csv("data/processed/tweets_annotated_haiku.csv", index=False)

    # Split into confidence buckets for human review
    high_conf = df[df["confidence"] == "high"]
    medium_conf = df[df["confidence"] == "medium"]
    low_conf = df[df["confidence"] == "low"]

    # Save review queues
    # High confidence — only save 10% random sample for spot check
    if len(high_conf) > 0:
        high_conf.sample(frac=0.10, random_state=42).to_csv(
            "data/processed/review_high_confidence_spotcheck.csv", index=False
        )
    else:
        high_conf.to_csv("data/processed/review_high_confidence_spotcheck.csv", index=False)
    medium_conf.to_csv("data/processed/review_medium_confidence.csv", index=False)
    low_conf.to_csv("data/processed/review_low_confidence.csv", index=False)

    # Print report
    print("\n" + "=" * 60)
    print("HAIKU ANNOTATION COMPLETE")
    print("=" * 60)
    print(f"Total annotated      : {len(df)}")
    print(f"Errors               : {errors}")
    print()
    print("Label breakdown:")
    print(df["label"].value_counts().to_string())
    print()
    print("Confidence breakdown:")
    print(df["confidence"].value_counts().to_string())
    print()
    print("Review queue sizes:")
    high_spotcheck_size = int(round(len(high_conf) * 0.10))
    print(f"  High conf spotcheck : {high_spotcheck_size} tweets")
    print(f"  Medium conf review  : {len(medium_conf)} tweets (review all)")
    print(f"  Low conf review     : {len(low_conf)} tweets (review all)")
    print()
    print("Estimated review workload:")
    review_total = len(medium_conf) + len(low_conf) + len(high_conf) * 0.10
    print(f"  ~{int(review_total)} tweets to manually review")
    print(f"  At 30 sec/tweet -> ~{int(review_total * 30 / 3600)} hours")
    print("=" * 60)


if __name__ == "__main__":
    main()
