"""
Script 3: verify_canada_purchase_paths.py

Check whether canonical products have a credible Canadian purchase path.
Uses OpenAI Responses API with web_search tool.

Part A: Buyability (retailer, url, price, stock, verified)
Part B: Canadian brand signals (canadian_company, made_in_canada)

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

# --- Structured output schemas ---
BUYABILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "retailers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "retailer": {"type": "string"},
                    "product_url": {"type": "string"},
                    "price_cad": {"type": ["number", "null"]},
                    "original_price_cad": {"type": ["number", "null"]},
                    "in_stock": {"type": "boolean"},
                },
                "required": ["retailer", "product_url", "price_cad", "original_price_cad", "in_stock"],
                "additionalProperties": False,
            },
        },
        "canada_verified": {"type": "boolean"},
    },
    "required": ["retailers", "canada_verified"],
    "additionalProperties": False,
}

BRAND_ORIGIN_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_name": {"type": "string"},
        "headquarters_location": {"type": ["string", "null"]},
        "canadian_company": {"type": "boolean"},
        "made_in_canada": {"type": "boolean"},
        "confidence": {"type": "string"},
        "evidence_url": {"type": ["string", "null"]},
        "notes": {"type": "string"},
    },
    "required": ["brand_name", "headquarters_location", "canadian_company", "made_in_canada", "confidence", "evidence_url", "notes"],
    "additionalProperties": False,
}

PROS_CONS_SCHEMA = {
    "type": "object",
    "properties": {
        "positives": {"type": "array", "items": {"type": "string"}},
        "negatives": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["positives", "negatives"],
    "additionalProperties": False,
}

INJECT_COMBINED_SCHEMA = {
    "type": "object",
    "properties": {
        "retailers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "retailer": {"type": "string"},
                    "product_url": {"type": "string"},
                    "price_cad": {"type": ["number", "null"]},
                    "original_price_cad": {"type": ["number", "null"]},
                    "in_stock": {"type": "boolean"},
                },
                "required": ["retailer", "product_url", "price_cad", "original_price_cad", "in_stock"],
                "additionalProperties": False,
            },
        },
        "canada_verified": {"type": "boolean"},
        "positives": {"type": "array", "items": {"type": "string"}},
        "negatives": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["retailers", "canada_verified", "positives", "negatives"],
    "additionalProperties": False,
}

PRODUCT_DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "product_name": {"type": "string"},
        "brand": {"type": "string"},
        "model": {"type": "string"},
    },
    "required": ["product_name", "brand", "model"],
    "additionalProperties": False,
}

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

Return ONLY this JSON shape (no markdown, no explanation):
{{
  "retailers": [
    {{
      "retailer": "short name or domain",
      "product_url": "full https URL to the product page",
      "price_cad": 123.45,
      "original_price_cad": 199.99 or null if the page does NOT show a higher regular/was/list price than price_cad,
      "in_stock": true or false
    }}
  ],
  "canada_verified": true or false
}}

Rules:
- ALWAYS search at least 3 Canadian retailers for the product. Return a row for EACH retailer that sells this product in Canada — aim for 2-3 rows. Only return 1 row if the product is truly exclusive to a single retailer.
- Prioritize the search order above, but check at least the brand site, one big-box retailer (Best Buy, Walmart, Canadian Tire), and Amazon.ca.
- original_price_cad: only when the page clearly shows a pre-sale or list price higher than price_cad; otherwise null.
- If nothing credible is found: {{"retailers": [], "canada_verified": false}}
"""

CANADIAN_BRANDS_PROMPT_TEMPLATE = """You are a researcher identifying Canadian {product_type} companies.

Your job is to THOROUGHLY search the web for any {product_type} brands that are:
1. Canadian-founded companies, OR
2. Companies headquartered in Canada, OR
3. Brands that manufacture or assemble {product_type_plural} in Canada

REQUIRED SEARCH STEPS (do ALL of these):
1. Search "Canadian {product_type} brands"
2. Search "Canadian {product_type} companies"
3. Search "{product_type} made in Canada"
4. Search "{product_type} headquartered in Canada"
5. Search "Canadian-owned {product_type}"
6. Check if any of these brands from our dataset are Canadian: {brands_to_check}

IMPORTANT:
- Include niche, prosumer, and commercial brands — not just mainstream consumer ones.
- Canadian-OWNED counts even if manufacturing is overseas.
- Do NOT give up after one search. Try all 6 searches above before concluding.
- It is VERY RARE that no Canadian brand exists in a product category. Search harder.

For each Canadian brand found, return:
- brand_name
- headquarters_location (city, province)
- canadian_company (true)
- made_in_canada (true/false)
- top_product (the most popular or best-rated {product_type} from this brand — full product name)
- notes (1-2 sentence explanation of why this is Canadian)

Return a JSON array. Return ONLY valid JSON, no markdown, no explanation.
"""

BRAND_ORIGIN_PROMPT_TEMPLATE = """You are verifying whether a product brand is Canadian.

BRAND: {brand_name}
CATEGORY: {product_type}

Search the web for:
- "{brand_name} headquarters"
- "{brand_name} founded"
- "{brand_name} {product_type} company Canada"
- "{brand_name} made in Canada" or "{brand_name} manufactured in Canada"

Return ONLY valid JSON with EXACTLY these keys:
{{
  "brand_name": "{brand_name}",
  "headquarters_location": "city, province/state, country" or null,
  "canadian_company": true/false,
  "made_in_canada": true/false,
  "confidence": "high" or "medium" or "low",
  "evidence_url": "best URL supporting this" or null,
  "notes": "short explanation"
}}

Rules:
- canadian_company is true if the brand is Canadian-founded, Canadian-owned, or headquartered in Canada.
- made_in_canada is true only if the products are clearly made, assembled, or manufactured in Canada.
- Do not mark a brand Canadian just because it sells in Canada.
- If the brand name is generic or ambiguous, use the category to disambiguate.
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
            model="gpt-4o-mini",
            instructions=instr,
            input=f"What are credible pros and cons for {product_name} by {brand_name}?",
            tools=[{"type": "web_search", "search_context_size": "medium"}],
            text={"format": {"type": "json_schema", "name": "pros_cons", "strict": True, "schema": PROS_CONS_SCHEMA}},
        )
    except Exception as e:
        print(f"      pros/cons lookup failed ({e}), skipping")
        return [], []

    text = _response_plain_text(response)
    data = json.loads(text) if text.strip() else {}
    if not isinstance(data, dict):
        print("      pros/cons: unexpected response, skipping")
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


def _float_or_none(x):
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def normalize_buyability(parsed):
    """Turn model JSON (retailers[] or legacy single-object) into primary row + alternatives."""
    base = {
        "retailer": None,
        "product_url": None,
        "price_cad": None,
        "original_price_cad": None,
        "in_stock": None,
        "is_on_sale": False,
        "alternative_retailers": [],
        "canada_verified": False,
    }
    if not parsed or not isinstance(parsed, dict):
        return dict(base)

    canada_verified = bool(parsed.get("canada_verified", False))
    rows = []
    raw_list = parsed.get("retailers")
    if isinstance(raw_list, list):
        for r in raw_list:
            if not isinstance(r, dict):
                continue
            rows.append(
                {
                    "retailer": r.get("retailer"),
                    "product_url": r.get("product_url"),
                    "price_cad": _float_or_none(r.get("price_cad")),
                    "original_price_cad": _float_or_none(r.get("original_price_cad")),
                    "in_stock": r.get("in_stock"),
                }
            )
    elif parsed.get("retailer") or parsed.get("product_url"):
        rows.append(
            {
                "retailer": parsed.get("retailer"),
                "product_url": parsed.get("product_url"),
                "price_cad": _float_or_none(parsed.get("price_cad")),
                "original_price_cad": _float_or_none(parsed.get("original_price_cad")),
                "in_stock": parsed.get("in_stock"),
            }
        )
        canada_verified = bool(parsed.get("canada_verified", canada_verified))

    rows = [r for r in rows if r.get("product_url") or r.get("retailer")]
    if not rows:
        out = dict(base)
        out["canada_verified"] = canada_verified
        return out

    def sort_key(r):
        in_stock_first = 1 if r.get("in_stock") is True else 0
        pr = r.get("price_cad")
        pk = pr if pr is not None else float("inf")
        return (-in_stock_first, pk)

    ordered = sorted(rows, key=sort_key)
    primary = ordered[0]
    alts = ordered[1:4]

    price = primary.get("price_cad")
    orig = primary.get("original_price_cad")
    is_on_sale = bool(
        orig is not None and price is not None and orig > price
    )
    if not is_on_sale:
        orig = None

    alternatives = []
    for a in alts:
        if not (a.get("retailer") or a.get("product_url")):
            continue
        alternatives.append(
            {
                "retailer": a.get("retailer"),
                "product_url": a.get("product_url"),
                "price_cad": a.get("price_cad"),
            }
        )

    return {
        "retailer": primary.get("retailer"),
        "product_url": primary.get("product_url"),
        "price_cad": price,
        "original_price_cad": orig,
        "in_stock": primary.get("in_stock"),
        "is_on_sale": is_on_sale,
        "alternative_retailers": alternatives,
        "canada_verified": canada_verified,
    }


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


def normalize_brand_name(name):
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


GLOBAL_BRAND_ORIGINS_PATH = Path(__file__).resolve().parent.parent / "data" / "global_brand_origins.json"


def _load_origins_file(path):
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    origins = data.get("brand_origins", data if isinstance(data, list) else [])
    cached = {}
    for row in origins:
        if not isinstance(row, dict):
            continue
        brand = row.get("brand_name")
        key = normalize_brand_name(brand)
        if key:
            cached[key] = row
    return cached


def load_brand_origin_cache(data_dir):
    global_cache = _load_origins_file(GLOBAL_BRAND_ORIGINS_PATH)
    category_cache = _load_origins_file(data_dir / "brand_origins.json")
    merged = dict(global_cache)
    merged.update(category_cache)
    return merged


def _save_origins_file(path, origins):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(origins.values(), key=lambda x: (x.get("brand_name") or "").lower())
    with open(path, "w") as f:
        json.dump({"brand_origins": rows}, f, indent=2)


def save_brand_origins(data_dir, origins):
    _save_origins_file(data_dir / "brand_origins.json", origins)
    global_cache = _load_origins_file(GLOBAL_BRAND_ORIGINS_PATH)
    global_cache.update(origins)
    _save_origins_file(GLOBAL_BRAND_ORIGINS_PATH, global_cache)


def verify_brand_origin(brand_name, product_type):
    print(f"    [brand] {brand_name}...")
    prompt = (BRAND_ORIGIN_PROMPT_TEMPLATE
              .replace("{brand_name}", brand_name)
              .replace("{product_type}", product_type))
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=prompt,
            input=f"Verify whether {brand_name} is a Canadian {product_type} brand.",
            tools=[{"type": "web_search", "search_context_size": "medium"}],
            text={"format": {"type": "json_schema", "name": "brand_origin", "strict": True, "schema": BRAND_ORIGIN_SCHEMA}},
        )
    except Exception as e:
        print(f"      brand lookup failed ({e}), marking non-Canadian")
        return {
            "brand_name": brand_name,
            "headquarters_location": None,
            "canadian_company": False,
            "made_in_canada": False,
            "confidence": "low",
            "evidence_url": None,
            "notes": f"Lookup failed: {e}",
        }

    text = _response_plain_text(response)
    data = json.loads(text) if text.strip() else {}

    result = {
        "brand_name": brand_name,
        "headquarters_location": data.get("headquarters_location"),
        "canadian_company": bool(data.get("canadian_company", False)),
        "made_in_canada": bool(data.get("made_in_canada", False)),
        "confidence": data.get("confidence") or "low",
        "evidence_url": data.get("evidence_url"),
        "notes": data.get("notes", ""),
    }
    status = "Canadian" if result["canadian_company"] else "not Canadian"
    print(f"      {status} | {result.get('headquarters_location') or 'unknown'}")
    return result


def verify_brand_origins(brands, product_type, data_dir, refresh, workers):
    print(f"\n  Part B1: Checking brand origins ({len(brands)} brand(s))...")
    cached = {} if refresh else load_brand_origin_cache(data_dir)
    origins = dict(cached)
    to_verify = []

    for brand in brands:
        key = normalize_brand_name(brand)
        if not key:
            continue
        if key in origins:
            row = origins[key]
            status = "Canadian" if row.get("canadian_company") else "not Canadian"
            print(f"    [brand] {brand}...")
            print(f"      cached | {status} | {row.get('headquarters_location') or 'unknown'}")
            continue
        to_verify.append(brand)

    if workers <= 1:
        for brand in to_verify:
            row = verify_brand_origin(brand, product_type)
            origins[normalize_brand_name(brand)] = row
            time.sleep(1)
    elif to_verify:
        max_workers = min(workers, len(to_verify))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(verify_brand_origin, brand, product_type): brand
                for brand in to_verify
            }
            for future in as_completed(futures):
                brand = futures[future]
                origins[normalize_brand_name(brand)] = future.result()

    save_brand_origins(data_dir, origins)
    canadian = [row for row in origins.values() if row.get("canadian_company")]
    print(f"    Canadian brand(s) found by brand check: {len(canadian)}")
    return origins


def known_brand_origins_from_config(cfg):
    """Category-level escape hatch for known Canadian brands (no API required)."""
    rows = {}
    for item in cfg.get("known_canadian_brands", []):
        if isinstance(item, str):
            row = {
                "brand_name": item,
                "headquarters_location": None,
                "canadian_company": True,
                "made_in_canada": False,
                "confidence": "manual",
                "evidence_url": None,
                "notes": "Configured as a known Canadian brand.",
            }
        elif isinstance(item, dict) and item.get("brand_name"):
            row = {
                "brand_name": item.get("brand_name"),
                "headquarters_location": item.get("headquarters_location"),
                "canadian_company": bool(item.get("canadian_company", True)),
                "made_in_canada": bool(item.get("made_in_canada", False)),
                "confidence": item.get("confidence", "manual"),
                "evidence_url": item.get("evidence_url"),
                "notes": item.get("notes", "Configured as a known Canadian brand."),
            }
        else:
            continue

        key = normalize_brand_name(row["brand_name"])
        if key:
            rows[key] = row
    return rows


def verify_product(product, buyability_prompt, price_min, price_max):
    pid = product["canonical_product_id"]
    name = product["canonical_product_name"]
    brand = product["brand"]

    prompt = buyability_prompt.replace("{product_name}", name).replace("{brand}", brand)

    print(f"    [{pid}] {name}...")

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=prompt,
        input=f"Find a Canadian purchase path for: {name} by {brand}",
        tools=[{"type": "web_search", "search_context_size": "medium"}],
        text={"format": {"type": "json_schema", "name": "buyability", "strict": True, "schema": BUYABILITY_SCHEMA}},
    )

    text = _response_plain_text(response)
    parsed = json.loads(text) if text.strip() else {}
    norm = normalize_buyability(parsed)

    notes = []

    if norm.get("product_url"):
        url_ok = validate_url(norm["product_url"])
        if not url_ok:
            # Primary URL failed — try alternative retailers before giving up
            fallback_found = False
            for alt in norm.get("alternative_retailers", []):
                alt_url = alt.get("product_url")
                if alt_url and validate_url(alt_url):
                    notes.append(f"Primary URL failed ({norm['retailer']}), fell back to {alt.get('retailer')}")
                    norm["retailer"] = alt.get("retailer") or norm["retailer"]
                    norm["product_url"] = alt_url
                    if alt.get("price_cad") is not None:
                        norm["price_cad"] = alt["price_cad"]
                    remaining_alts = [a for a in norm["alternative_retailers"] if a.get("product_url") != alt_url]
                    norm["alternative_retailers"] = remaining_alts
                    fallback_found = True
                    print(f"      primary URL unreachable, fell back to {alt.get('retailer')}")
                    break
            if not fallback_found:
                notes.append("URL validation failed (non-200 or unreachable)")
                norm["canada_verified"] = False

    price = norm.get("price_cad")
    if price is not None:
        try:
            price = float(price)
            if price < price_min or price > price_max:
                notes.append(f"Price ${price} outside expected range ${price_min}-${price_max}")
        except (ValueError, TypeError):
            notes.append(f"Price value '{price}' is not a valid number")
            price = None
            norm["price_cad"] = None

    status = "verified" if norm.get("canada_verified") else "not found"
    stock = "in stock" if norm.get("in_stock") else "out of stock/unknown"
    price_str = f"${price:.2f}" if price else "N/A"
    sale_flag = " (sale)" if norm.get("is_on_sale") else ""
    print(f"      {status} | {norm.get('retailer', 'N/A')} | {price_str}{sale_flag} | {stock}")

    return {
        "canonical_product_id": pid,
        "canonical_product_name": name,
        "brand": brand,
        "retailer": norm.get("retailer"),
        "product_url": norm.get("product_url"),
        "price_cad": price,
        "original_price_cad": norm.get("original_price_cad"),
        "is_on_sale": norm.get("is_on_sale", False),
        "in_stock": norm.get("in_stock"),
        "canada_verified": norm.get("canada_verified", False),
        "alternative_retailers": norm.get("alternative_retailers", []),
        "canadian_company": False,
        "made_in_canada": False,
        "notes": "; ".join(notes) if notes else "",
    }


def _extract_json_from_prose(prose, brand_name, product_type):
    """Retry: ask the model to pull structured JSON from its own prose answer (no web search)."""
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=(
                "You previously answered a question about a product. "
                "Extract ONLY a JSON object from your answer. "
                "Return NOTHING except valid JSON in this format: "
                f'{{"product_name": "full product name", "brand": "{brand_name}", "model": "model name"}}'
            ),
            input=f"Extract the product info from this text:\n\n{prose[:2000]}",
        )
        text = ""
        for item in response.output:
            if hasattr(item, "content") and item.content is not None:
                for block in item.content:
                    if hasattr(block, "text"):
                        text += block.text
        return parse_json_response(text)
    except Exception:
        return None


INJECT_COMBINED_PROMPT_TEMPLATE = """You are a Canadian retail product researcher.
Do TWO things for this product in a SINGLE search session:

PRODUCT: {product_name} by {brand_name}
CATEGORY: {product_type}

TASK 1 — Canadian purchase path:
Search Canadian retailers (brand .ca site, Best Buy Canada, Walmart Canada, Canadian Tire, Amazon.ca) for this product.
Find: retailer name, product URL, CAD price, and whether it is in stock.

TASK 2 — Pros and cons:
From retailer pages, reviews, or expert sources, list 3-5 brief strengths and 3-5 brief drawbacks.

Return ONLY this JSON (no markdown, no explanation):
{{
  "retailers": [
    {{"retailer": "short name", "product_url": "https://...", "price_cad": 123.45, "original_price_cad": null, "in_stock": true}}
  ],
  "canada_verified": true,
  "positives": ["...", "..."],
  "negatives": ["...", "..."]
}}

If you cannot find the product in Canada: {{"retailers": [], "canada_verified": false, "positives": [], "negatives": []}}
"""


def inject_canadian_product(brand_name, product_type, buyability_prompt, price_min, price_max, pre_discovered_product=None):
    """Get Canadian purchase path + pros/cons for a Canadian brand's top product in one call."""

    if pre_discovered_product:
        name = pre_discovered_product
        print(f"      Using pre-discovered product: {name}")
    else:
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions=(
                f"Find the most popular or best-rated {product_type} made by {brand_name}. "
                f"Return the product name, brand, and model."
            ),
            input=f"What is the best or most popular {product_type} from {brand_name}?",
            tools=[{"type": "web_search", "search_context_size": "medium"}],
            text={"format": {"type": "json_schema", "name": "product_discovery", "strict": True, "schema": PRODUCT_DISCOVERY_SCHEMA}},
        )
        text = _response_plain_text(response)
        product_info = json.loads(text) if text.strip() else {}
        if not product_info.get("product_name"):
            print(f"      Could not find a product for {brand_name}")
            return None
        name = product_info["product_name"]
        print(f"      Found: {name}")

    prompt = (INJECT_COMBINED_PROMPT_TEMPLATE
              .replace("{product_name}", name)
              .replace("{brand_name}", brand_name)
              .replace("{product_type}", product_type))

    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=prompt,
        input=f"Find Canadian purchase path and pros/cons for: {name} by {brand_name}",
        tools=[{"type": "web_search", "search_context_size": "medium"}],
        text={"format": {"type": "json_schema", "name": "inject_combined", "strict": True, "schema": INJECT_COMBINED_SCHEMA}},
    )
    text = _response_plain_text(response)
    parsed = json.loads(text) if text.strip() else {}
    norm = normalize_buyability(parsed)

    price = norm.get("price_cad")
    if price is not None:
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = None
            norm["price_cad"] = None

    status = "verified" if norm.get("canada_verified") else "not found"
    price_str = f"${price:.2f}" if price else "N/A"
    stock_str = "in stock" if norm.get("in_stock") else "out of stock"
    sale_flag = " (sale)" if norm.get("is_on_sale") else ""
    print(f"      {status} | {norm.get('retailer', 'N/A')} | {price_str}{sale_flag} | {stock_str}")

    def _clamp(items, *, max_items=5, max_len=110):
        out = []
        for x in (items if isinstance(items, list) else [])[:max_items]:
            if not isinstance(x, str):
                continue
            s = " ".join(x.split()).strip()
            if len(s) > max_len:
                s = s[:max_len - 1] + "\u2026"
            if s:
                out.append(s)
        return out

    positives = _clamp(parsed.get("positives") or [])
    negatives = _clamp(parsed.get("negatives") or [])
    print(f"      pros/cons: {len(positives)} strength(s), {len(negatives)} drawback(s)")

    return {
        "canonical_product_id": None,
        "canonical_product_name": name,
        "brand": brand_name,
        "model": "",
        "retailer": norm.get("retailer"),
        "product_url": norm.get("product_url"),
        "price_cad": price,
        "original_price_cad": norm.get("original_price_cad"),
        "is_on_sale": norm.get("is_on_sale", False),
        "in_stock": norm.get("in_stock"),
        "canada_verified": norm.get("canada_verified", False),
        "alternative_retailers": norm.get("alternative_retailers", []),
        "canadian_company": False,
        "made_in_canada": False,
        "notes": "Canadian brand product (not reviewer-backed)",
        "positives": positives,
        "negatives": negatives,
    }


def _load_cached_canadian_brands(data_dir):
    """Load broad-search Canadian brand results from a prior canada_purchase_paths.json."""
    cache_path = data_dir / "canada_purchase_paths.json"
    if not cache_path.exists():
        return []
    try:
        with open(cache_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    brands = data.get("canadian_brands", [])
    return [b for b in brands if isinstance(b, dict) and b.get("canadian_company")]


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
    brand_origins = verify_brand_origins(
        dataset_brands,
        product_type,
        data_dir,
        refresh,
        workers,
    )
    known_origins = known_brand_origins_from_config(cfg)
    if known_origins:
        print(f"  Configured Canadian brand override(s): {len(known_origins)}")
        brand_origins.update(known_origins)
        save_brand_origins(data_dir, brand_origins)

    # Load cached broad-search results from a previous run (if any)
    cached_canadian_brands = _load_cached_canadian_brands(data_dir)

    if refresh or not cached_canadian_brands:
        try:
            discovered_canadian_brands = find_canadian_brands(
                product_type,
                product_type_plural,
                dataset_brands,
            )
        except Exception as e:
            print(f"    Broad Canadian brand search failed ({e}), using cached/B1 results only")
            discovered_canadian_brands = cached_canadian_brands
    else:
        print(f"\n  Part B: Using {len(cached_canadian_brands)} cached Canadian brand(s) from prior run")
        for b in cached_canadian_brands:
            print(f"      - {b.get('brand_name', 'unknown')}")
        discovered_canadian_brands = cached_canadian_brands

    discovered_by_key = {
        normalize_brand_name(b.get("brand_name")): b
        for b in discovered_canadian_brands
        if b.get("canadian_company")
    }

    # Only consider Canadian brands that are actually in this category's dataset
    # or were found by the broad search (Part B). Don't inject brands from the
    # global cache that belong to unrelated categories.
    dataset_brand_keys = {normalize_brand_name(b) for b in dataset_brands}
    combined_canadian_by_key = {}
    for key, origin in brand_origins.items():
        if origin.get("canadian_company") and key in dataset_brand_keys:
            combined_canadian_by_key[key] = origin
    for key, discovered in discovered_by_key.items():
        if key:
            combined_canadian_by_key.setdefault(key, discovered)

    for pp in purchase_paths:
        key = normalize_brand_name(pp.get("brand"))
        origin = brand_origins.get(key, {})
        discovered = discovered_by_key.get(key, {})
        if origin.get("canadian_company") or discovered.get("canadian_company"):
            pp["canadian_company"] = True
            pp["made_in_canada"] = bool(
                origin.get("made_in_canada") or discovered.get("made_in_canada")
            )

    canadian_brands = list(combined_canadian_by_key.values())

    # Part C: Inject top product for Canadian brands not already in the dataset
    existing_brand_keys = {
        normalize_brand_name(pp.get("brand"))
        for pp in purchase_paths
        if pp.get("brand")
    }
    for cb in canadian_brands:
        if not cb.get("canadian_company"):
            continue
        bname = cb.get("brand_name", "")
        bkey = normalize_brand_name(bname)
        if any(bkey == key or (bkey and key and (bkey in key or key in bkey)) for key in existing_brand_keys):
            continue
        pre_product = cb.get("top_product") or None
        print(f"\n  Part C: Injecting top product for Canadian brand '{bname}'...")
        try:
            injected = inject_canadian_product(bname, product_type, buyability_prompt, price_min, price_max, pre_discovered_product=pre_product)
        except Exception as e:
            print(f"      Injection failed ({e}), skipping brand")
            continue
        if injected:
            injected["canadian_company"] = True
            injected["made_in_canada"] = cb.get("made_in_canada", False)
            injected["reviewer_backed"] = False
            purchase_paths.append(injected)
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
