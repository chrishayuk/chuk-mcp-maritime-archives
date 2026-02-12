#!/usr/bin/env python3
"""
UKHO Global Wrecks Demo -- chuk-mcp-maritime-archives

Demonstrates the UK Hydrographic Office global wrecks archive: 94,000+
wreck records worldwide (50 curated when using generate_ukho.py fallback).
Shows UKHO-specific search filters (flag, vessel_type), regional analysis,
depth filtering, famous wreck lookups, and cross-archive comparison.

Demonstrates:
    maritime_search_wrecks (UKHO filters: flag, vessel_type, depth)
    maritime_get_wreck (UKHO wreck detail)
    maritime_get_statistics (includes UKHO data)
    maritime_export_geojson (UKHO wreck positions)

Usage:
    python examples/ukho_global_wrecks_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 70)
    print("  UKHO GLOBAL WRECKS DEMO")
    print("  UK Hydrographic Office -- 94,000+ wrecks worldwide")
    print("=" * 70)

    # ----- 1: Overview -- search all UKHO wrecks -------------------------
    print("\n1. UKHO archive overview")
    print("-" * 50)

    archive = await runner.run("maritime_get_archive", archive_id="ukho")
    if "error" not in archive:
        a = archive["archive"]
        print(f"   Name:    {a['name']}")
        print(f"   Org:     {a['organisation']}")
        print(f"   Period:  {a['coverage_start']}-{a['coverage_end']}")
        print(f"   License: {a.get('license', '?')}")

    all_wrecks = await runner.run("maritime_search_wrecks", archive="ukho", max_results=500)
    if "error" in all_wrecks:
        print(f"   Error: {all_wrecks['error']}")
        return

    total = all_wrecks["wreck_count"]
    print(f"\n   Total UKHO wrecks loaded: {total}")

    # Collect stats
    flags = {}
    regions = {}
    types = {}
    causes = {}
    depths = []
    for w in all_wrecks["wrecks"]:
        f = w.get("flag") or "Unknown"
        flags[f] = flags.get(f, 0) + 1
        r = w.get("region") or "unclassified"
        regions[r] = regions.get(r, 0) + 1
        t = w.get("vessel_type") or "Unknown"
        types[t] = types.get(t, 0) + 1
        c = w.get("loss_cause", "unknown")
        causes[c] = causes.get(c, 0) + 1
        if w.get("depth_estimate_m") is not None:
            depths.append(w["depth_estimate_m"])

    print(f"   Unique flags: {len(flags)}")
    print(f"   Unique regions: {len(regions)}")
    print(f"   Unique vessel types: {len(types)}")

    # ----- 2: Search by nationality (flag) --------------------------------
    print("\n2. Search by nationality (flag filter)")
    print("-" * 50)

    for flag in ["UK", "NL", "ES", "PT", "US", "DE", "JP"]:
        result = await runner.run(
            "maritime_search_wrecks", archive="ukho", flag=flag, max_results=3
        )
        if "error" not in result and result["wreck_count"] > 0:
            count = result["wreck_count"]
            ships = ", ".join(w["ship_name"] for w in result["wrecks"][:3])
            suffix = "..." if count > 3 else ""
            print(f"   {flag:3s}  {count:3d} wreck(s): {ships}{suffix}")

    # ----- 3: Search by vessel type ---------------------------------------
    print("\n3. Search by vessel type")
    print("-" * 50)

    for vtype in ["liner", "warship", "galleon", "battleship", "cargo", "retourschip"]:
        result = await runner.run(
            "maritime_search_wrecks", archive="ukho", vessel_type=vtype, max_results=5
        )
        if "error" not in result and result["wreck_count"] > 0:
            ships = [f"{w['ship_name']} ({w.get('loss_date', '?')[:4]})" for w in result["wrecks"]]
            print(f"\n   {vtype.upper()} ({result['wreck_count']}):")
            for s in ships:
                print(f"     - {s}")

    # ----- 4: Famous wreck lookups ----------------------------------------
    print("\n4. Famous wreck lookups")
    print("-" * 50)

    famous = [
        ("RMS Titanic", "The 'unsinkable' liner, 1912"),
        ("RMS Lusitania", "Torpedoed by U-20, 1915"),
        ("Vasa", "Swedish warship capsized on maiden voyage, 1628"),
        ("Mary Rose", "Henry VIII's flagship, sank in the Solent, 1545"),
        ("USS Arizona", "Pearl Harbor, 1941"),
        ("SS Thistlegorm", "Red Sea dive wreck, WWII cargo"),
        ("Endurance", "Shackleton's Antarctic expedition vessel, 1915"),
    ]

    for ship_name, note in famous:
        result = await runner.run(
            "maritime_search_wrecks", archive="ukho", ship_name=ship_name, max_results=1
        )
        if "error" not in result and result["wreck_count"] > 0:
            w = result["wrecks"][0]
            pos = w.get("position", {})
            lat = pos.get("lat", "?")
            lon = pos.get("lon", "?")
            depth = w.get("depth_estimate_m")
            depth_str = f"{depth}m" if depth is not None else "?"
            print(f"\n   {w['ship_name']}")
            print(f"     {note}")
            print(
                f"     Lost: {w.get('loss_date', '?')}  "
                f"Cause: {w.get('loss_cause', '?')}  "
                f"Depth: {depth_str}"
            )
            print(f"     Position: {lat}N, {lon}E  [{w.get('region', '?')}]")
            print(f"     Flag: {w.get('flag', '?')}  Type: {w.get('vessel_type', '?')}")

    # ----- 5: Depth-based exploration -------------------------------------
    print("\n\n5. Depth-based wreck exploration")
    print("-" * 50)

    # Shallow wrecks (diveable)
    shallow = await runner.run(
        "maritime_search_wrecks", archive="ukho", max_depth_m=30, max_results=100
    )
    if "error" not in shallow:
        print(f"\n   Shallow wrecks (< 30m, diveable): {shallow['wreck_count']}")
        for w in shallow["wrecks"][:5]:
            print(
                f"     {w['ship_name']:25s}  {w.get('depth_estimate_m', '?'):>5}m  [{w.get('region', '?')}]"
            )

    # Deep wrecks
    deep = await runner.run(
        "maritime_search_wrecks", archive="ukho", min_depth_m=1000, max_results=100
    )
    if "error" not in deep:
        print(f"\n   Deep wrecks (> 1000m): {deep['wreck_count']}")
        for w in deep["wrecks"][:5]:
            print(
                f"     {w['ship_name']:25s}  {w.get('depth_estimate_m', '?'):>5}m  [{w.get('region', '?')}]"
            )

    # ----- 6: Regional distribution ---------------------------------------
    print("\n6. Regional distribution of UKHO wrecks")
    print("-" * 50)

    max_count = max(regions.values()) if regions else 1
    for region, count in sorted(regions.items(), key=lambda x: -x[1]):
        bar_len = int(count / max_count * 30)
        bar = "#" * bar_len
        print(f"   {region:25s}  {count:3d}  {bar}")

    # ----- 7: Flag distribution -------------------------------------------
    print("\n7. Wreck distribution by flag/nationality")
    print("-" * 50)

    max_flag = max(flags.values()) if flags else 1
    for flag, count in sorted(flags.items(), key=lambda x: -x[1]):
        bar_len = int(count / max_flag * 30)
        bar = "#" * bar_len
        print(f"   {flag:10s}  {count:3d}  {bar}")

    # ----- 8: Cross-archive comparison ------------------------------------
    print("\n8. Cross-archive comparison: UKHO vs traditional archives")
    print("-" * 50)

    for arch in ["maarer", "eic", "carreira", "galleon", "soic", "ukho"]:
        result = await runner.run("maritime_search_wrecks", archive=arch, max_results=500)
        if "error" not in result:
            count = result["wreck_count"]
            arch_causes = {}
            for w in result["wrecks"]:
                c = w.get("loss_cause", "unknown")
                arch_causes[c] = arch_causes.get(c, 0) + 1
            top_cause = max(arch_causes.items(), key=lambda x: x[1])[0] if arch_causes else "?"
            print(f"   {arch:10s}  {count:5d} wrecks  (top cause: {top_cause})")

    # ----- 9: UKHO wreck detail -------------------------------------------
    print("\n9. UKHO wreck detail (Titanic)")
    print("-" * 50)

    titanic = await runner.run(
        "maritime_search_wrecks", archive="ukho", ship_name="Titanic", max_results=1
    )
    if "error" not in titanic and titanic["wreck_count"] > 0:
        wreck_id = titanic["wrecks"][0]["wreck_id"]
        detail = await runner.run("maritime_get_wreck", wreck_id=wreck_id)
        if "error" not in detail:
            w = detail["wreck"]
            print(f"   ID:        {w.get('wreck_id')}")
            print(f"   Ship:      {w.get('ship_name')}")
            print(f"   Flag:      {w.get('flag')}")
            print(f"   Type:      {w.get('vessel_type')}")
            print(f"   Lost:      {w.get('loss_date')}")
            print(f"   Cause:     {w.get('loss_cause')}")
            print(f"   Location:  {w.get('loss_location')}")
            print(f"   Region:    {w.get('region')}")
            print(f"   Status:    {w.get('status')}")
            if w.get("position"):
                pos = w["position"]
                print(
                    f"   Position:  {pos.get('lat')}N, {pos.get('lon')}E "
                    f"(+/-{pos.get('uncertainty_km', '?')}km)"
                )
            if w.get("depth_estimate_m") is not None:
                print(f"   Depth:     {w['depth_estimate_m']}m")

    # ----- 10: GeoJSON export of UKHO wrecks ------------------------------
    print("\n10. GeoJSON export of UKHO wrecks")
    print("-" * 50)

    geojson = await runner.run("maritime_export_geojson", archive="ukho")
    if "error" not in geojson:
        print(f"   Exported {geojson['feature_count']} UKHO wreck positions")
        print(f"   GeoJSON type: {geojson['geojson']['type']}")

        # Show first feature
        if geojson["geojson"]["features"]:
            feat = geojson["geojson"]["features"][0]
            print("\n   First feature:")
            print(json.dumps(feat, indent=4))

    # ----- Summary --------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print()
    print(f"  UKHO wrecks loaded: {total}")
    print(f"  Flags represented: {len(flags)} ({', '.join(sorted(flags.keys()))})")
    print(f"  Regions covered: {len(regions)}")
    print(f"  Vessel types: {len(types)}")
    print()
    print("  UKHO-specific search filters:")
    print("    flag         -- filter by vessel nationality (e.g. UK, NL, US)")
    print("    vessel_type  -- filter by ship classification (e.g. liner, warship)")
    print("    min_depth_m  -- minimum wreck depth in metres")
    print("    max_depth_m  -- maximum wreck depth in metres")
    print()
    print("  The UKHO archive complements the existing European trading")
    print("  company archives (MAARER, EIC, Carreira, Galleon, SOIC) with")
    print("  global coverage spanning 5 centuries and 15+ nationalities.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
