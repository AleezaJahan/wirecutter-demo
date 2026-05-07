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

TIER_SCORES = {"top_pick": 2.0, "strong_pick": 1.5, "mention": 1.0}

# Fallback heuristics for records that lack endorsement_tier
_FALLBACK_TOP = ["best overall", "#1", "top pick", "top tested", "editor's choice", "winner"]
_FALLBACK_RUNNER = ["also great", "runner-up", "runner up", "#2", "#3"]
_FALLBACK_BUDGET = ["budget", "cheap", "affordable", "under $", "under £", "value", "bang for"]


def classify_strength(record):
    """
    Score a reviewer endorsement.
    Uses endorsement_tier directly when available (from LLM extraction).
    Falls back to text heuristics for legacy records.
    """
    tier = record.get("endorsement_tier")
    if tier in TIER_SCORES:
        return TIER_SCORES[tier]

    # Fallback: parse recommendation_type text
    rt = (record.get("recommendation_type") or "").lower()
    if not rt:
        return 1.0
    if any(kw in rt for kw in _FALLBACK_TOP):
        return 2.0
    if any(kw in rt for kw in _FALLBACK_RUNNER):
        return 1.5
    if any(bq in rt for bq in _FALLBACK_BUDGET):
        return 1.0
    if "best" in rt:
        return 1.5
    return 1.0


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

        # Weighted scoring: take the max strength per source
        source_strengths = {}
        for r in matching_reviews:
            src = r["source_name"]
            strength = classify_strength(r)
            source_strengths[src] = max(source_strengths.get(src, 0), strength)
        weighted_score = sum(source_strengths.values())

        all_positives = []
        all_negatives = []
        all_positives_detail = []
        all_negatives_detail = []
        use_cases = []
        for r in matching_reviews:
            if r.get("positives"):
                all_positives.extend(r["positives"])
            if r.get("negatives"):
                all_negatives.extend(r["negatives"])
            if r.get("positives_detail"):
                all_positives_detail.extend(r["positives_detail"])
            if r.get("negatives_detail"):
                all_negatives_detail.extend(r["negatives_detail"])
            if r.get("specific_use_case"):
                use_cases.append(r["specific_use_case"])

        ca = ca_by_id.get(pid, {})

        # Injected Canadian-brand rows (Script 3) may carry positives/negatives without reviewers
        for key, bucket in (
            ("positives", all_positives),
            ("negatives", all_negatives),
        ):
            extra = ca.get(key)
            if isinstance(extra, list):
                bucket.extend(str(x).strip() for x in extra if str(x).strip())

        product = {
            "canonical_product_id": pid,
            "canonical_product_name": cp["canonical_product_name"],
            "brand": cp["brand"],
            "model": cp["model"],
            "sources": sources,
            "cross_source_count": cross_source_count,
            "weighted_score": weighted_score,
            "source_strengths": source_strengths,
            "recommendation_types": recommendation_types,
            "positives": list(set(all_positives)),
            "negatives": list(set(all_negatives)),
            "positives_detail": list(set(all_positives_detail)),
            "negatives_detail": list(set(all_negatives_detail)),
            "specific_use_cases": list(set(use_cases)),
            "retailer": ca.get("retailer"),
            "product_url": ca.get("product_url"),
            "price_cad": ca.get("price_cad"),
            "original_price_cad": ca.get("original_price_cad"),
            "is_on_sale": bool(ca.get("is_on_sale", False)),
            "in_stock": ca.get("in_stock"),
            "canada_verified": ca.get("canada_verified", False),
            "alternative_retailers": ca.get("alternative_retailers") or [],
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

    merged.sort(key=lambda x: (-x["weighted_score"], -x["cross_source_count"], x.get("price_cad") or 99999))

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
