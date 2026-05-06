"""
Script 3: verify_canada_purchase_paths.py

Check whether canonical products have a credible Canadian purchase path.
Uses OpenAI Responses API with web_search tool.

Part A: Buyability (retailer, url, price, stock, verified)
Part B: Canadian brand discovery (canadian_company = founded/HQ/parent in Canada; made_in_canada is separate)

Usage:
  python3 scripts/verify_canada_purchase_paths.py --category robot_vacuum
  python3 scripts/verify_canada_purchase_paths.py --category robot_vacuum --refresh
  python3 scripts/verify_canada_purchase_paths.py --category robot_vacuum --workers 1
"""

import json
import os
import re
import sys
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)
from openai import OpenAI
from config import get_category_config

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BUYABILITY_PROMPT_TEMPLATE = """You are a Canadian retail product researcher. Your task is to find a credible Canadian purchase path for a specific {product_type}.

PRODUCT: {{product_name}} (by {{brand}})

SEARCH PRIORITY (you MUST follow this order):
1. FIRST: Search for the official brand Canada website or Canadian storefront
   - e.g. brand.ca, brand.com/ca, ca.brand.com
   - Look for the specific product page with a Canadian price in CAD
2. SECOND: If no official Canadian brand page, check major Canadian retailers:
   - Best Buy Canada (bestbuy.ca)
   - Canadian Tire (canadiantire.ca)
   - Walmart Canada (walmart.ca)
   - Costco Canada (costco.ca)
   - The Bay (thebay.com)
   - Home Depot Canada (homedepot.ca)
   - Staples Canada (staples.ca)
   - Visions Electronics (visions.ca)
{extra_retailers}3. LAST RESORT: Amazon.ca (only if nothing found above)

IMPORTANT:
- The price MUST be in Canadian dollars (CAD), not USD.
- "in_stock" means the product can currently be purchased/added to cart.
- If the product exists on a Canadian site but is out of stock, still report it but set in_stock=false.
- If the product name differs slightly in Canada (e.g. different suffix), still match it if it's clearly the same product.

Return a JSON object with EXACTLY these fields:
{{{{"retailer": "retailer name or domain" or null, "product_url": "full URL to the product page" or null, "price_cad": numeric price in CAD or null, "in_stock": true/false or null, "canada_verified": true/false}}}}

If no Canadian purchase path found at all, return:
{{{{"retailer": null, "product_url": null, "price_cad": null, "in_stock": null, "canada_verified": false}}}}

Return ONLY the JSON object. No markdown. No explanation.
"""

CANADIAN_BRANDS_PROMPT_TEMPLATE = """You are a researcher identifying Canadian {product_type} companies.

Your job is to THOROUGHLY search the web for any {product_type} brands that qualify as CANADIAN COMPANIES.
A Canadian company means ANY of the following (manufacturing in Canada is NOT required):
1. Founded in Canada, OR
2. Headquarters in Canada, OR
3. Parent company is Canadian (even if products are built abroad)

Separately, track manufacturing ONLY in made_in_canada (true only if you find evidence the {product_type} is made or assembled in Canada).
A brand can be canadian_company: true with made_in_canada: false — that is normal (e.g. Canadian-owned, offshore manufacturing).

IMPORTANT SEARCH INSTRUCTIONS:
- Search for "Canadian {product_type} brands" and "Canadian {product_type} companies"
- Search for "{product_type} brands headquartered in Canada"
- Search for "{product_type} made in Canada" and "{product_type} assembled in Canada"
- Also check if any of these specific brands are Canadian: {brands_to_check}
- Look beyond the major international brands. Smaller or niche Canadian companies count too.
- Do NOT assume no Canadian brands exist. Search thoroughly before concluding.

ONLY return brands that qualify as Canadian companies (founded in Canada, HQ in Canada, or Canadian parent).
made_in_canada alone is not required to count as a Canadian company.
Do NOT return non-Canadian brands.

For each Canadian brand found, provide:
- brand_name
- headquarters_location (city, province)
- canadian_company (true if Canadian-founded OR Canadian HQ OR Canadian parent — NOT "only if made in Canada")
- made_in_canada (true ONLY if you substantiate manufacturing/assembly in Canada; false otherwise)
- notes (brief explanation: ownership/HQ vs where products are built)

Return a JSON array. Empty array [] if none found.
Return ONLY the JSON. No markdown. No explanation.
"""

INJECT_PROS_CONS_INSTRUCTIONS_TEMPLATE = """You summarize strengths and drawbacks for shoppers.

PRODUCT: {product_name}
BRAND: {brand_name}
CATEGORY: {product_type}

Use web search — retailer pages, manuals, expert reviews — and only describe what those sources actually say.
Do not invent specs or exaggerate claims.

Return ONLY valid JSON with EXACTLY these keys:
{{"positives": ["...", ...], "negatives": ["...", ...]}}

Rules:
- 3 to 5 short phrases per array (fewer OK if thin coverage).
- Each phrase max 110 characters; plain everyday language (no jargon walls).
- "negatives" = real trade-offs or criticisms, not marketing fluff inverted.
If you find virtually nothing substantive, return empty arrays.
"""


def _response_plain_text(response) -> str:
    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text
    return text


def lightweight_injected_pros_cons(
    product_name: str, brand_name: str, product_type: str
) -> tuple[list, list]:
    """Quick web-scan for bullets (injected Canadian products have no reviewer records)."""
    instr = (
        INJECT_PROS_CONS_INSTRUCTIONS_TEMPLATE.replace("{product_name}", product_name)
        .replace("{brand_name}", brand_name)
        .replace("{product_type}", product_type)
    )
    try:
        response = client.responses.create(
            model="o4-mini",
            instructions=instr,
            input=f"What are credible pros and cons for {product_name} by {brand_name}?",
            tools=[{"type": "web_search", "search_context_size": "medium"}],
        )
    except Exception as e:
        print(f"      pros/cons lookup failed ({e}), skipping")
        return [], []

    data = parse_json_response(_response_plain_text(response))
    if not data or not isinstance(data, dict):
        print("      pros/cons: could not parse JSON, skipping")
        return [], []

    def _clamp(items, *, max_items: int, max_len: int) -> list:
        out = []
        raw = items if isinstance(items, list) else []
        for x in raw[:max_items]:
            if not isinstance(x, str):
                continue
            s = " ".join(x.split()).strip()
            if len(s) > max_len:
                s = s[: max_len - 1] + "\u2026"
            if s:
                out.append(s)
        return out

    pos = _clamp(data.get("positives") or [], max_items=5, max_len=110)
    neg = _clamp(data.get("negatives") or [], max_items=5, max_len=110)
    print(f"      pros/cons: {len(pos)} strength(s), {len(neg)} drawback(s)")
    return pos, neg


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


def validate_url(url):
    if not url:
        return False
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
        return resp.status_code < 400
    except Exception:
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True,
                                headers={"User-Agent": "Mozilla/5.0"}, stream=True)
            return resp.status_code < 400
        except Exception:
            return False


def load_purchase_path_cache(data_dir):
    """Load prior verified purchase paths so repeated runs only refresh misses."""
    cache_path = data_dir / "canada_purchase_paths.json"
    if not cache_path.exists():
        return {}

    try:
        with open(cache_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  WARNING: Could not load existing purchase-path cache ({e})")
        return {}

    cached = {}
    for row in data.get("purchase_paths", []):
        pid = row.get("canonical_product_id")
        if pid:
            cached[pid] = row
    return cached


def reusable_cached_path(product, cached_by_id):
    """Return a cached row only when it is a verified match for this product."""
    pid = product["canonical_product_id"]
    cached = cached_by_id.get(pid)
    if not cached:
        return None

    name = product["canonical_product_name"]
    brand = product["brand"]
    if cached.get("canonical_product_name") != name or cached.get("brand") != brand:
        return None

    if not cached.get("canada_verified"):
        return None
    if not cached.get("retailer") or not cached.get("product_url"):
        return None

    reused = dict(cached)
    reused["canonical_product_id"] = pid
    reused["canonical_product_name"] = name
    reused["brand"] = brand
    return reused


def print_cached_path(row):
    price = row.get("price_cad")
    try:
        price_str = f"${float(price):.2f}" if price is not None else "N/A"
    except (ValueError, TypeError):
        price_str = "N/A"
    stock = "in stock" if row.get("in_stock") else "out of stock/unknown"
    print(f"      cached | {row.get('retailer', 'N/A')} | {price_str} | {stock}")


def get_int_arg(flag, default):
    for i, arg in enumerate(sys.argv):
        if arg == flag and i + 1 < len(sys.argv):
            try:
                return max(1, int(sys.argv[i + 1]))
            except ValueError:
                print(f"  WARNING: Invalid {flag} value '{sys.argv[i + 1]}', using {default}")
                return default
    return default


def verify_product(product, buyability_prompt, price_min, price_max):
    pid = product["canonical_product_id"]
    name = product["canonical_product_name"]
    brand = product["brand"]

    prompt = buyability_prompt.replace("{product_name}", name).replace("{brand}", brand)

    print(f"    [{pid}] {name}...")

    response = client.responses.create(
        model="o4-mini",
        instructions=prompt,
        input=f"Find a Canadian purchase path for: {name} by {brand}",
        tools=[{"type": "web_search", "search_context_size": "high"}],
    )

    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text

    result = parse_json_response(text)
    if result is None:
        print(f"      WARNING: Could not parse response for {name}")
        result = {
            "retailer": None, "product_url": None,
            "price_cad": None, "in_stock": None, "canada_verified": False,
        }

    notes = []

    if result.get("product_url"):
        url_ok = validate_url(result["product_url"])
        if not url_ok:
            notes.append("URL validation failed (non-200 or unreachable)")
            result["canada_verified"] = False

    price = result.get("price_cad")
    if price is not None:
        try:
            price = float(price)
            if price < price_min or price > price_max:
                notes.append(f"Price ${price} outside expected range ${price_min}-${price_max}")
        except (ValueError, TypeError):
            notes.append(f"Price value '{price}' is not a valid number")
            price = None

    status = "verified" if result.get("canada_verified") else "not found"
    stock = "in stock" if result.get("in_stock") else "out of stock/unknown"
    price_str = f"${price:.2f}" if price else "N/A"
    print(f"      {status} | {result.get('retailer', 'N/A')} | {price_str} | {stock}")

    return {
        "canonical_product_id": pid,
        "canonical_product_name": name,
        "brand": brand,
        "retailer": result.get("retailer"),
        "product_url": result.get("product_url"),
        "price_cad": price,
        "in_stock": result.get("in_stock"),
        "canada_verified": result.get("canada_verified", False),
        "canadian_company": False,
        "made_in_canada": False,
        "notes": "; ".join(notes) if notes else "",
    }


def inject_canadian_product(brand_name, product_type, buyability_prompt, price_min, price_max):
    """Find the top product from a Canadian brand and get its Canadian purchase path."""
    response = client.responses.create(
        model="o4-mini",
        instructions=(
            f"Find the most popular or best-rated {product_type} made by {brand_name}. "
            f"Return a JSON object with: "
            f'{{"product_name": "full product name", "brand": "{brand_name}", "model": "model name"}}'
        ),
        input=f"What is the best or most popular {product_type} from {brand_name}?",
        tools=[{"type": "web_search", "search_context_size": "high"}],
    )
    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text
    product_info = parse_json_response(text)
    if not product_info or not product_info.get("product_name"):
        print(f"      Could not find a product for {brand_name}")
        return None

    name = product_info["product_name"]
    model = product_info.get("model", "")
    print(f"      Found: {name}")

    prompt = buyability_prompt.replace("{product_name}", name).replace("{brand}", brand_name)
    response = client.responses.create(
        model="o4-mini",
        instructions=prompt,
        input=f"Find a Canadian purchase path for: {name} by {brand_name}",
        tools=[{"type": "web_search", "search_context_size": "high"}],
    )
    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text
    result = parse_json_response(text)
    if result is None:
        result = {"retailer": None, "product_url": None, "price_cad": None, "in_stock": None, "canada_verified": False}

    price = result.get("price_cad")
    if price is not None:
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = None

    status = "verified" if result.get("canada_verified") else "not found"
    price_str = f"${price:.2f}" if price else "N/A"
    stock_str = "in stock" if result.get("in_stock") else "out of stock"
    print(f"      {status} | {result.get('retailer', 'N/A')} | {price_str} | {stock_str}")

    positives, negatives = lightweight_injected_pros_cons(name, brand_name, product_type)

    return {
        "canonical_product_id": None,
        "canonical_product_name": name,
        "brand": brand_name,
        "model": model,
        "retailer": result.get("retailer"),
        "product_url": result.get("product_url"),
        "price_cad": price,
        "in_stock": result.get("in_stock"),
        "canada_verified": result.get("canada_verified", False),
        "canadian_company": False,
        "made_in_canada": False,
        "notes": "Canadian brand product (not reviewer-backed)",
        "positives": positives,
        "negatives": negatives,
    }


def find_canadian_brands(product_type, product_type_plural, brands_in_dataset):
    print(f"\n  Part B: Searching for Canadian {product_type} brands...")
    brands_csv = ", ".join(brands_in_dataset) if brands_in_dataset else "none known yet"

    prompt = (CANADIAN_BRANDS_PROMPT_TEMPLATE
              .replace("{product_type}", product_type)
              .replace("{product_type_plural}", product_type_plural)
              .replace("{brands_to_check}", brands_csv))

    response = client.responses.create(
        model="o4-mini",
        instructions=prompt,
        input=(
            f"Search thoroughly for any {product_type} brands that are Canadian companies, "
            f"headquartered in Canada, or manufacture in Canada. "
            f"Also check whether any of these brands from our dataset are Canadian: {brands_csv}"
        ),
        tools=[{"type": "web_search", "search_context_size": "high"}],
    )

    text = ""
    for item in response.output:
        if hasattr(item, "content") and item.content is not None:
            for block in item.content:
                if hasattr(block, "text"):
                    text += block.text

    brands = parse_json_response(text)
    if brands is None:
        brands = []
    if not isinstance(brands, list):
        brands = [brands]

    print(f"    Found {len(brands)} Canadian brand(s)")
    for b in brands:
        print(f"      - {b.get('brand_name', 'unknown')}: {b.get('notes', '')}")

    return brands


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]
    product_type = cfg.get("product_type", category_id)
    product_type_plural = cfg.get("product_type_plural", product_type)
    price_range = cfg.get("price_range", {})
    price_min = price_range.get("min", 10)
    price_max = price_range.get("max", 10000)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-key-here":
        print("ERROR: OPENAI_API_KEY is not set. Add it to .env")
        sys.exit(1)

    extra_retailers = cfg.get("canadian_retailers", [])
    if extra_retailers:
        lines = "".join(f"   - {r}\n" for r in extra_retailers)
        extra_block = f"2b. ALSO CHECK these category-specific Canadian retailers:\n{lines}"
    else:
        extra_block = ""
    buyability_prompt = (BUYABILITY_PROMPT_TEMPLATE
                         .replace("{product_type}", product_type)
                         .replace("{extra_retailers}", extra_block))

    print("=" * 60)
    print(f"Script 3: Verifying Canada purchase paths [{category_id}]")
    print("=" * 60)

    with open(data_dir / "canonical_products.json") as f:
        data = json.load(f)

    products = data["canonical_products"]
    print(f"  Processing {len(products)} canonical products\n")

    refresh = "--refresh" in sys.argv
    workers = get_int_arg("--workers", 4)
    cached_by_id = {} if refresh else load_purchase_path_cache(data_dir)
    if refresh:
        print("  Cache disabled via --refresh; all products will be rechecked")
    elif cached_by_id:
        reusable_count = sum(
            1 for product in products
            if reusable_cached_path(product, cached_by_id) is not None
        )
        print(f"  Cache: reusing {reusable_count} verified purchase path(s)")

    print(f"  Part A: Checking buyability in Canada... (workers={workers})")
    purchase_paths = [None] * len(products)
    products_to_verify = []

    for idx, product in enumerate(products):
        cached = reusable_cached_path(product, cached_by_id)
        if cached is not None:
            print(f"    [{product['canonical_product_id']}] {product['canonical_product_name']}...")
            print_cached_path(cached)
            purchase_paths[idx] = cached
            continue

        products_to_verify.append((idx, product))

    if workers <= 1:
        for idx, product in products_to_verify:
            result = verify_product(product, buyability_prompt, price_min, price_max)
            purchase_paths[idx] = result
            time.sleep(1)
    elif products_to_verify:
        max_workers = min(workers, len(products_to_verify))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    verify_product,
                    product,
                    buyability_prompt,
                    price_min,
                    price_max,
                ): idx
                for idx, product in products_to_verify
            }
            for future in as_completed(futures):
                idx = futures[future]
                purchase_paths[idx] = future.result()

    purchase_paths = [pp for pp in purchase_paths if pp is not None]

    dataset_brands = sorted(set(p["brand"] for p in products))
    canadian_brands = find_canadian_brands(product_type, product_type_plural, dataset_brands)
    brand_names_lower = {
        b.get("brand_name", "").lower()
        for b in canadian_brands
        if b.get("canadian_company")
    }

    for pp in purchase_paths:
        if pp["brand"].lower() in brand_names_lower:
            pp["canadian_company"] = True
            matching = [b for b in canadian_brands if b.get("brand_name", "").lower() == pp["brand"].lower()]
            if matching and matching[0].get("made_in_canada"):
                pp["made_in_canada"] = True

    # Part C: Inject top product for Canadian brands not already in the dataset
    existing_brands_lower = {pp["brand"].lower() for pp in purchase_paths}
    for cb in canadian_brands:
        if not cb.get("canadian_company"):
            continue
        bname = cb.get("brand_name", "")
        if bname.lower() in existing_brands_lower:
            continue
        print(f"\n  Part C: Injecting top product for Canadian brand '{bname}'...")
        injected = inject_canadian_product(bname, product_type, buyability_prompt, price_min, price_max)
        if injected:
            injected["canadian_company"] = True
            injected["made_in_canada"] = cb.get("made_in_canada", False)
            injected["reviewer_backed"] = False
            purchase_paths.append(injected)
            # Also inject into canonical_products.json so Script 4 can merge
            new_pid = f"p_{len(products) + 1:03d}"
            injected["canonical_product_id"] = new_pid
            new_canonical = {
                "canonical_product_id": new_pid,
                "canonical_product_name": injected["canonical_product_name"],
                "brand": injected["brand"],
                "model": injected.get("model", ""),
                "raw_names": [injected["canonical_product_name"]],
            }
            products.append(new_canonical)
            data["canonical_products"] = products
            with open(data_dir / "canonical_products.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"      Injected as {new_pid}")

    verified = [pp for pp in purchase_paths if pp["canada_verified"]]
    not_available = [pp for pp in purchase_paths if not pp["canada_verified"]]
    in_stock = [pp for pp in verified if pp.get("in_stock")]

    output = {
        "metadata": {
            "category": category_id,
            "total_products": len(products),
            "canada_verified_count": len(verified),
            "not_available_count": len(not_available),
            "in_stock_count": len(in_stock),
        },
        "purchase_paths": purchase_paths,
        "canadian_brands": canadian_brands,
    }

    out_path = data_dir / "canada_purchase_paths.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Summary:")
    print(f"    Total products: {len(products)}")
    print(f"    Canada verified: {len(verified)}")
    print(f"    In stock: {len(in_stock)}")
    print(f"    Not available: {len(not_available)}")
    print(f"\n  Saved to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
