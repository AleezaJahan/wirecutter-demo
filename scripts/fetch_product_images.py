"""
Fetch product image URLs for featured picks using o4-mini web search.

Usage:
  python3 scripts/fetch_product_images.py --category air_purifier
  python3 scripts/fetch_product_images.py --all
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
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def fetch_image_url(product_name: str) -> Optional[str]:
    """Ask o4-mini to find the official product image URL."""
    try:
        response = client.responses.create(
            model="o4-mini",
            instructions=(
                "Find the official product image URL for this product. "
                "Look on the manufacturer's website or a major retailer. "
                "The URL must point directly to a .jpg, .png, or .webp image file, "
                "OR be an og:image / product image URL from the product page. "
                'Return ONLY a JSON object: {"image_url": "https://..."}\n'
                "No markdown. No explanation. Just the JSON."
            ),
            input=f"Find the official product image for: {product_name}",
            tools=[{"type": "web_search", "search_context_size": "medium"}],
        )
    except Exception as e:
        print(f"    API error: {e}")
        return None

    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text

    result = parse_json_response(text)
    if result and result.get("image_url"):
        return result["image_url"]

    url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|webp)\S*', text, re.IGNORECASE)
    if url_match:
        return url_match.group().rstrip(')"\'')

    return None


def process_category(category_id: str):
    picks_path = FRONTEND_DATA / category_id / "site_featured_picks.json"
    if not picks_path.exists():
        print(f"  Skipping {category_id}: no site_featured_picks.json")
        return

    with open(picks_path) as f:
        picks = json.load(f)

    changed = False
    for pick in picks:
        if not pick.get("name"):
            continue
        if pick.get("image_url"):
            print(f"  [{pick['name']}] already has image, skipping")
            continue

        print(f"  [{pick['name']}] searching...")
        url = fetch_image_url(pick["name"])
        if url:
            pick["image_url"] = url
            changed = True
            print(f"    -> {url[:80]}...")
        else:
            print(f"    -> no image found")

    if changed:
        with open(picks_path, "w") as f:
            json.dump(picks, f, indent=2)
        print(f"  Updated {picks_path.name}")
    else:
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
        print(f"Fetching images: {cat_id}")
        print(f"{'='*50}")
        process_category(cat_id)

    print("\nDone.")


if __name__ == "__main__":
    main()
