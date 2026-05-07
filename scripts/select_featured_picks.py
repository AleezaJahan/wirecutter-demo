"""
Script 5: select_featured_picks.py

Choose a small set of featured products using deterministic rules.
Pure Python — NO AI, NO web search.

Usage: python3 scripts/select_featured_picks.py --category robot_vacuum
"""

import csv
import json
import sys
from config import get_category_config

sys.stdout.reconfigure(line_buffering=True)


def sort_key(p):
    return (-p.get("weighted_score", 0), -p["cross_source_count"], p.get("price_cad") or 99999)


def sort_key_upgrade(p):
    return (-p.get("weighted_score", 0), -p["cross_source_count"], -(p.get("price_cad") or 0))


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
    budget_ceiling_cfg = rules.get("budget_ceiling")
    upgrade_floor_cfg = rules.get("upgrade_floor")
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

    # Auto-compute thresholds from price distribution if not set in config
    prices = sorted(p["price_cad"] for p in eligible if p.get("price_cad"))
    if budget_ceiling_cfg is not None:
        budget_ceiling = budget_ceiling_cfg
    elif len(prices) >= 4:
        budget_ceiling = prices[len(prices) // 4]
    else:
        budget_ceiling = 500

    if upgrade_floor_cfg is not None:
        upgrade_floor = upgrade_floor_cfg
    elif len(prices) >= 4:
        upgrade_floor = prices[3 * len(prices) // 4]
    else:
        upgrade_floor = 1000

    auto_note = ""
    if budget_ceiling_cfg is None or upgrade_floor_cfg is None:
        auto_note = " (auto-computed from price distribution)"

    print(f"  Eligible pool: {len(eligible)} products (verified, in stock, priced)")
    print(f"  Budget ceiling: ${budget_ceiling} | Upgrade floor: ${upgrade_floor}{auto_note}")

    picks = {}

    # --- best_overall ---
    # Exclude products where ALL recommendations are DIY/alternative (not a real product pick)
    diy_indicators = ["diy", "build yourself", "build it yourself", "alternative", "homemade"]
    def is_diy_only(p):
        recs = p.get("recommendation_types", [])
        if not recs:
            return False
        return all(any(dq in rt.lower() for dq in diy_indicators) for rt in recs)

    pool = sorted([p for p in eligible if not is_diy_only(p)], key=sort_key)
    best_overall = pool[0] if pool else None
    if best_overall:
        assigned_ids.add(best_overall["canonical_product_id"])
        picks["best_overall"] = {
            "canonical_product_id": best_overall["canonical_product_id"],
            "canonical_product_name": best_overall["canonical_product_name"],
            "price_cad": best_overall["price_cad"],
            "retailer": best_overall["retailer"],
            "cross_source_count": best_overall["cross_source_count"],
            "weighted_score": best_overall.get("weighted_score", 0),
            "recommendation_types": best_overall.get("recommendation_types", []),
            "reason": f"Highest weighted score ({best_overall.get('weighted_score', 0)} pts from {best_overall['cross_source_count']} source(s)).",
        }
        print(f"  best_overall: {best_overall['canonical_product_name']} (${best_overall['price_cad']}, score: {best_overall.get('weighted_score', 0)})")

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
            "weighted_score": best_budget.get("weighted_score", 0),
            "recommendation_types": best_budget.get("recommendation_types", []),
            "reason": f"Highest score under ${budget_ceiling} ({best_budget.get('weighted_score', 0)} pts from {best_budget['cross_source_count']} source(s)).",
        }
        print(f"  best_budget: {best_budget['canonical_product_name']} (${best_budget['price_cad']}, score: {best_budget.get('weighted_score', 0)})")
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
            "weighted_score": best_upgrade.get("weighted_score", 0),
            "recommendation_types": best_upgrade.get("recommendation_types", []),
            "reason": f"Highest score above ${upgrade_floor} ({best_upgrade.get('weighted_score', 0)} pts from {best_upgrade['cross_source_count']} source(s)).",
        }
        print(f"  best_upgrade: {best_upgrade['canonical_product_name']} (${best_upgrade['price_cad']}, score: {best_upgrade.get('weighted_score', 0)})")
    else:
        picks["best_upgrade"] = None
        print("  best_upgrade: None found")

    # --- best_for_specific_use_case ---
    # Exclude labels that are just budget/value qualifiers — those belong in the budget pick
    budget_exclude = ["budget", "cheap", "affordable", "under $", "under £", "value"]
    use_case_pool = [
        p for p in eligible
        if has_keyword_match(p.get("recommendation_types", []), use_case_keywords)
        and p["canonical_product_id"] not in assigned_ids
        and not all(any(bq in rt.lower() for bq in budget_exclude) for rt in p.get("recommendation_types", []) if any(kw in rt.lower() for kw in use_case_keywords))
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
            "weighted_score": best_use_case.get("weighted_score", 0),
            "recommendation_types": best_use_case.get("recommendation_types", []),
            "reason": f"Top for '{use_case_label}' ({best_use_case.get('weighted_score', 0)} pts from {best_use_case['cross_source_count']} source(s)).",
        }
        print(f"  best_for_specific_use_case: {best_use_case['canonical_product_name']} ({use_case_label}, score: {best_use_case.get('weighted_score', 0)})")
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
            "reason": f"{tier_labels.get(tier, 'Canadian company')}{reviewer_note}.",
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

    # Generate scoring breakdown CSV
    generate_scoring_csv(products, picks, data_dir, category_id)

    print("Done.")


def generate_scoring_csv(products, picks, data_dir, category_id):
    """Write a human-readable CSV showing why each product scored the way it did."""
    # Load reviewer records to get per-source recommendation labels
    rr_path = data_dir / "reviewer_records_canonicalized.json"
    rec_by_product_source = {}
    if rr_path.exists():
        with open(rr_path) as f:
            rr_data = json.load(f)
        for r in rr_data.get("records", []):
            pid = r.get("canonical_product_id")
            src = r.get("source_name")
            rt = r.get("recommendation_type", "")
            if pid and src and rt:
                key = (pid, src)
                if key not in rec_by_product_source:
                    rec_by_product_source[key] = rt
                else:
                    existing = rec_by_product_source[key]
                    if len(rt) > len(existing):
                        rec_by_product_source[key] = rt

    # Build role assignment lookup
    role_for_product = {}
    for role, pick in picks.items():
        if pick and pick.get("canonical_product_id"):
            role_for_product[pick["canonical_product_id"]] = role.replace("_", " ").title()

    # Collect all sources across all products
    all_sources = sorted(set(
        src for p in products for src in p.get("source_strengths", {}).keys()
    ))

    csv_path = data_dir / "scoring_breakdown.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        header = ["Product Name", "Role Assigned", "Price (CAD)", "Total Score", "Sources Count"]
        for src in all_sources:
            header.append(f"{src} - Label")
            header.append(f"{src} - Points")
        header.append("Why Picked")
        writer.writerow(header)

        sorted_products = sorted(products, key=lambda x: (-x.get("weighted_score", 0), -x["cross_source_count"]))

        for p in sorted_products:
            pid = p["canonical_product_id"]
            role = role_for_product.get(pid, "")
            price = p.get("price_cad", "")
            score = p.get("weighted_score", 0)
            src_count = p["cross_source_count"]
            strengths = p.get("source_strengths", {})

            row = [p["canonical_product_name"], role, price, score, src_count]

            for src in all_sources:
                pts = strengths.get(src, "")
                label = rec_by_product_source.get((pid, src), "")
                if not label and src in strengths:
                    strength_val = strengths[src]
                    label = {3: "Top Pick", 2: "Runner-up", 1: "Mentioned"}.get(strength_val, "")
                row.append(label)
                row.append(pts)

            # Why picked explanation
            if role:
                pick_data = picks.get(role.replace(" ", "_").lower(), {})
                reason = pick_data.get("reason", "") if pick_data else ""
                row.append(reason)
            else:
                row.append("")

            writer.writerow(row)

    print(f"  Scoring breakdown saved to {csv_path}")


if __name__ == "__main__":
    main()
