"""
Merge drip, budget drip, espresso, french press, and Nespresso site JSON into
one guide: public/coffee/site_products.json + site_featured_picks.json

Run: python3 scripts/build_coffee_guide_bundle.py
"""

import json
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "frontend" / "public"


def prefix_products(products: list, prefix: str) -> list:
    out = []
    for p in products:
        q = dict(p)
        old_id = p["id"]
        q["id"] = f"{prefix}__{old_id}"
        # Keep source context in recommendations line (optional)
        out.append(q)
    return out


def prefix_id(old: Optional[str], prefix: str) -> Optional[str]:
    if old is None:
        return None
    return f"{prefix}__{old}"


def load_products(cat: str) -> list:
    path = PUBLIC / cat / "site_products.json"
    with open(path) as f:
        return json.load(f)


def load_picks(cat: str) -> list:
    path = PUBLIC / cat / "site_featured_picks.json"
    with open(path) as f:
        return json.load(f)


def pick_by_role(picks: list, role: str) -> dict:
    for p in picks:
        if p.get("role") == role:
            return p
    return {}


def main():
    sections = [
        {
            "slug": "drip",
            "source_cat": "drip_coffee_maker",
            "role": "guide_drip_overall",
            "role_display": "Best drip coffee maker (overall)",
            "pick_role": "best_overall",
        },
        {
            "slug": "budget_drip",
            "source_cat": "budget_drip_coffee_maker",
            "role": "guide_budget_drip",
            "role_display": "Best budget drip coffee maker",
            "pick_role": "best_budget",
        },
        {
            "slug": "espresso",
            "source_cat": "espresso_machine",
            "role": "guide_espresso_grinder",
            "role_display": "Best espresso machine (with built-in grinder)",
            "pick_role": "best_overall",
        },
        {
            "slug": "french",
            "source_cat": "french_press",
            "role": "guide_french_press",
            "role_display": "Best French press",
            "pick_role": "best_overall",
        },
        {
            "slug": "nespresso",
            "source_cat": "nespresso_machine",
            "role": "guide_nespresso",
            "role_display": "Best Nespresso machine",
            "pick_role": "best_overall",
        },
    ]

    badges = {
        "guide_drip_overall": "Top pick",
        "guide_budget_drip": "Budget pick",
        "guide_espresso_grinder": "Top pick",
        "guide_french_press": "Top pick",
        "guide_nespresso": "Top pick",
    }

    all_products: list = []
    combined: list = []

    for sec in sections:
        prefix = sec["slug"]
        prods = load_products(sec["source_cat"])
        all_products.extend(prefix_products(prods, prefix))

        src_pick = pick_by_role(load_picks(sec["source_cat"]), sec["pick_role"])
        if not src_pick.get("name"):
            continue
        combined.append(
            {
                "role": sec["role"],
                "role_display": sec["role_display"],
                "badge": badges.get(sec["role"], ""),
                "id": prefix_id(src_pick.get("id"), prefix),
                "name": src_pick.get("name"),
                "price_cad": src_pick.get("price_cad"),
                "price_display": src_pick.get("price_display"),
                "retailer": src_pick.get("retailer"),
                "use_case": src_pick.get("use_case"),
                "reason": src_pick.get("reason", ""),
                "source_count": src_pick.get("source_count"),
                "canadianness_tier": src_pick.get("canadianness_tier"),
                "recommendations": src_pick.get("recommendations", []),
            }
        )

    # Canadian pick from french press (ESPRO is Vancouver-based)
    fp_picks = load_picks("french_press")
    ca_pick = pick_by_role(fp_picks, "best_canadian_option")
    if ca_pick.get("name"):
        combined.append(
            {
                "role": "best_canadian_option",
                "role_display": "Canadian-owned company to know",
                "badge": "Canadian pick",
                "id": prefix_id(ca_pick.get("id"), "french"),
                "name": ca_pick.get("name"),
                "price_cad": ca_pick.get("price_cad"),
                "price_display": ca_pick.get("price_display"),
                "retailer": ca_pick.get("retailer"),
                "use_case": ca_pick.get("use_case"),
                "reason": (
                    "Our Canadian-angle pick: ESPRO is headquartered in Vancouver, BC. "
                    "The P3 is also our French press winner\u2014a rare case where the "
                    "best press comes from a Canadian company."
                ),
                "source_count": ca_pick.get("source_count", ca_pick.get("cross_source_count")),
                "canadianness_tier": ca_pick.get("canadianness_tier"),
                "recommendations": ca_pick.get("recommendations", []),
            }
        )

    out_dir = PUBLIC / "coffee"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "site_products.json", "w") as f:
        json.dump(all_products, f, indent=2)
    with open(out_dir / "site_featured_picks.json", "w") as f:
        json.dump(combined, f, indent=2)

    # Single category entry for the site index
    cats_path = PUBLIC / "categories.json"
    with open(cats_path) as f:
        cats = json.load(f)
    strip = {
        "drip_coffee_maker",
        "budget_drip_coffee_maker",
        "espresso_machine",
        "french_press",
        "nespresso_machine",
    }
    cats = [c for c in cats if c["id"] not in strip]
    entry = {
        "id": "coffee",
        "name": "Coffee & Espresso",
        "product_count": len(all_products),
    }
    cats = [c for c in cats if c["id"] != "coffee"]
    cats.append(entry)
    cats.sort(key=lambda c: c["name"].lower())
    with open(cats_path, "w") as f:
        json.dump(cats, f, indent=2)

    print(f"Wrote {out_dir}/ with {len(combined)} guide sections, {len(all_products)} products")
    print("Updated categories.json (removed split coffee categories, added coffee)")


if __name__ == "__main__":
    main()
