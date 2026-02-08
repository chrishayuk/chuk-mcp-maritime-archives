#!/usr/bin/env python3
"""
GeoJSON Export Demo -- chuk-mcp-maritime-archives

Export VOC wreck positions as GeoJSON FeatureCollection for mapping
and GIS analysis. Shows filtering by region, status, and specific
wreck IDs, plus the optional uncertainty and voyage data properties.

Demonstrates:
    maritime_export_geojson (multiple filter combinations)
    maritime_search_wrecks (to find wreck IDs)

Usage:
    python examples/geojson_export_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- GeoJSON Export Demo")
    print("=" * 60)

    # ----- Export 1: All wrecks -------------------------------------
    print("\n1. Export all wreck positions")
    print("-" * 40)

    result = await runner.run("maritime_export_geojson")
    print(f"   Features: {result['feature_count']}")
    print(f"   Type: {result['geojson']['type']}")

    print("\n   Wreck sites:")
    for feat in result["geojson"]["features"]:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        name = props.get("ship_name", "?")
        status = props.get("status", "?")
        unc = props.get("uncertainty_km", "?")
        print(f"     {name:25s}  [{coords[0]:8.2f}, {coords[1]:7.2f}]  status={status}  +/-{unc}km")

    # ----- Export 2: Found wrecks only ------------------------------
    print("\n2. Export only found wrecks")
    print("-" * 40)

    found = await runner.run("maritime_export_geojson", status="found")
    print(f"   Found wrecks: {found['feature_count']}")
    for feat in found["geojson"]["features"]:
        print(f"     {feat['properties']['ship_name']}")

    # ----- Export 3: By specific wreck IDs --------------------------
    print("\n3. Export specific wrecks by ID")
    print("-" * 40)

    # First find some wreck IDs
    wrecks = await runner.run("maritime_search_wrecks")
    wreck_ids = [w["wreck_id"] for w in wrecks["wrecks"][:2]]
    print(f"   Exporting: {wreck_ids}")

    specific = await runner.run("maritime_export_geojson", wreck_ids=wreck_ids)
    print(f"   Features: {specific['feature_count']}")

    # ----- Export 4: Minimal properties (no uncertainty/voyage) ------
    print("\n4. Minimal export (no uncertainty or voyage data)")
    print("-" * 40)

    minimal = await runner.run(
        "maritime_export_geojson",
        include_uncertainty=False,
        include_voyage_data=False,
    )
    # Show that properties only have core fields
    if minimal["geojson"]["features"]:
        props = minimal["geojson"]["features"][0]["properties"]
        print(f"   Property keys: {sorted(props.keys())}")

    # ----- Export 5: Full properties --------------------------------
    print("\n5. Full export (all properties)")
    print("-" * 40)

    full = await runner.run(
        "maritime_export_geojson",
        include_uncertainty=True,
        include_voyage_data=True,
    )
    if full["geojson"]["features"]:
        props = full["geojson"]["features"][0]["properties"]
        print(f"   Property keys: {sorted(props.keys())}")

    # ----- Pretty-print full GeoJSON --------------------------------
    print("\n6. Full GeoJSON output")
    print("-" * 40)
    print(json.dumps(result["geojson"], indent=2))

    # ----- Text output mode -----------------------------------------
    print("\n7. Text output mode")
    print("-" * 40)
    text = await runner.run_text("maritime_export_geojson")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
