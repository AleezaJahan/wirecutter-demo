"""
Backfill alternative retailers for featured picks.

For each featured pick, searches for additional Canadian retailers
and writes them into site_products.json and site_featured_picks.json.

Usage:
  python3 scripts/backfill_alt_retailers.py --all
  python3 scripts/backfill_alt_retailers.py --category robot_vacuum
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FRONTEND_DATA = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"


def parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'[\[{].*[\]}]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def _response_plain_text(response) -> str:
    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text
    return text


def find_alt_retailers(product_name: str, primary_retailer: Optional[str]) -> list:
    """Search for alternative Canadian retailers for a product."""
    skip_note = ""
    if primary_retailer:
        skip_note = f"\nWe already have it at {primary_retailer}. Do NOT include {primary_retailer} in your results — only find OTHER retailers."

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=(
                "You are a Canadian retail researcher. Find where this product is sold in Canada.\n"
                f"{skip_note}\n\n"
                "Search these Canadian retailers in order:\n"
                "1. Official brand .ca site\n"
                "2. Best Buy Canada (bestbuy.ca)\n"
                "3. Walmart Canada (walmart.ca)\n"
                "4. Canadian Tire (canadiantire.ca)\n"
                "5. Costco Canada (costco.ca)\n"
                "6. Amazon.ca\n"
                "7. Other Canadian retailers\n\n"
                "Return ONLY a JSON array of retailers that sell this product:\n"
                '[{"retailer": "short name", "product_url": "https://...", "price_cad": 123.45}]\n\n'
                "Rules:\n"
                "- Only include retailers where you found the EXACT product page with a CAD price\n"
                "- product_url must be a real URL to the product page\n"
                "- Return an empty array [] if you can't find it anywhere else\n"
                "- No markdown, no explanation, just the JSON array"
            ),
            input=f"Find Canadian retailers for: {product_name}",
            tools=[{"type": "web_search", "search_context_size": "medium"}],
        )
    except Exception as e:
        print(f"    API error: {e}")
        return []

    text = _response_plain_text(response)
    result = parse_json_response(text)

    if isinstance(result, list):
        valid = []
        for r in result:
            if isinstance(r, dict) and (r.get("product_url") or r.get("retailer")):
                price = r.get("price_cad")
                if price is not None:
                    try:
                        price = float(price)
                    except (TypeError, ValueError):
                        price = None
                valid.append({
                    "retailer": r.get("retailer", ""),
                    "product_url": r.get("product_url", ""),
                    "price_display": f"${price:,.2f}" if price else None,
                })
        return valid
    return []


def process_category(category_id: str):
    picks_path = FRONTEND_DATA / category_id / "site_featured_picks.json"
    prods_path = FRONTEND_DATA / category_id / "site_products.json"

    if not picks_path.exists():
        print(f"  Skipping {category_id}: no site_featured_picks.json")
        return

    with open(picks_path) as f:
        picks = json.load(f)
    with open(prods_path) as f:
        products = json.load(f)

    prod_map = {p["id"]: p for p in products}
    picks_changed = False
    prods_changed = False

    for pick in picks:
        if not pick.get("name"):
            continue

        product = prod_map.get(pick.get("id"))
        existing_alts = (product or {}).get("alternative_retailers", [])
        if len(existing_alts) > 0:
            print(f"  [{pick['name'][:40]}] already has {len(existing_alts)} alt(s), skipping")
            continue

        primary = pick.get("retailer") or (product or {}).get("retailer")
        print(f"  [{pick['name'][:40]}] searching for alternatives (primary: {primary})...")
        alts = find_alt_retailers(pick["name"], primary)

        if alts:
            print(f"    -> found {len(alts)}: {[a['retailer'] for a in alts]}")
            if product:
                product["alternative_retailers"] = alts
                prods_changed = True
        else:
            print(f"    -> no alternatives found")

    if prods_changed:
        with open(prods_path, "w") as f:
            json.dump(products, f, indent=2)
        print(f"  Updated site_products.json")

    if picks_changed:
        with open(picks_path, "w") as f:
            json.dump(picks, f, indent=2)
        print(f"  Updated site_featured_picks.json")

    if not prods_changed and not picks_changed:
        print(f"  No changes for {category_id}")


def main():
    if "--all" in sys.argv:
        categories_path = FRONTEND_DATA / "categories.json"
        with open(categories_path) as f:
            categories = json.load(f)
        cat_ids = [c["id"] for c in categories]
    elif "--category" in sys.argv:
        idx = sys.argv.index("--category")
        cat_ids = [sys.argv[idx + 1]]
    else:
        print(__doc__)
        sys.exit(1)

    for cat_id in cat_ids:
        print(f"\n{'='*50}")
        print(f"Backfilling alt retailers: {cat_id}")
        print(f"{'='*50}")
        process_category(cat_id)

    print("\nDone.")


if __name__ == "__main__":
    main()
