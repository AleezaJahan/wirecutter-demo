"""
Script 6: build_site_data.py

Prepare final JSON for the landing page.
Pure Python — NO AI, NO web search.

Usage: python3 scripts/build_site_data.py --category robot_vacuum
"""

import json
import re
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
        "price_display": f"${p['price_cad']:.2f}" if p.get("price_cad") is not None else "N/A",
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
        "recommendations": sanitize_recommendations(p.get("recommendation_types", [])),
        "positives": p.get("positives", []),
        "negatives": p.get("negatives", []),
        "positives_detail": p.get("positives_detail", []),
        "negatives_detail": p.get("negatives_detail", []),
        "notes": p.get("notes", ""),
    }


def normalize_text(text):
    return " ".join(str(text).split()).strip()


def to_sentence(text):
    if not text:
        return ""
    text = normalize_text(text).rstrip(".")
    if not text:
        return ""
    return f"{text}."


def recommendation_is_internal(text):
    if not text:
        return True
    t = normalize_text(text)
    lower = t.lower()
    if not t:
        return True
    if "£" in t:
        return True
    if re.fullmatch(r"#\d+(\s+ranked)?", lower):
        return True
    purely_internal = [
        "under $",
        "under £",
        "notable mention",
    ]
    if any(fragment in lower for fragment in purely_internal):
        return True
    purely_internal_exact = {
        "reviewed", "recommended", "runner-up", "runner up",
        "also great", "honorable mention",
    }
    return lower.strip() in purely_internal_exact


def sanitize_recommendations(items):
    out = []
    seen = set()
    for raw in items or []:
        if not isinstance(raw, str):
            continue
        text = normalize_text(raw)
        if not text or recommendation_is_internal(text):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def product_blurb(product, pick):
    positives = product.get("positives", []) if product else []
    cleaned = []
    for item in positives:
        if not isinstance(item, str):
            continue
        sentence = to_sentence(item)
        if sentence:
            cleaned.append(sentence)
    # Use product positives directly as the card blurb (no templated framing).
    if cleaned:
        return " ".join(cleaned[:2])
    use_case = pick.get("use_case")
    if isinstance(use_case, str) and use_case.strip():
        return f"Best for {normalize_text(use_case).rstrip('.')}."
    return ""


def feature_summary(product):
    positives = product.get("positives", []) if product else []
    for item in positives:
        if not isinstance(item, str):
            continue
        clean = normalize_text(item).rstrip(".")
        if clean:
            return clean
    return ""


def build_pick_context(role, pick, product):
    """Create shopper-facing context from structured fields, not internal ranking notes."""
    if pick.get("context"):
        return pick["context"]
    blurb = product_blurb(product, pick)
    if blurb:
        return blurb
    features = feature_summary(product)
    return to_sentence(features) if features else ""


def flatten_pick(role, pick, product_by_id, existing_picks_by_role=None):
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

    # Preserve image_url from a prior run's output so Step 7 doesn't need to re-fetch
    image_url = None
    if existing_picks_by_role:
        prev = existing_picks_by_role.get(role)
        if prev and prev.get("id") == pick.get("canonical_product_id"):
            image_url = prev.get("image_url")

    result = {
        "role": role,
        "role_display": role.replace("_", " ").title(),
        "id": pick.get("canonical_product_id"),
        "name": pick.get("canonical_product_name"),
        "price_cad": pick.get("price_cad"),
        "price_display": f"${pick['price_cad']:.2f}" if pick.get("price_cad") else "N/A",
        "retailer": pick.get("retailer") or "N/A",
        "use_case": pick.get("use_case"),
        "context": build_pick_context(role, pick, product),
        # Internal ranking logic is intentionally omitted from frontend copy.
        "reason": "",
        "source_count": pick.get("cross_source_count", 0),
        "canadianness_tier": pick.get("canadianness_tier"),
        "recommendations": sanitize_recommendations(pick.get("recommendation_types", [])),
    }
    if image_url:
        result["image_url"] = image_url
    return result


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

    existing_picks_path = out_dir / "site_featured_picks.json"
    existing_picks_by_role = {}
    if existing_picks_path.exists():
        try:
            with open(existing_picks_path) as f:
                for ep in json.load(f):
                    if isinstance(ep, dict) and ep.get("role"):
                        existing_picks_by_role[ep["role"]] = ep
        except (json.JSONDecodeError, OSError):
            pass

    site_picks = [flatten_pick(role, picks.get(role), product_by_id, existing_picks_by_role) for role in role_order]

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
