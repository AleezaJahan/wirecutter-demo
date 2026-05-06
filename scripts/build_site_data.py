"""
Script 6: build_site_data.py

Prepare final JSON for the landing page.
Pure Python — NO AI, NO web search.

Usage: python3 scripts/build_site_data.py --category robot_vacuum
"""

import json
import sys
from pathlib import Path
from config import get_category_config

sys.stdout.reconfigure(line_buffering=True)

FRONTEND_DATA = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"


def flatten_product(p):
    orig = p.get("original_price_cad")
    try:
        orig_f = float(orig) if orig is not None else None
    except (TypeError, ValueError):
        orig_f = None
    alts = p.get("alternative_retailers") or []
    alt_out = []
    for a in alts:
        if not isinstance(a, dict):
            continue
        pc = a.get("price_cad")
        try:
            pc_f = float(pc) if pc is not None else None
        except (TypeError, ValueError):
            pc_f = None
        alt_out.append({
            "retailer": a.get("retailer") or "N/A",
            "product_url": a.get("product_url") or "",
            "price_display": f"${pc_f:.2f}" if pc_f is not None else None,
        })
    return {
        "id": p["canonical_product_id"],
        "name": p["canonical_product_name"],
        "brand": p["brand"],
        "model": p["model"],
        "price_cad": p.get("price_cad"),
        "price_display": f"${p['price_cad']:.2f}" if p.get("price_cad") else "N/A",
        "original_price_cad": orig_f,
        "original_price_display": f"${orig_f:.2f}" if orig_f is not None else None,
        "is_on_sale": bool(p.get("is_on_sale", False)),
        "retailer": p.get("retailer") or "N/A",
        "product_url": p.get("product_url") or "",
        "in_stock": bool(p.get("in_stock")),
        "canada_verified": bool(p.get("canada_verified")),
        "canadian_company": bool(p.get("canadian_company")),
        "made_in_canada": bool(p.get("made_in_canada")),
        "canadianness_tier": p.get("canadianness_tier"),
        "alternative_retailers": alt_out,
        "sources": p.get("sources", []),
        "source_count": p.get("cross_source_count", 0),
        "recommendations": p.get("recommendation_types", []),
        "positives": p.get("positives", []),
        "negatives": p.get("negatives", []),
        "notes": p.get("notes", ""),
    }


def sentence_case(text):
    if not text:
        return text
    text = str(text).strip()
    return text[:1].upper() + text[1:]


def normalize_feature_phrase(text):
    if not text:
        return text
    text = str(text).strip().rstrip(".")
    text = text.lower()
    replacements = {
        " anc": " ANC",
        " lidar": " LiDAR",
        " cad": " CAD",
        " eq": " EQ",
        " kpa": " kPa",
        " pa ": " Pa ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def clean_use_case(text):
    if not text:
        return text
    text = " ".join(str(text).split()).strip()
    lowered = text.lower()
    for prefix in ("best ", "top "):
        if lowered.startswith(prefix):
            return text[len(prefix):]
    return text


def feature_summary(product):
    positives = product.get("positives", []) if product else []
    for item in positives:
        if not isinstance(item, str):
            continue
        clean = " ".join(item.split()).strip().rstrip(".")
        if clean:
            return normalize_feature_phrase(clean)
    return ""


def build_pick_context(role, pick, product):
    """Create shopper-facing context from structured fields, not internal ranking notes."""
    if pick.get("context"):
        return pick["context"]

    features = feature_summary(product)
    use_case = pick.get("use_case")

    strength = f" It stands out for {features}." if features else ""

    if role == "best_budget":
        if features:
            return f"A lower-priced option for shoppers who want the essentials without paying flagship prices.{strength}"
        return "A lower-priced option for shoppers who want the basics without paying for every premium feature."

    if role == "best_upgrade":
        if features:
            return f"A premium option for shoppers who want more capability and convenience.{strength}"
        return "A premium option for shoppers who want more capability, convenience, and room to grow."

    if role == "best_for_specific_use_case":
        clean_case = clean_use_case(use_case)
        if clean_case and features:
            return f"Best if you care most about {clean_case.lower()}.{strength}"
        if use_case:
            return f"Best if you care most about {clean_case.lower()}."
        if features:
            return f"A strong alternative for a more specific need.{strength}"
        return "A strong alternative for shoppers with a more specific use case."

    if role == "best_canadian_option":
        if features:
            return f"A Canadian-owned brand option available through a Canadian retailer.{strength}"
        return "A Canadian-owned brand option available through a Canadian retailer."

    if features:
        return f"The best default choice for most shoppers.{strength}"
    return "The best default choice for most shoppers who want a reliable recommendation without sorting through every option."


def flatten_pick(role, pick, product_by_id):
    if pick is None:
        return {
            "role": role,
            "role_display": role.replace("_", " ").title(),
            "id": None,
            "name": None,
            "price_display": None,
            "retailer": None,
            "reason": "No qualifying product found.",
        }
    product = product_by_id.get(pick.get("canonical_product_id"), {})
    return {
        "role": role,
        "role_display": role.replace("_", " ").title(),
        "id": pick.get("canonical_product_id"),
        "name": pick.get("canonical_product_name"),
        "price_cad": pick.get("price_cad"),
        "price_display": f"${pick['price_cad']:.2f}" if pick.get("price_cad") else "N/A",
        "retailer": pick.get("retailer") or "N/A",
        "use_case": pick.get("use_case"),
        "context": build_pick_context(role, pick, product),
        "reason": pick.get("reason", ""),
        "source_count": pick.get("cross_source_count", 0),
        "canadianness_tier": pick.get("canadianness_tier"),
        "recommendations": pick.get("recommendation_types", []),
    }


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]

    print("=" * 60)
    print(f"Script 6: Building site data [{category_id}]")
    print("=" * 60)

    out_dir = FRONTEND_DATA / category_id
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(data_dir / "merged_products.json") as f:
        merged = json.load(f)

    with open(data_dir / "featured_picks.json") as f:
        featured = json.load(f)

    site_products = [flatten_product(p) for p in merged["products"]]
    product_by_id = {
        p["canonical_product_id"]: p
        for p in merged["products"]
    }

    with open(out_dir / "site_products.json", "w") as f:
        json.dump(site_products, f, indent=2)

    picks = featured["picks"]
    role_order = ["best_overall", "best_budget", "best_upgrade", "best_for_specific_use_case", "best_canadian_option"]
    site_picks = [flatten_pick(role, picks.get(role), product_by_id) for role in role_order]

    with open(out_dir / "site_featured_picks.json", "w") as f:
        json.dump(site_picks, f, indent=2)

    # Also write a categories index for the frontend
    categories_index_path = FRONTEND_DATA / "categories.json"
    existing = []
    if categories_index_path.exists():
        with open(categories_index_path) as f:
            existing = json.load(f)

    cat_entry = {
        "id": category_id,
        "name": cfg.get("category_name", category_id),
        "product_count": len(site_products),
    }
    existing = [c for c in existing if c["id"] != category_id]
    existing.append(cat_entry)
    existing.sort(key=lambda c: c["name"])

    with open(categories_index_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"  Wrote {len(site_products)} products to frontend/src/data/{category_id}/site_products.json")
    print(f"  Wrote {len(site_picks)} featured picks to frontend/src/data/{category_id}/site_featured_picks.json")
    print(f"  Updated categories index at frontend/src/data/categories.json")
    print("Done.")


if __name__ == "__main__":
    main()
