#!/usr/bin/env python3
"""
Location Lookup Demo -- chuk-mcp-maritime-archives

Explore the VOC gazetteer of ~160 historical place names with
coordinates, regions, and historical context. Demonstrates how
an LLM can resolve place names from voyage records to modern
coordinates for mapping and analysis.

Demonstrates:
    maritime_lookup_location (exact, alias, and substring matching)
    maritime_list_locations (search, filter by region/type)

No network access required -- all data is local.

Usage:
    python examples/location_lookup_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Location Lookup Demo")
    print("=" * 60)

    # ---------------------------------------------------------------
    # 1. Look up well-known VOC locations
    # ---------------------------------------------------------------
    print("\n--- Lookup well-known VOC locations ---")

    locations = ["Batavia", "Cape of Good Hope", "Texel", "Deshima", "Malacca"]
    for name in locations:
        result = await runner.run("maritime_lookup_location", name=name)
        if "location" in result:
            loc = result["location"]
            print(
                f"  {name:25s} -> {loc['name']:25s}  "
                f"({loc['lat']:7.2f}, {loc['lon']:7.2f})  "
                f"region: {loc.get('region', '?')}"
            )
        else:
            print(f"  {name:25s} -> not found")

    # ---------------------------------------------------------------
    # 2. Alias resolution
    # ---------------------------------------------------------------
    print("\n--- Alias resolution ---")
    print("  Historical names often differ from modern ones:")

    aliases = ["Jakarta", "Kaapstad", "Sri Lanka", "Colombo", "Nagasaki"]
    for name in aliases:
        result = await runner.run("maritime_lookup_location", name=name)
        if "location" in result:
            loc = result["location"]
            print(f"  '{name}' -> canonical: '{loc['name']}'")
        else:
            print(f"  '{name}' -> not found")

    # ---------------------------------------------------------------
    # 3. Search by region
    # ---------------------------------------------------------------
    print("\n--- Search by region: indonesia ---")
    result = await runner.run("maritime_list_locations", region="indonesia", max_results=10)
    print(f"  Found {result['location_count']} locations in Indonesia (showing 10):")
    for loc in result["locations"][:10]:
        print(
            f"    {loc['name']:25s}  type: {loc.get('type', '?'):10s}  ({loc['lat']:.2f}, {loc['lon']:.2f})"
        )

    # ---------------------------------------------------------------
    # 4. Search by type
    # ---------------------------------------------------------------
    print("\n--- Search by type: cape ---")
    result = await runner.run("maritime_list_locations", location_type="cape")
    print(f"  Found {result['location_count']} capes/headlands:")
    for loc in result["locations"]:
        print(f"    {loc['name']:30s}  region: {loc.get('region', '?')}")

    # ---------------------------------------------------------------
    # 5. Text search across names and notes
    # ---------------------------------------------------------------
    print("\n--- Text search: 'spice' ---")
    result = await runner.run("maritime_list_locations", query="spice")
    print(f"  Found {result['location_count']} locations matching 'spice':")
    for loc in result["locations"]:
        print(f"    {loc['name']:25s}  notes: {loc.get('notes', '')[:60]}")

    # ---------------------------------------------------------------
    # 6. Text mode output
    # ---------------------------------------------------------------
    print("\n--- Text mode: lookup Batavia ---")
    text = await runner.run_text("maritime_lookup_location", name="Batavia")
    print(text)

    # ---------------------------------------------------------------
    # 7. Full JSON for a single location
    # ---------------------------------------------------------------
    print("\n--- Full JSON: Cape of Good Hope ---")
    result = await runner.run("maritime_lookup_location", name="Cape of Good Hope")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("Demo complete! The gazetteer enables LLMs to resolve")
    print("place names from Particulars text to coordinates.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
