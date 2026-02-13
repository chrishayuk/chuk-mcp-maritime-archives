#!/usr/bin/env python3
"""
NOAA US Wrecks Demo -- chuk-mcp-maritime-archives

Demonstrates the NOAA AWOIS wreck archive: ~13,000 wrecks in US
coastal waters (50 curated when using generate_noaa.py fallback).
Shows NOAA-specific GP quality filtering, US regional search
(Gulf of Mexico, Great Lakes), depth analysis, and cross-archive
comparison with UKHO global wrecks.

Demonstrates:
    maritime_search_wrecks (NOAA filters: gp_quality, region, flag)
    maritime_get_wreck (NOAA wreck detail)
    maritime_get_statistics (includes NOAA data)
    maritime_export_geojson (NOAA wreck positions)

Usage:
    python examples/noaa_us_wrecks_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 70)
    print("  NOAA US WRECKS (AWOIS) DEMO")
    print("  Automated Wreck and Obstruction Information System")
    print("=" * 70)

    # ----- 1. Archive overview -----------------------------------------------
    print("\n1. NOAA Archive Overview")
    print("-" * 40)

    archive = await runner.run("maritime_get_archive", archive_id="noaa")
    if "error" not in archive:
        a = archive["archive"]
        print(f"   Name: {a.get('name', '?')}")
        print(f"   Organisation: {a.get('organisation', '?')}")
        print(f"   Coverage: {a.get('coverage_start', '?')}-{a.get('coverage_end', '?')}")
        print(f"   Total wrecks: {a.get('total_wrecks', '?')}")
        print(f"   License: {a.get('license', '?')}")
    else:
        print(f"   {archive['error']}")
        return

    # ----- 2. Search all NOAA wrecks ----------------------------------------
    print("\n2. All NOAA wrecks (first 10)")
    print("-" * 40)

    result = await runner.run("maritime_search_wrecks", archive="noaa", max_results=10)
    if "error" not in result:
        print(f"   Total: {result['wreck_count']} wrecks")
        for w in result["wrecks"][:10]:
            depth = w.get("depth_estimate_m") or "?"
            print(f"     {w['ship_name']:30s}  {w.get('loss_date', '?'):12s}  depth={depth}m")
    else:
        print(f"   {result['error']}")

    # ----- 3. GP Quality search (high-accuracy positions) --------------------
    print("\n3. High-accuracy positions (GP Quality 1)")
    print("-" * 40)

    gp1 = await runner.run("maritime_search_wrecks", archive="noaa", gp_quality=1, max_results=10)
    if "error" not in gp1:
        print(f"   Found: {gp1['wreck_count']} high-accuracy wrecks")
        for w in gp1["wrecks"][:10]:
            print(f"     {w['ship_name']:30s}  depth={w.get('depth_estimate_m', '?')}m")
    else:
        print(f"   {gp1['error']}")

    # ----- 4. Gulf of Mexico wrecks -----------------------------------------
    print("\n4. Gulf of Mexico wrecks")
    print("-" * 40)

    gulf = await runner.run("maritime_search_wrecks", archive="noaa", region="gulf_of_mexico")
    if "error" not in gulf:
        print(f"   Found: {gulf['wreck_count']} Gulf wrecks")
        for w in gulf["wrecks"]:
            print(f"     {w['ship_name']:30s}  {w.get('loss_date', '?'):12s}")
    else:
        print(f"   {gulf['error']}")

    # ----- 5. Great Lakes wrecks --------------------------------------------
    print("\n5. Great Lakes wrecks")
    print("-" * 40)

    lakes = await runner.run("maritime_search_wrecks", archive="noaa", region="great_lakes")
    if "error" not in lakes:
        print(f"   Found: {lakes['wreck_count']} Great Lakes wrecks")
        for w in lakes["wrecks"]:
            print(f"     {w['ship_name']:30s}  {w.get('loss_date', '?'):12s}")
    else:
        print(f"   {lakes['error']}")

    # ----- 6. Famous US wreck lookups ----------------------------------------
    print("\n6. Famous US wrecks")
    print("-" * 40)

    famous = ["Monitor", "Arizona", "Fitzgerald", "Andrea Doria", "Atocha"]
    for name in famous:
        result = await runner.run("maritime_search_wrecks", archive="noaa", ship_name=name)
        if "error" not in result and result["wrecks"]:
            w = result["wrecks"][0]
            print(f"   {w['ship_name']:30s}  {w.get('loss_date', '?'):12s}  {w.get('region', '?')}")
        else:
            print(f"   {name:30s}  not found")

    # ----- 7. Wreck detail ---------------------------------------------------
    print("\n7. Wreck detail: USS Monitor")
    print("-" * 40)

    detail = await runner.run("maritime_get_wreck", wreck_id="noaa_wreck:00001")
    if "error" not in detail:
        w = detail["wreck"]
        print(f"   Ship: {w['ship_name']}")
        print(f"   Lost: {w.get('loss_date', '?')}")
        print(f"   Cause: {w.get('loss_cause', '?')}")
        print(f"   Region: {w.get('region', '?')}")
        print(f"   Depth: {w.get('depth_estimate_m', '?')}m")
        print(f"   Flag: {w.get('flag', '?')}")
        print(f"   Type: {w.get('vessel_type', '?')}")
        print(f"   GP Quality: {w.get('gp_quality', '?')}")
        pos = w.get("position", {})
        if pos:
            print(f"   Position: {pos.get('lat', '?')}N, {pos.get('lon', '?')}E")
            print(f"   Uncertainty: {pos.get('uncertainty_km', '?')}km")
    else:
        print(f"   {detail['error']}")

    # ----- 8. Cross-archive comparison (NOAA vs UKHO) ----------------------
    print("\n8. Cross-archive comparison: NOAA vs UKHO")
    print("-" * 40)

    for archive_id in ["noaa", "ukho"]:
        result = await runner.run("maritime_search_wrecks", archive=archive_id, max_results=500)
        if "error" not in result:
            count = result["wreck_count"]
            depths = [
                w.get("depth_estimate_m")
                for w in result["wrecks"]
                if w.get("depth_estimate_m") is not None
            ]
            avg_depth = sum(depths) / len(depths) if depths else 0
            print(f"   {archive_id.upper():6s}: {count:4d} wrecks, avg depth {avg_depth:.0f}m")

    # ----- 9. GeoJSON export ------------------------------------------------
    print("\n9. GeoJSON export (NOAA wrecks)")
    print("-" * 40)

    geo = await runner.run("maritime_export_geojson", archive="noaa")
    if "error" not in geo:
        print(f"   Features: {geo['feature_count']}")
        print(f"   Type: {geo['geojson']['type']}")
        if geo["geojson"]["features"]:
            feat = geo["geojson"]["features"][0]
            print(f"   Sample: {feat['properties'].get('ship_name', '?')}")
    else:
        print(f"   {geo['error']}")

    # ----- 10. Text output mode ---------------------------------------------
    print("\n10. Text output mode")
    print("-" * 40)

    text = await runner.run_text("maritime_search_wrecks", archive="noaa", max_results=5)
    print(text)

    print("\n" + "=" * 70)
    print("  Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
