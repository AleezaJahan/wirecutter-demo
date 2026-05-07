"""
Script 2: canonicalize_products.py

Turn messy reviewer product names into canonical product identities.
Uses OpenAI API for name cleaning (NO web search).

Usage: python3 scripts/canonicalize_products.py --category robot_vacuum
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

CANONICALIZE_PROMPT_TEMPLATE = """You are a product data cleaner. Given a list of raw product names for {product_type_plural}, your job is to:

1. Clean up each name (fix typos, normalize formatting)
2. Infer the brand and model for each
3. Group identical products that appear under different names into one canonical entry

Return a JSON object with two fields:

"canonical_products": an array of objects, each with:
  - "canonical_product_id": a short unique ID like "p_001", "p_002", etc.
  - "canonical_product_name": the cleaned, canonical full product name
  - "brand": the brand name
  - "model": the model name/number
  - "raw_names": array of original raw names that map to this product

"needs_review": an array of objects for any names you're unsure about:
  - "raw_product_name": the original name
  - "reason": why it needs review

Return ONLY the JSON object. No markdown. No explanation.
"""


def parse_json_from_text(text):
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
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]
    product_type_plural = cfg.get("product_type_plural", category_id)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-key-here":
        print("ERROR: OPENAI_API_KEY is not set. Add it to .env")
        sys.exit(1)

    print("=" * 60)
    print(f"Script 2: Canonicalizing products [{category_id}]")
    print("=" * 60)

    with open(data_dir / "reviewer_records.json") as f:
        rr_data = json.load(f)

    records = rr_data.get("records") or []
    if not records:
        print("ERROR: reviewer_records.json has no records to canonicalize.")
        sys.exit(1)

    raw_names = sorted(set(r.get("raw_product_name") for r in records if r.get("raw_product_name")))

    print(f"  Sending {len(raw_names)} raw names to OpenAI for canonicalization...")

    prompt = CANONICALIZE_PROMPT_TEMPLATE.replace("{product_type_plural}", product_type_plural)
    names_text = "\n".join(f"- {name}" for name in raw_names)

    response = client.responses.create(
        model="o4-mini",
        instructions=prompt,
        input=f"Here are the raw product names to canonicalize:\n\n{names_text}",
    )

    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text

    result = parse_json_from_text(text)

    if result is None:
        print("  First attempt failed to parse. Retrying...")
        response = client.responses.create(
            model="o4-mini",
            instructions=prompt + "\n\nYou MUST return valid JSON. No other text.",
            input=f"Here are the raw product names to canonicalize:\n\n{names_text}",
        )
        text = ""
        for item in response.output:
            if hasattr(item, "content") and item.content is not None:
                for block in item.content:
                    if hasattr(block, "text"):
                        text += block.text
        result = parse_json_from_text(text)

    if result is None:
        print("  ERROR: Could not parse canonicalization response after retry.")
        sys.exit(1)

    canonical_products = result.get("canonical_products", [])
    needs_review = result.get("needs_review", [])

    print(f"  Got {len(canonical_products)} canonical products, {len(needs_review)} needing review")

    # Build mapping from raw name to canonical ID
    name_to_canonical = {}
    for cp in canonical_products:
        cid = cp.get("canonical_product_id")
        if not cid:
            print(f"  WARNING: skipping canonical row without canonical_product_id")
            continue
        for raw_name in cp.get("raw_names") or []:
            if not raw_name or not isinstance(raw_name, str):
                continue
            name_to_canonical[raw_name.lower().strip()] = cid

    # Attach canonical IDs to reviewer records
    for record in records:
        raw = record.get("raw_product_name", "").lower().strip()
        record["canonical_product_id"] = name_to_canonical.get(raw)

    # Save outputs
    with open(data_dir / "canonical_products.json", "w") as f:
        json.dump({"canonical_products": canonical_products}, f, indent=2)

    with open(data_dir / "reviewer_records_canonicalized.json", "w") as f:
        json.dump({"records": records}, f, indent=2)

    with open(data_dir / "needs_review.json", "w") as f:
        json.dump({"needs_review": needs_review}, f, indent=2)

    print(f"\n  Saved canonical_products.json ({len(canonical_products)} products)")
    print(f"  Saved reviewer_records_canonicalized.json ({len(records)} records)")
    print(f"  Saved needs_review.json ({len(needs_review)} items)")
    print("Done.")


if __name__ == "__main__":
    main()
