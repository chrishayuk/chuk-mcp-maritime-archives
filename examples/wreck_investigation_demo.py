#!/usr/bin/env python3
"""
Wreck Investigation Demo -- chuk-mcp-maritime-archives

Demonstrates a complete wreck investigation workflow: search for
wrecks, examine individual wreck records, assess position quality,
and export locations as GeoJSON. All IDs are discovered from search
results -- no hardcoded identifiers.

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

    # ----- Step 1: Search for wrecks ---------------------------------
    print("\n1. Search for wrecks")
    print("-" * 40)

    result = await runner.run("maritime_search_wrecks", max_results=10)

    if "error" in result:
        print(f"   API unavailable: {result['error']}")
        print("   (This demo requires network access to the MAARER archive)")
        print("\n   Continuing with position assessment (no network needed)...")
    else:
        print(f"   Found {result['wreck_count']} wreck(s)")

    wreck_id = None
    if "wrecks" in result:
        for w in result["wrecks"]:
            print(f"\n   {w['wreck_id']}: {w['ship_name']}")
            print(f"     Lost: {w.get('loss_date', '?')}  Cause: {w.get('loss_cause', '?')}")
            print(f"     Region: {w.get('region', '?')}  Status: {w.get('status', '?')}")
            if w.get("position"):
                pos = w["position"]
                print(f"     Position: {pos.get('lat', '?')}N, {pos.get('lon', '?')}E")
            if wreck_id is None:
                wreck_id = w["wreck_id"]

    # ----- Step 2: Get full wreck detail ----------------------------
    if wreck_id:
        print(f"\n2. Get full details for {wreck_id}")
        print("-" * 40)

        wreck = await runner.run("maritime_get_wreck", wreck_id=wreck_id)
        if "error" not in wreck:
            detail = wreck["wreck"]
            print(f"   Wreck ID: {detail.get('wreck_id', wreck_id)}")
            print(f"   Ship: {detail.get('ship_name', '?')} ({detail.get('ship_type', '?')})")
            print(f"   Lost: {detail.get('loss_date', '?')}")
            print(f"   Cause: {detail.get('loss_cause', '?')}")
            print(f"   Status: {detail.get('status', '?')}")
            if detail.get("position"):
                pos = detail["position"]
                print(f"   Position: {pos.get('lat')}N, {pos.get('lon')}E")
                print(f"   Uncertainty: +/-{pos.get('uncertainty_km', '?')}km")
            if detail.get("cargo_value_guilders"):
                print(f"   Cargo value: {detail['cargo_value_guilders']:,.0f} guilders")
        else:
            print(f"   {wreck['error']}")
    else:
        print("\n2. (Skipped -- no wreck results)")

    # ----- Step 3: Assess position quality --------------------------
    if wreck_id:
        print(f"\n3. Assess position quality for {wreck_id}")
        print("-" * 40)

        assessment = await runner.run(
            "maritime_assess_position",
            wreck_id=wreck_id,
            source_description="GPS surveyed wreck site",
        )
        a = assessment.get("assessment", {})
        quality = a.get("assessment", {})
        print(f"   Quality score: {quality.get('quality_score', '?')}")
        print(f"   Quality label: {quality.get('quality_label', '?')}")
        print(f"   Uncertainty type: {quality.get('uncertainty_type', '?')}")
        print(f"   Uncertainty radius: +/-{quality.get('uncertainty_radius_km', '?')}km")

    # ----- Step 4: Assess a dead reckoning position -----------------
    print("\n4. Dead reckoning position assessment (no network needed)")
    print("-" * 40)

    assessment2 = await runner.run(
        "maritime_assess_position",
        latitude=-35.0,
        longitude=25.0,
        source_description="Dead reckoning position estimate from ship log",
        date="1650-06-15",
    )
    a2 = assessment2.get("assessment", {})
    q2 = a2.get("assessment", {})
    print(f"   Quality score: {q2.get('quality_score', '?')}")
    print(f"   Quality label: {q2.get('quality_label', '?')}")
    print(f"   Uncertainty type: {q2.get('uncertainty_type', '?')}")
    print(f"   Uncertainty radius: +/-{q2.get('uncertainty_radius_km', '?')}km")

    # ----- Step 5: Export as GeoJSON --------------------------------
    print("\n5. Export wreck positions as GeoJSON")
    print("-" * 40)

    geojson = await runner.run("maritime_export_geojson")
    if "error" not in geojson:
        print(f"   Feature count: {geojson['feature_count']}")
        print(f"   GeoJSON type: {geojson['geojson']['type']}")

        for feat in geojson["geojson"]["features"][:5]:
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            print(
                f"     {props.get('ship_name', '?')}: [{coords[0]:.2f}, {coords[1]:.2f}] ({props.get('status', '?')})"
            )

        if geojson["geojson"]["features"]:
            print("\n   First feature (full):")
            print(json.dumps(geojson["geojson"]["features"][0], indent=4))
    else:
        print(f"   {geojson['error']}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
