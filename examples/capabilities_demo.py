#!/usr/bin/env python3
"""
Capabilities Demo -- chuk-mcp-maritime-archives

Quick-start script showing what the server can do. Lists archives,
tools, ship types, regions, and demonstrates dual output mode
(JSON vs text). No network access required -- all data is local.

Demonstrates:
    maritime_capabilities
    maritime_list_archives
    maritime_list_hull_profiles

Usage:
    python examples/capabilities_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Server Capabilities")
    print("=" * 60)

    # List all registered tools
    print(f"\nRegistered tools ({len(runner.tool_names)}):")
    for name in sorted(runner.tool_names):
        print(f"  - {name}")

    # Server capabilities (JSON mode)
    caps = await runner.run("maritime_capabilities")
    print(f"\nServer: {caps['server_name']} v{caps['version']}")

    # Archives
    print(f"\nMaritime Archives ({len(caps['archives'])}):")
    for arch in caps["archives"]:
        records = arch.get("total_records") or "N/A"
        print(f"  {arch['archive_id']:12s}  {arch['name']}")
        print(
            f"               Period: {arch.get('coverage_start', '?')}-{arch.get('coverage_end', '?')}  Records: {records}"
        )

    # Tools
    print(f"\nTools ({len(caps['tools'])}):")
    for tool in caps["tools"]:
        print(f"  {tool['name']:35s} [{tool['category']:10s}] {tool['description']}")

    # Ship types
    print(f"\nVOC Ship Types ({len(caps['ship_types'])}):")
    for st in caps["ship_types"]:
        print(f"  - {st}")

    # Regions
    print(f"\nGeographic Regions ({len(caps['regions'])}):")
    for code, desc in caps["regions"].items():
        print(f"  {code:25s} {desc}")

    # Single archive detail
    print("\n--- Archive details (maritime_get_archive) ---")
    for aid in ["das", "eic", "carreira", "galleon", "soic", "ukho"]:
        arch = await runner.run("maritime_get_archive", archive_id=aid)
        a = arch["archive"]
        print(f"  {aid:10s}  {a['name']}")
        print(f"             Org:    {a['organisation']}")
        print(f"             Period: {a['coverage_start']}-{a['coverage_end']}")
        print(f"             Records: {a.get('total_records', '?')}")
        print()

    # Hull profiles
    profiles = await runner.run("maritime_list_hull_profiles")
    print(f"\nHull Profiles ({profiles['count']}):")
    for st in profiles["ship_types"]:
        print(f"  - {st}")

    # ---------------------------------------------------------------
    # Dual output mode
    # ---------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Dual Output Mode Demo")
    print("-" * 60)

    # Archives in text mode
    print("\nmaritime_list_archives (output_mode='text'):")
    text = await runner.run_text("maritime_list_archives")
    print(text)

    # Capabilities in text mode
    print("\nmaritime_capabilities (output_mode='text'):")
    text = await runner.run_text("maritime_capabilities")
    print(text)

    print("\n" + "=" * 60)
    print("All capabilities shown above require no network access.")
    print("Run other demos to see search, cross-referencing, and")
    print("export features in action.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
