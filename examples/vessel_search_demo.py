#!/usr/bin/env python3
"""
Vessel Search Demo -- chuk-mcp-maritime-archives

Search for VOC vessels by name, type, and construction details.
Also demonstrates the hull profile tools for hydrodynamic data
useful in drift modelling and wreck search planning.

Demonstrates:
    maritime_search_vessels (by name, by type)
    maritime_get_vessel (full vessel record)
    maritime_get_hull_profile (ship type characteristics)

Usage:
    python examples/vessel_search_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Vessel Search Demo")
    print("=" * 60)

    # ----- Search all vessels ---------------------------------------
    print("\n1. All vessels in the registry")
    print("-" * 40)

    result = await runner.run("maritime_search_vessels")
    print(f"   Found {result['vessel_count']} vessel(s)")

    for v in result["vessels"]:
        vtype = v.get("type", "?")
        tonnage = f"{v['tonnage']} lasten" if v.get("tonnage") else "? lasten"
        year = v.get("built_year", "?")
        chamber = v.get("chamber", "?")
        print(f"\n   {v['vessel_id']}: {v['name']}")
        print(f"     Type: {vtype}  Tonnage: {tonnage}")
        print(f"     Built: {year}  Chamber: {chamber}")

    # ----- Search by name -------------------------------------------
    print("\n2. Search for the Batavia")
    print("-" * 40)

    batavia = await runner.run("maritime_search_vessels", name="Batavia")
    if batavia["vessel_count"] > 0:
        v = batavia["vessels"][0]
        print(f"   Found: {v['name']} ({v.get('type', '?')})")

        # Get full vessel details
        vessel = await runner.run("maritime_get_vessel", vessel_id=v["vessel_id"])
        if "vessel" in vessel:
            vd = vessel["vessel"]
            print(f"\n   Full vessel record:")
            print(f"     Name: {vd.get('name', '?')}")
            print(f"     Type: {vd.get('type', '?')}")
            print(f"     Tonnage: {vd.get('tonnage', '?')} lasten")
            print(f"     Built: {vd.get('built_year', '?')}")
            print(f"     Shipyard: {vd.get('shipyard', '?')}")
            print(f"     Chamber: {vd.get('chamber', '?')}")

            if vd.get("dimensions"):
                dims = vd["dimensions"]
                print(f"     Dimensions: {dims.get('length_m', '?')}m x {dims.get('beam_m', '?')}m")
                print(f"     Draught: {dims.get('draught_m', '?')}m")

    # ----- Compare ship types ---------------------------------------
    print("\n3. VOC ship type comparison")
    print("-" * 40)

    profiles = await runner.run("maritime_list_hull_profiles")
    print(f"\n   {'Type':15s}  {'Tonnage':15s}  {'Length':10s}  {'Beam':10s}")
    print(f"   {'-'*15}  {'-'*15}  {'-'*10}  {'-'*10}")

    for st in profiles["ship_types"]:
        profile = await runner.run("maritime_get_hull_profile", ship_type=st)
        p = profile["profile"]

        tonnage_range = p.get("tonnage_range_lasten", {})
        t_str = f"{tonnage_range.get('min', '?')}-{tonnage_range.get('max', '?')}"

        dims = p.get("dimensions_typical", {})
        length = dims.get("length_m", {}).get("typical", "?")
        beam = dims.get("beam_m", {}).get("typical", "?")

        print(f"   {st:15s}  {t_str:15s}  {str(length):>6}m   {str(beam):>6}m")

    # ----- Text output mode -----------------------------------------
    print("\n4. Text output mode")
    print("-" * 40)
    text = await runner.run_text("maritime_search_vessels")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
