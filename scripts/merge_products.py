"""
Script 4: merge_products.py

Merge reviewer and Canada data into one product record.
Pure Python — NO AI, NO web search.

Usage: python3 scripts/merge_products.py --category robot_vacuum
"""

import json
import sys
from pathlib import Path
from config import get_category_config

sys.stdout.reconfigure(line_buffering=True)


def main():
    cfg = get_category_config()
    data_dir = cfg["_data_dir"]
    category_id = cfg["_category_id"]

    print("=" * 60)
    print(f"Script 4: Merging products [{category_id}]")
    print("=" * 60)

    with open(data_dir / "canonical_products.json") as f:
        cp_data = json.load(f)

    with open(data_dir / "reviewer_records_canonicalized.json") as f:
        rr_data = json.load(f)

    with open(data_dir / "canada_purchase_paths.json") as f:
        ca_data = json.load(f)

    canonical_products = cp_data["canonical_products"]
    reviewer_records = rr_data["records"]
    purchase_paths = ca_data["purchase_paths"]

    # Load needs_review flags
    nr_path = data_dir / "needs_review.json"
    needs_review_ids = set()
    if nr_path.exists():
        with open(nr_path) as f:
            nr_data = json.load(f)
        for item in nr_data.get("needs_review", []):
            raw_name = item.get("raw_product_name", "").lower().strip()
            for cp in canonical_products:
                if raw_name in [n.lower().strip() for n in cp.get("raw_names", [])]:
                    needs_review_ids.add(cp["canonical_product_id"])

    ca_by_id = {pp["canonical_product_id"]: pp for pp in purchase_paths}

    merged = []
    for cp in canonical_products:
        pid = cp["canonical_product_id"]

        matching_reviews = [
            r for r in reviewer_records
            if r.get("canonical_product_id") == pid
        ]

        sources = list(set(r["source_name"] for r in matching_reviews))
        cross_source_count = len(sources)

        recommendation_types = [
            r.get("recommendation_type")
            for r in matching_reviews
            if r.get("recommendation_type")
        ]

        all_positives = []
        all_negatives = []
        use_cases = []
        for r in matching_reviews:
            if r.get("positives"):
                all_positives.extend(r["positives"])
            if r.get("negatives"):
                all_negatives.extend(r["negatives"])
            if r.get("specific_use_case"):
                use_cases.append(r["specific_use_case"])

        ca = ca_by_id.get(pid, {})

        product = {
            "canonical_product_id": pid,
            "canonical_product_name": cp["canonical_product_name"],
            "brand": cp["brand"],
            "model": cp["model"],
            "sources": sources,
            "cross_source_count": cross_source_count,
            "recommendation_types": recommendation_types,
            "positives": list(set(all_positives)),
            "negatives": list(set(all_negatives)),
            "specific_use_cases": list(set(use_cases)),
            "retailer": ca.get("retailer"),
            "product_url": ca.get("product_url"),
            "price_cad": ca.get("price_cad"),
            "in_stock": ca.get("in_stock"),
            "canada_verified": ca.get("canada_verified", False),
            "canadian_company": ca.get("canadian_company", False),
            "made_in_canada": ca.get("made_in_canada", False),
            "canadianness_tier": (
                "A" if ca.get("made_in_canada") else
                "B" if ca.get("canadian_company") else
                "C" if ca.get("canada_verified") else
                None
            ),
            "reviewer_backed": ca.get("reviewer_backed", True),
            "needs_review": pid in needs_review_ids,
            "notes": ca.get("notes", ""),
        }
        merged.append(product)

    merged.sort(key=lambda x: (-x["cross_source_count"], x.get("price_cad") or 99999))

    output = {
        "metadata": {
            "category": category_id,
            "total_products": len(merged),
            "canada_verified_count": sum(1 for m in merged if m["canada_verified"]),
            "in_stock_count": sum(1 for m in merged if m.get("in_stock")),
        },
        "products": merged,
    }

    out_path = data_dir / "merged_products.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Merged {len(merged)} products")
    print(f"  Canada verified: {output['metadata']['canada_verified_count']}")
    print(f"  In stock: {output['metadata']['in_stock_count']}")
    print(f"  Saved to {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
