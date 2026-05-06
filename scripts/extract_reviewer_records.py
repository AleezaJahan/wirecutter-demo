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
- "positives": array of brief pro points (array of strings, or empty [])
- "negatives": array of brief con points (array of strings, or empty [])
- "specific_use_case": if for a specific use case like "pet hair" or "mopping" (string or null)
- "date_reviewed": date or period of the review, e.g. "2025", "May 2025" (string or null)

CRITICAL RULES:
- Return ONLY the JSON array. No markdown. No explanation. No ```json fences.
- Extract ALL products, not just the top one.
- If you find 0 products, return an empty array: []
- Do NOT invent information. Use null for unknown fields.
- Even if some info is behind a paywall, return whatever product names you CAN see.
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

    print(f"    Got {len(records)} records from {source_name}")
    return records


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]
    product_type = cfg.get("product_type", category_id)
    sources = cfg["reviewer_sources"]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-key-here":
        print("ERROR: OPENAI_API_KEY is not set. Add it to .env")
        sys.exit(1)

    print("=" * 60)
    print(f"Script 1: Extracting reviewer records [{category_id}]")
    print("=" * 60)

    all_records = []
    for source in sources:
        records = extract_from_source(source, product_type)
        all_records.extend(records)

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

    out_path = data_dir / "reviewer_records.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(valid_records)} valid records ({len(error_records)} errors) to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
