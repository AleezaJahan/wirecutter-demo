"""
Script 5: select_featured_picks.py

Choose a small set of featured products using deterministic rules.
Pure Python — NO AI, NO web search.

Usage: python3 scripts/select_featured_picks.py --category robot_vacuum
"""

import json
import sys
from config import get_category_config

sys.stdout.reconfigure(line_buffering=True)


def sort_key(p):
    return (-p["cross_source_count"], p.get("price_cad") or 99999)


def sort_key_upgrade(p):
    return (-p["cross_source_count"], -(p.get("price_cad") or 0))


def has_keyword_match(recommendation_types, keywords):
    for rt in recommendation_types:
        rt_lower = rt.lower()
        for kw in keywords:
            if kw in rt_lower:
                return True
    return False


def get_use_case_label(recommendation_types, use_case_keywords):
    for rt in recommendation_types:
        rt_lower = rt.lower()
        for kw in use_case_keywords:
            if kw in rt_lower:
                return rt
    return None


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]

    rules = cfg.get("featured_picks_rules", {})
    budget_ceiling = rules.get("budget_ceiling", 500)
    upgrade_floor = rules.get("upgrade_floor", 1000)
    overall_keywords = rules.get("overall_keywords", ["best overall", "#1"])
    use_case_keywords = rules.get("use_case_keywords", ["pet", "mop", "hair"])

    print("=" * 60)
    print(f"Script 5: Selecting featured picks [{category_id}]")
    print("=" * 60)

    with open(data_dir / "merged_products.json") as f:
        data = json.load(f)

    products = data["products"]
    assigned_ids = set()

    eligible = [
        p for p in products
        if p.get("canada_verified")
        and p.get("in_stock")
        and p.get("price_cad") is not None
    ]

    print(f"  Eligible pool: {len(eligible)} products (verified, in stock, priced)")
    print(f"  Budget ceiling: ${budget_ceiling} | Upgrade floor: ${upgrade_floor}")

    picks = {}

    # --- best_overall ---
    pool = sorted(eligible, key=sort_key)
    if pool:
        top_count = pool[0]["cross_source_count"]
        top_tier = [p for p in pool if p["cross_source_count"] == top_count and p["canonical_product_id"] not in assigned_ids]
        keyword_matches = [p for p in top_tier if has_keyword_match(p.get("recommendation_types", []), overall_keywords)]
        best_overall = keyword_matches[0] if keyword_matches else (top_tier[0] if top_tier else None)
    else:
        best_overall = None
    if best_overall:
        assigned_ids.add(best_overall["canonical_product_id"])
        picks["best_overall"] = {
            "canonical_product_id": best_overall["canonical_product_id"],
            "canonical_product_name": best_overall["canonical_product_name"],
            "price_cad": best_overall["price_cad"],
            "retailer": best_overall["retailer"],
            "cross_source_count": best_overall["cross_source_count"],
            "recommendation_types": best_overall.get("recommendation_types", []),
            "reason": f"Top pick with {best_overall['cross_source_count']} reviewer source(s). Recommended as: {', '.join(best_overall.get('recommendation_types', []))}",
        }
        print(f"  best_overall: {best_overall['canonical_product_name']} (${best_overall['price_cad']})")

    # --- best_budget ---
    budget_pool = [p for p in eligible if (p.get("price_cad") or 99999) <= budget_ceiling]
    budget_pool.sort(key=sort_key)
    best_budget = None
    for p in budget_pool:
        if p["canonical_product_id"] not in assigned_ids:
            best_budget = p
            break
    if best_budget:
        assigned_ids.add(best_budget["canonical_product_id"])
        picks["best_budget"] = {
            "canonical_product_id": best_budget["canonical_product_id"],
            "canonical_product_name": best_budget["canonical_product_name"],
            "price_cad": best_budget["price_cad"],
            "retailer": best_budget["retailer"],
            "cross_source_count": best_budget["cross_source_count"],
            "recommendation_types": best_budget.get("recommendation_types", []),
            "reason": f"Best budget option at ${best_budget['price_cad']} (under ${budget_ceiling} ceiling) with {best_budget['cross_source_count']} reviewer source(s).",
        }
        print(f"  best_budget: {best_budget['canonical_product_name']} (${best_budget['price_cad']})")
    else:
        picks["best_budget"] = None
        print("  best_budget: None found")

    # --- best_upgrade ---
    upgrade_pool = [p for p in eligible if (p.get("price_cad") or 0) >= upgrade_floor]
    upgrade_pool.sort(key=sort_key_upgrade)
    best_upgrade = None
    for p in upgrade_pool:
        if p["canonical_product_id"] not in assigned_ids:
            best_upgrade = p
            break
    if best_upgrade:
        assigned_ids.add(best_upgrade["canonical_product_id"])
        picks["best_upgrade"] = {
            "canonical_product_id": best_upgrade["canonical_product_id"],
            "canonical_product_name": best_upgrade["canonical_product_name"],
            "price_cad": best_upgrade["price_cad"],
            "retailer": best_upgrade["retailer"],
            "cross_source_count": best_upgrade["cross_source_count"],
            "recommendation_types": best_upgrade.get("recommendation_types", []),
            "reason": f"Premium upgrade at ${best_upgrade['price_cad']} (above ${upgrade_floor} floor) with {best_upgrade['cross_source_count']} reviewer source(s).",
        }
        print(f"  best_upgrade: {best_upgrade['canonical_product_name']} (${best_upgrade['price_cad']})")
    else:
        picks["best_upgrade"] = None
        print("  best_upgrade: None found")

    # --- best_for_specific_use_case ---
    use_case_pool = [
        p for p in eligible
        if has_keyword_match(p.get("recommendation_types", []), use_case_keywords)
        and p["canonical_product_id"] not in assigned_ids
    ]
    use_case_pool.sort(key=sort_key)
    best_use_case = None
    if use_case_pool:
        best_use_case = use_case_pool[0]
        use_case_label = get_use_case_label(best_use_case.get("recommendation_types", []), use_case_keywords)
        assigned_ids.add(best_use_case["canonical_product_id"])
        picks["best_for_specific_use_case"] = {
            "canonical_product_id": best_use_case["canonical_product_id"],
            "canonical_product_name": best_use_case["canonical_product_name"],
            "price_cad": best_use_case["price_cad"],
            "retailer": best_use_case["retailer"],
            "use_case": use_case_label,
            "cross_source_count": best_use_case["cross_source_count"],
            "recommendation_types": best_use_case.get("recommendation_types", []),
            "reason": f"Top pick for '{use_case_label}' with {best_use_case['cross_source_count']} reviewer source(s).",
        }
        print(f"  best_for_specific_use_case: {best_use_case['canonical_product_name']} ({use_case_label})")
    else:
        picks["best_for_specific_use_case"] = None
        print("  best_for_specific_use_case: None found")

    # --- best_canadian_option ---
    canadian_pool = [p for p in products if p.get("canadian_company")]
    canadian_pool.sort(key=sort_key)
    best_canadian = None
    if canadian_pool:
        best_canadian = canadian_pool[0]
        tier = best_canadian.get("canadianness_tier", "B")
        tier_labels = {"A": "Made/assembled in Canada", "B": "Canadian-owned brand"}
        reviewer_note = "" if best_canadian.get("reviewer_backed", True) else " (not reviewer-backed)"
        picks["best_canadian_option"] = {
            "canonical_product_id": best_canadian["canonical_product_id"],
            "canonical_product_name": best_canadian["canonical_product_name"],
            "price_cad": best_canadian.get("price_cad"),
            "retailer": best_canadian.get("retailer"),
            "in_stock": best_canadian.get("in_stock"),
            "cross_source_count": best_canadian["cross_source_count"],
            "canadianness_tier": tier,
            "reason": f"{tier_labels.get(tier, 'Canadian company')} product{reviewer_note}.",
        }
        print(f"  best_canadian_option: {best_canadian['canonical_product_name']}")
    else:
        picks["best_canadian_option"] = None
        print("  best_canadian_option: None (no Canadian companies in dataset)")

    output = {
        "metadata": {
            "category": category_id,
            "budget_ceiling": budget_ceiling,
            "upgrade_floor": upgrade_floor,
            "eligible_pool_size": len(eligible),
        },
        "picks": picks,
    }

    out_path = data_dir / "featured_picks.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Saved to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
