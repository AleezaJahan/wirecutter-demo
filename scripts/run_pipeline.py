"""
Run the full pipeline with minimal arguments.

Usage:
  python3 scripts/run_pipeline.py "noise-cancelling headphones" --sources "RTINGS, SoundGuys, TechRadar"
  python3 scripts/run_pipeline.py "robot vacuums" --sources "RTINGS, Vacuum Wars, Consumer Reports"
  python3 scripts/run_pipeline.py "air purifiers" --sources "RTINGS, Wirecutter, TechRadar" --budget 200 --upgrade 500
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_DIR = ROOT / "categories"
SCRIPTS_DIR = ROOT / "scripts"


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def pluralize(name):
    if name.endswith("s") or name.endswith("es"):
        return name
    if name.endswith("y") and not name.endswith("ey"):
        return name[:-1] + "ies"
    return name + "s"


def build_source_query(source_name, product_type):
    """Generate a sensible default search query for a source."""
    s = source_name.lower()
    if "rtings" in s:
        return (
            f"Go to https://www.rtings.com and search for the best {product_type} recommendations. "
            f"List EVERY {product_type} that RTINGS recommends. "
            f"For each product get: full product name, category it's recommended for, "
            f"detailed pros with specific scores/measurements, detailed cons with specific flaws."
        )
    elif "youtube" in s:
        return (
            f"Search YouTube for '{source_name} best {product_type} 2025 2026'. "
            f"Find their most recent video ranking {product_type}. "
            f"Extract every product mentioned with its ranking and any brief notes."
        )
    else:
        site = source_name.lower().replace(" ", "")
        return (
            f"Search for 'site:{site}.com best {product_type} 2025 2026' and also "
            f"search for '{source_name} best {product_type}' to find their current recommendations. "
            f"Extract every {product_type} from their list. "
            f"For each product get: full name, ranking position or category, "
            f"detailed pros with specific scores/measurements, detailed cons with specific flaws."
        )


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    product_type = sys.argv[1]
    sources = []
    budget = 200
    upgrade = 500
    skip_existing = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--sources" and i + 1 < len(sys.argv):
            sources = [s.strip() for s in sys.argv[i + 1].split(",")]
            i += 2
        elif sys.argv[i] == "--budget" and i + 1 < len(sys.argv):
            budget = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--upgrade" and i + 1 < len(sys.argv):
            upgrade = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--skip-existing":
            skip_existing = True
            i += 1
        else:
            i += 1

    if not sources:
        config_path = CATEGORIES_DIR / f"{slugify(product_type)}.json"
        if config_path.exists():
            skip_existing = False  # will reuse existing
        else:
            print("ERROR: --sources required. Example: --sources \"RTINGS, SoundGuys, TechRadar\"")
            sys.exit(1)

    category_id = slugify(product_type)
    product_plural = pluralize(product_type)
    category_name = product_type.title()

    config = {
        "category_id": category_id,
        "category_name": category_name,
        "product_type": product_type,
        "product_type_plural": product_plural,
        "reviewer_sources": [
            {"source_name": s, "query": build_source_query(s, product_type)}
            for s in sources
        ],
        "price_range": {"min": 20, "max": 5000, "currency": "CAD"},
        "featured_picks_rules": {
            "budget_ceiling": budget,
            "upgrade_floor": upgrade,
            "overall_keywords": ["best overall", "#1", f"best {product_type}"],
            "use_case_keywords": ["travel", "commute", "office", "pet", "budget", "premium"],
        },
    }

    CATEGORIES_DIR.mkdir(exist_ok=True)
    config_path = CATEGORIES_DIR / f"{category_id}.json"

    if config_path.exists() and not skip_existing:
        print(f"Config already exists: {config_path}")
        print("Using existing config. Delete it or edit it to change sources.")
        with open(config_path) as f:
            existing_cfg = json.load(f)
        sources = [s["source_name"] for s in existing_cfg.get("reviewer_sources", [])]
        budget = existing_cfg.get("featured_picks_rules", {}).get("budget_ceiling", budget)
        upgrade = existing_cfg.get("featured_picks_rules", {}).get("upgrade_floor", upgrade)
        category_name = existing_cfg.get("category_name", category_name)
    else:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Created config: {config_path}")

    print(f"\nCategory: {category_name}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Budget ceiling: ${budget} | Upgrade floor: ${upgrade}")
    print()

    scripts = [
        "extract_reviewer_records.py",
        "canonicalize_products.py",
        "verify_canada_purchase_paths.py",
        "merge_products.py",
        "select_featured_picks.py",
        "build_site_data.py",
        "fetch_product_images.py",
        "generate_guide_content.py",
    ]

    for script in scripts:
        script_path = SCRIPTS_DIR / script
        print(f"{'=' * 50}")
        print(f"Running: {script}")
        print(f"{'=' * 50}")
        result = subprocess.run(
            [sys.executable, str(script_path), "--category", category_id],
            cwd=str(SCRIPTS_DIR),
        )
        if result.returncode != 0:
            print(f"\nERROR: {script} failed with exit code {result.returncode}")
            sys.exit(1)
        print()

    print("=" * 50)
    print("Pipeline complete!")
    print(f"  Data: data/{category_id}/")
    print(f"  Site: frontend/src/data/{category_id}/")
    print("=" * 50)


if __name__ == "__main__":
    main()
