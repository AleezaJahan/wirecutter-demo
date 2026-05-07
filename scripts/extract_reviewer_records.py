"""
Script 1: extract_reviewer_records.py

Turn selected reviewer pages into structured reviewer records.
Uses OpenAI Responses API with web_search tool.

Usage: python3 scripts/extract_reviewer_records.py --category robot_vacuum
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)
from openai import OpenAI
from config import get_category_config

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EXTRACTION_PROMPT_TEMPLATE = """You are a structured data extractor. You MUST return ONLY a valid JSON array.

Search the web as instructed and extract EVERY {product_type} product mentioned as a recommendation or pick.

Return a JSON array where each element has these fields:
- "raw_product_name": full product name exactly as the source lists it (string)
- "source_name": "{source_name}" (string)
- "source_url": the URL of the page you found this product on (string)
- "recommendation_type": the role/category/award, e.g. "Best Overall", "Top Tested", "Budget Pick", "#1 Ranked" (string or null)
- "positives": short card-style labels, max 8-10 words each. Examples:
  "5,500 Pa suction, highest in its class"
  "194-minute battery, covers 2,000 sq ft"
  "99% pet hair pickup on hardwood"
  BAD (too wordy): "Suction power measured at 5,500 Pa, which is the highest among mid-range models tested"
  BAD (too vague): "Good suction"
  (array of strings, or empty [])
- "positives_detail": same pros but as full sentences with context. Examples:
  "Suction power measured at 5,500 Pa, highest among mid-range models"
  "Battery lasted 194 minutes in continuous cleaning, enough for 2,000 sq ft"
  Keep the same order as "positives" so each index matches.
  (array of strings, or empty [])
- "negatives": short card-style labels, max 8-10 words each. Examples:
  "Misses small obstacles like cables and socks"
  "72 dB on max, louder than competitors"
  "App crashes during scheduled cleans"
  BAD (too wordy): "Obstacle avoidance missed small objects like cables and socks in testing according to the reviewer"
  BAD (too vague): "Can be loud"
  (array of strings, or empty [])
- "negatives_detail": same cons but as full sentences with context. Examples:
  "Obstacle avoidance missed small objects like cables and socks in testing"
  "Noise reaches 72 dB on max setting, louder than most competitors"
  Keep the same order as "negatives" so each index matches.
  (array of strings, or empty [])
- "endorsement_tier": classify the reviewer's intent for this product (string, REQUIRED, one of these three values):
    "top_pick" = the reviewer's #1 overall recommendation for this product category (their single best pick, editor's choice, or the product they'd tell everyone to buy)
    "strong_pick" = runner-up, "also great", best-in-a-specific-niche like "Best for Pets" or "Best Budget", or a #2-#3 ranked product
    "mention" = listed or recommended but NOT a top or standout pick (e.g. "Notable Mention", ranked #4+, "worth considering", included in a list without strong endorsement)
- "specific_use_case": if for a specific use case like "pet hair" or "mopping" (string or null)
- "date_reviewed": date or period of the review, e.g. "2025", "May 2025" (string or null)

CRITICAL RULES:
- Return ONLY the JSON array. No markdown. No explanation. No ```json fences.
- Extract ALL products, not just the top one.
- If you find 0 products, return an empty array: []
- Do NOT invent information. Use null for unknown fields.
- Even if some info is behind a paywall, return whatever product names you CAN see.
- For positives and negatives, always prefer the reviewer's specific language, numbers, and
  test results over generic summaries. If the reviewer says "scored 8.2 out of 10 for comfort",
  include that exact detail.
"""


def parse_json_from_text(text: str):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
    except json.JSONDecodeError:
        pass

    # Find the outermost [ ... ] by matching first [ to last ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def strip_citation_artifacts(text):
    """Remove markdown links, parenthesized URLs, and source-name citations left by web_search."""
    if not isinstance(text, str):
        return text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'\(https?://[^\)]+\)', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s*\(\s*[\w.-]+\.(com|org|net|ca|co\.uk)\s*\)\s*$', '', text)
    text = re.sub(r'\s*\(\s*[\w.-]+\.(com|org|net|ca|co\.uk)\s*\)', '', text)
    return text.strip()


def clean_record(record):
    """Strip citation artifacts from all string fields in a record."""
    for key in ("positives", "negatives"):
        if isinstance(record.get(key), list):
            record[key] = [strip_citation_artifacts(item) for item in record[key]]
            record[key] = [item for item in record[key] if item]
    for key in ("recommendation_type", "specific_use_case", "raw_product_name"):
        if isinstance(record.get(key), str):
            record[key] = strip_citation_artifacts(record[key])
    return record


def extract_from_source(source, product_type):
    source_name = source["source_name"]
    query = source["query"]
    prompt = EXTRACTION_PROMPT_TEMPLATE.replace("{source_name}", source_name).replace("{product_type}", product_type)

    print(f"  Extracting from {source_name}...")

    response = client.responses.create(
        model="o4-mini",
        instructions=prompt,
        input=query,
        tools=[{"type": "web_search", "search_context_size": "high"}],
    )

    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text

    records = parse_json_from_text(text)

    if records is None or len(records) == 0:
        print(f"    First attempt got 0 parsed records. Retrying...")
        retry_prompt = (
            f"I searched for {source_name} {product_type} recommendations but got no structured results. "
            f"Please try again: {query}\n\n"
            "You MUST return a JSON array of products. Even if you only find product names, return them."
        )
        response = client.responses.create(
            model="o4-mini",
            instructions=prompt,
            input=retry_prompt,
            tools=[{"type": "web_search", "search_context_size": "high"}],
        )
        text = ""
        for item in response.output:
            if hasattr(item, "content") and item.content is not None:
                for block in item.content:
                    if hasattr(block, "text"):
                        text += block.text

        records = parse_json_from_text(text)

    if records is None:
        print(f"    WARNING: Could not parse JSON from {source_name}.")
        records = [{"_raw_text": text[:2000], "source_name": source_name, "_parse_error": True}]

    records = [clean_record(r) for r in records]
    print(f"    Got {len(records)} records from {source_name}")
    return records


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]
    product_type = cfg.get("product_type", category_id)
    sources = cfg["reviewer_sources"]

    skip_if_exists = "--skip-if-exists" in sys.argv
    out_path = data_dir / "reviewer_records.json"

    if skip_if_exists and out_path.exists():
        print(f"  [skip] {out_path} already exists. Use without --skip-if-exists to re-extract.")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-key-here":
        print("ERROR: OPENAI_API_KEY is not set. Add it to .env")
        sys.exit(1)

    print("=" * 60)
    print(f"Script 1: Extracting reviewer records [{category_id}]")
    print("=" * 60)

    all_records = []
    max_workers = min(len(sources), 6)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_from_source, source, product_type): i
            for i, source in enumerate(sources)
        }
        results_by_idx = {}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results_by_idx[idx] = future.result()
            except Exception as e:
                print(f"  ERROR extracting source {sources[idx]['source_name']}: {e}")
                results_by_idx[idx] = []
        for i in range(len(sources)):
            all_records.extend(results_by_idx.get(i, []))

    valid_records = [r for r in all_records if not r.get("_parse_error")]
    error_records = [r for r in all_records if r.get("_parse_error")]

    output = {
        "metadata": {
            "category": category_id,
            "total_records": len(valid_records),
            "parse_errors": len(error_records),
            "sources": [s["source_name"] for s in sources],
        },
        "records": valid_records,
        "errors": error_records,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(valid_records)} valid records ({len(error_records)} errors) to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
