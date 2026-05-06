"""
Shared config loader for the pipeline scripts.
Reads category JSON from categories/<category_id>.json based on --category CLI arg.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get_category_config():
    category_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--category" and i + 1 < len(sys.argv):
            category_id = sys.argv[i + 1]
            break

    if not category_id:
        print("ERROR: --category argument required. Example: --category robot_vacuum")
        sys.exit(1)

    config_path = ROOT / "categories" / f"{category_id}.json"
    if not config_path.exists():
        print(f"ERROR: Category config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        cfg = json.load(f)

    data_dir = ROOT / "data" / category_id
    data_dir.mkdir(parents=True, exist_ok=True)

    cfg["_category_id"] = category_id
    cfg["_data_dir"] = data_dir

    return cfg
