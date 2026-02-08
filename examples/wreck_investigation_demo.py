#!/usr/bin/env python3
"""
Wreck Investigation Demo -- chuk-mcp-maritime-archives

Demonstrates a complete wreck investigation workflow: search for
wrecks, examine individual wreck records, assess position quality,
and export locations as GeoJSON.

Demonstrates:
    maritime_search_wrecks (by region, status, cause)
    maritime_get_wreck (full wreck detail)
    maritime_assess_position (position quality assessment)
    maritime_export_geojson (GeoJSON export)

Usage:
    python examples/wreck_investigation_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Wreck Investigation Demo")
    print("=" * 60)

    # ----- Step 1: Search for found wrecks ---------------------------
    print("\n1. Search for wrecks with 'found' status")
    print("-" * 40)

    result = await runner.run("maritime_search_wrecks", status="found")
    print(f"   Found {result['wreck_count']} wreck(s) with status=found")

    for w in result["wrecks"]:
        print(f"\n   {w['wreck_id']}: {w['ship_name']}")
        print(f"     Lost: {w.get('loss_date', '?')}  Cause: {w.get('loss_cause', '?')}")
        print(f"     Region: {w.get('region', '?')}  Status: {w.get('status', '?')}")
        if w.get("position"):
            pos = w["position"]
            print(f"     Position: {pos.get('lat', '?')}N, {pos.get('lon', '?')}E")

    # ----- Step 2: Get full wreck detail ----------------------------
    print("\n2. Get full details for the Batavia wreck")
    print("-" * 40)

    wreck = await runner.run("maritime_get_wreck", wreck_id="maarer:VOC-0789")
    detail = wreck["wreck"]
    print(f"   Wreck ID: {detail['wreck_id']}")
    print(f"   Ship: {detail['ship_name']} ({detail.get('ship_type', '?')})")
    print(f"   Tonnage: {detail.get('tonnage', '?')} lasten")
    print(f"   Lost: {detail.get('loss_date', '?')}")
    print(f"   Cause: {detail.get('loss_cause', '?')}")
    print(f"   Region: {detail.get('region', '?')}")
    print(f"   Status: {detail.get('status', '?')}")
    if detail.get("position"):
        pos = detail["position"]
        print(f"   Position: {pos.get('lat')}N, {pos.get('lon')}E")
        print(f"   Uncertainty: +/-{pos.get('uncertainty_km', '?')}km")
    if detail.get("depth_estimate_m"):
        print(f"   Depth: ~{detail['depth_estimate_m']}m")
    if detail.get("cargo_value_guilders"):
        print(f"   Cargo value: {detail['cargo_value_guilders']:,.0f} guilders")
    if detail.get("lives_lost"):
        print(f"   Lives lost: {detail['lives_lost']}")

    # ----- Step 3: Assess position quality --------------------------
    print("\n3. Assess position quality for the Batavia wreck")
    print("-" * 40)

    assessment = await runner.run(
        "maritime_assess_position",
        wreck_id="maarer:VOC-0789",
        source_description="GPS surveyed wreck site",
    )
    a = assessment["assessment"]
    quality = a.get("assessment", {})
    print(f"   Quality score: {quality.get('quality_score', '?')}")
    print(f"   Quality label: {quality.get('quality_label', '?')}")
    print(f"   Uncertainty type: {quality.get('uncertainty_type', '?')}")
    print(f"   Uncertainty radius: +/-{quality.get('uncertainty_radius_km', '?')}km")

    factors = a.get("factors", {})
    nav_era = factors.get("navigation_era", {})
    if nav_era.get("technology"):
        print(f"   Navigation tech: {nav_era['technology']}")
        print(f"   Typical accuracy: +/-{nav_era.get('typical_accuracy_km', '?')}km")

    recs = a.get("recommendations", {})
    if recs.get("for_search"):
        print(f"   Search advice: {recs['for_search'][:80]}...")

    # ----- Step 4: Assess a dead reckoning position -----------------
    print("\n4. Compare: dead reckoning position assessment")
    print("-" * 40)

    assessment2 = await runner.run(
        "maritime_assess_position",
        latitude=-35.0,
        longitude=25.0,
        source_description="Dead reckoning position estimate from ship log",
        date="1650-06-15",
    )
    a2 = assessment2["assessment"]
    q2 = a2.get("assessment", {})
    print(f"   Quality score: {q2.get('quality_score', '?')}")
    print(f"   Quality label: {q2.get('quality_label', '?')}")
    print(f"   Uncertainty type: {q2.get('uncertainty_type', '?')}")
    print(f"   Uncertainty radius: +/-{q2.get('uncertainty_radius_km', '?')}km")

    # ----- Step 5: Export as GeoJSON --------------------------------
    print("\n5. Export all wreck positions as GeoJSON")
    print("-" * 40)

    geojson = await runner.run("maritime_export_geojson")
    print(f"   Feature count: {geojson['feature_count']}")
    print(f"   GeoJSON type: {geojson['geojson']['type']}")

    print("\n   Sample features:")
    for feat in geojson["geojson"]["features"][:3]:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        print(f"     {props.get('ship_name', '?')}: [{coords[0]:.2f}, {coords[1]:.2f}] ({props.get('status', '?')})")

    # Pretty-print one feature
    if geojson["geojson"]["features"]:
        print("\n   First feature (full):")
        print(json.dumps(geojson["geojson"]["features"][0], indent=4))

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
