"""
Script 3: verify_canada_purchase_paths.py

Check whether canonical products have a credible Canadian purchase path.
Uses OpenAI Responses API with web_search tool.

Part A: Buyability (retailer, url, price, stock, verified)
Part B: Canadian brand signals (canadian_company, made_in_canada)

Usage: python3 scripts/verify_canada_purchase_paths.py --category robot_vacuum
"""

import json
import os
import re
import sys
import requests
import time
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
3. LAST RESORT: Amazon.ca (only if nothing found above)

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

Your job is to THOROUGHLY search the web for any {product_type} brands that are:
1. Canadian-founded companies, OR
2. Companies headquartered in Canada, OR
3. Brands that manufacture or assemble {product_type_plural} in Canada

IMPORTANT SEARCH INSTRUCTIONS:
- Search for "Canadian {product_type} brands" and "Canadian {product_type} companies"
- Search for "{product_type} brands headquartered in Canada"
- Search for "{product_type} made in Canada" and "{product_type} assembled in Canada"
- Also check if any of these specific brands are Canadian: {brands_to_check}
- Look beyond the major international brands. Smaller or niche Canadian companies count too.
- Do NOT assume no Canadian brands exist. Search thoroughly before concluding.

ONLY return brands that ARE Canadian (founded, headquartered, or manufacturing in Canada).
Do NOT return non-Canadian brands.

For each Canadian brand found, provide:
- brand_name
- headquarters_location (city, province)
- canadian_company (true/false)
- made_in_canada (true/false)
- notes (brief explanation)

Return a JSON array. Empty array [] if none found.
Return ONLY the JSON. No markdown. No explanation.
"""


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

    buyability_prompt = BUYABILITY_PROMPT_TEMPLATE.replace("{product_type}", product_type)

    print("=" * 60)
    print(f"Script 3: Verifying Canada purchase paths [{category_id}]")
    print("=" * 60)

    with open(data_dir / "canonical_products.json") as f:
        data = json.load(f)

    products = data["canonical_products"]
    print(f"  Processing {len(products)} canonical products\n")

    print("  Part A: Checking buyability in Canada...")
    purchase_paths = []
    for product in products:
        result = verify_product(product, buyability_prompt, price_min, price_max)
        purchase_paths.append(result)
        time.sleep(1)

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
