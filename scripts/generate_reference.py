#!/usr/bin/env python3
"""
Validate and reformat reference data JSON files.

The JSON files in data/ are the source of truth for gazetteer, routes,
and hull profile data.  This script loads them via the Python modules
(which validates structure) and writes them back (which normalises
formatting).

Run after editing any reference JSON file to verify and reformat:

    python scripts/generate_reference.py

Validates:
    data/gazetteer.json     -- ~170 VOC-era place names with coordinates
    data/routes.json        -- 18 historical sailing routes with waypoints (5 nations)
    data/hull_profiles.json -- 6 ship type hydrodynamic profiles
"""

import json
import sys
from pathlib import Path

from download_utils import is_cached, parse_args

# Add project root to path so we can import the source modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

DATA_DIR = PROJECT_ROOT / "data"


def validate_gazetteer() -> Path:
    """Validate and reformat gazetteer JSON."""
    from chuk_mcp_maritime_archives.core.voc_gazetteer import VOC_GAZETTEER

    entries = []
    for name, entry in VOC_GAZETTEER.items():
        entries.append({"name": name, **entry})

    path = DATA_DIR / "gazetteer.json"
    with open(path, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    return path


def validate_routes() -> Path:
    """Validate and reformat routes JSON."""
    from chuk_mcp_maritime_archives.core.voc_routes import VOC_ROUTES

    routes = []
    for route_id, route in VOC_ROUTES.items():
        routes.append({"route_id": route_id, **route})

    path = DATA_DIR / "routes.json"
    with open(path, "w") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)
    return path


def validate_hull_profiles() -> Path:
    """Validate and reformat hull profiles JSON."""
    from chuk_mcp_maritime_archives.core.hull_profiles import HULL_PROFILES

    profiles = list(HULL_PROFILES.values())

    path = DATA_DIR / "hull_profiles.json"
    with open(path, "w") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    return path


def main() -> None:
    args = parse_args("Validate and reformat reference data")

    print("=" * 60)
    print("Reference Data Validation — chuk-mcp-maritime-archives")
    print("=" * 60)
    print(f"\nData directory: {DATA_DIR}\n")

    gazetteer_path = DATA_DIR / "gazetteer.json"
    if not args.force and is_cached(gazetteer_path, args.cache_max_age):
        print("Using cached reference data (use --force to regenerate)")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Step 1: Validating gazetteer.json...")
    p1 = validate_gazetteer()
    print(f"  {p1} ({p1.stat().st_size:,} bytes)")

    print("\nStep 2: Validating routes.json...")
    p2 = validate_routes()
    print(f"  {p2} ({p2.stat().st_size:,} bytes)")

    print("\nStep 3: Validating hull_profiles.json...")
    p3 = validate_hull_profiles()
    print(f"  {p3} ({p3.stat().st_size:,} bytes)")

    print(f"\n{'=' * 60}")
    print("Reference data validation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
