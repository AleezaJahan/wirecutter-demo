"""
Fetch product image URLs for featured picks.

Primary method: scrape og:image from the retailer product page (free, fast, reliable).
Fallback: use gpt-4o-mini web search if og:image scraping fails.

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

import requests
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FRONTEND_DATA = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def scrape_og_image(url: str) -> Optional[str]:
    """Fetch a product page and extract the og:image meta tag."""
    if not url or not url.startswith("http"):
        return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code >= 400:
            return None
        html = resp.text[:50000]

        og_match = re.search(
            r'<meta\s+(?:[^>]*?)property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not og_match:
            og_match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+(?:[^>]*?)property=["\']og:image["\']',
                html, re.IGNORECASE
            )
        if og_match:
            img_url = og_match.group(1).strip()
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            if img_url.startswith("http"):
                return img_url

        img_match = re.search(
            r'<meta\s+(?:[^>]*?)name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not img_match:
            img_match = re.search(
                r'<meta\s+content=["\']([^"\']+)["\']\s+(?:[^>]*?)name=["\']twitter:image["\']',
                html, re.IGNORECASE
            )
        if img_match:
            img_url = img_match.group(1).strip()
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            if img_url.startswith("http"):
                return img_url

    except Exception:
        pass
    return None


def fetch_image_url_ai(product_name: str) -> Optional[str]:
    """Fallback: ask gpt-4o-mini to find the product image URL via web search."""
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
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
        print(f"    AI fallback error: {e}")
        return None

    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text

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
        if result and result.get("image_url"):
            return result["image_url"]
    except json.JSONDecodeError:
        pass

    url_match = re.search(r'https?://\S+\.(?:jpg|jpeg|png|webp)\S*', text, re.IGNORECASE)
    if url_match:
        return url_match.group().rstrip(')"\'')

    return None


def process_category(category_id: str):
    picks_path = FRONTEND_DATA / category_id / "site_featured_picks.json"
    products_path = FRONTEND_DATA / category_id / "site_products.json"
    if not picks_path.exists():
        print(f"  Skipping {category_id}: no site_featured_picks.json")
        return

    with open(picks_path) as f:
        picks = json.load(f)

    product_urls = {}
    if products_path.exists():
        with open(products_path) as f:
            for p in json.load(f):
                if not p.get("id"):
                    continue
                if p.get("product_url"):
                    product_urls[p["id"]] = [p["product_url"]]
                else:
                    product_urls[p["id"]] = []
                for alt in p.get("alternative_retailers") or []:
                    if alt.get("product_url"):
                        product_urls.setdefault(p["id"], []).append(alt["product_url"])

    changed = False
    for pick in picks:
        if not pick.get("name"):
            continue
        if pick.get("image_url"):
            print(f"  [{pick['name'][:50]}] already has image, skipping")
            continue

        urls_to_try = product_urls.get(pick.get("id")) or []
        image_url = None

        for url in urls_to_try:
            print(f"  [{pick['name'][:50]}] trying og:image from {url[:60]}...")
            image_url = scrape_og_image(url)
            if image_url:
                print(f"    -> og:image: {image_url[:80]}...")
                break

        if not image_url:
            if not urls_to_try:
                print(f"  [{pick['name'][:50]}] no product URLs available, trying AI fallback...")
            else:
                print(f"    og:image failed on all URLs, trying AI fallback...")
            image_url = fetch_image_url_ai(pick["name"])
            if image_url:
                print(f"    -> AI fallback: {image_url[:80]}...")
            else:
                print(f"    -> no image found")

        if image_url:
            pick["image_url"] = image_url
            changed = True

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
