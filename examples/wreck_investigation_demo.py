#!/usr/bin/env python3
"""
Wreck Investigation Demo -- chuk-mcp-maritime-archives

Demonstrates a complete wreck investigation workflow across multiple
archives (MAARER, EIC, Carreira, Galleon, SOIC): search for wrecks,
examine individual wreck records, assess position quality, and export
locations as GeoJSON.

Demonstrates:
    maritime_search_wrecks (by region, status, cause, archive)
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

    # ----- Step 1: Search wrecks across all archives -------------------
    print("\n1. Search for wrecks across ALL archives")
    print("-" * 40)

    result = await runner.run("maritime_search_wrecks", max_results=15)

    if "error" in result:
        print(f"   API unavailable: {result['error']}")
        print("\n   Continuing with offline archives...")
    else:
        print(f"   Found {result['wreck_count']} wreck(s)")
        archives_seen = set()
        for w in result["wrecks"]:
            arch = w.get("archive", "?")
            archives_seen.add(arch)
            print(f"   {w['wreck_id']:22s} {w['ship_name']:25s} [{arch:10s}] {w.get('loss_date', '?')}")
        print(f"   Archives: {', '.join(sorted(archives_seen))}")

    # ----- Step 1b: Per-archive wreck searches (offline) ---------------
    print("\n1b. Per-archive wreck searches (offline)")
    print("-" * 40)

    for archive in ["eic", "carreira", "galleon", "soic"]:
        wrecks = await runner.run("maritime_search_wrecks", archive=archive, max_results=3)
        if "error" not in wrecks:
            print(f"\n   {archive.upper()} ({wrecks['wreck_count']} wrecks):")
            for w in wrecks["wrecks"]:
                cause = w.get("loss_cause", "?")
                status = w.get("status", "?")
                print(f"     {w['ship_name']:25s} {w.get('loss_date', '?'):12s} {cause:10s} [{status}]")

    wreck_id = None
    if "wrecks" in result and result["wrecks"]:
        wreck_id = result["wrecks"][0]["wreck_id"]

    # ----- Step 2: Get full wreck detail ----------------------------
    # Use an EIC wreck (offline) for the detail demo
    demo_wreck_id = "eic_wreck:0010"
    print(f"\n2. Get full details for {demo_wreck_id}")
    print("-" * 40)

    wreck = await runner.run("maritime_get_wreck", wreck_id=demo_wreck_id)
    if "error" not in wreck:
        detail = wreck["wreck"]
        print(f"   Wreck ID: {detail.get('wreck_id')}")
        print(f"   Ship: {detail.get('ship_name', '?')}")
        print(f"   Archive: {detail.get('archive', '?')}")
        print(f"   Lost: {detail.get('loss_date', '?')}")
        print(f"   Cause: {detail.get('loss_cause', '?')}")
        print(f"   Location: {detail.get('loss_location', '?')}")
        print(f"   Status: {detail.get('status', '?')}")
        if detail.get("position"):
            pos = detail["position"]
            print(f"   Position: {pos.get('lat')}N, {pos.get('lon')}E")
            print(f"   Uncertainty: +/-{pos.get('uncertainty_km', '?')}km")
        if detail.get("depth_estimate_m"):
            print(f"   Depth: ~{detail['depth_estimate_m']}m")
        if detail.get("particulars"):
            print(f"   Details: {detail['particulars'][:120]}...")
    else:
        print(f"   {wreck['error']}")

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
            geom = feat.get("geometry")
            if geom and geom.get("coordinates"):
                coords = geom["coordinates"]
                print(
                    f"     {props.get('ship_name', '?')}: [{coords[0]:.2f}, {coords[1]:.2f}] ({props.get('status', '?')})"
                )
            else:
                print(
                    f"     {props.get('ship_name', '?')}: [no coords] ({props.get('status', '?')})"
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
