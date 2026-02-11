#!/usr/bin/env python3
"""
Voyage Search Demo -- chuk-mcp-maritime-archives

Search for voyages across multiple archives using different filters
and retrieve full voyage details. Demonstrates the search-then-detail
workflow across DAS (Dutch), EIC (English), Carreira (Portuguese),
Galleon (Spanish), and SOIC (Swedish) archives.

Demonstrates:
    maritime_search_voyages (multiple filter combinations, multi-archive)
    maritime_get_voyage (detail retrieval from search results)

Usage:
    python examples/voyage_search_demo.py
"""

import asyncio

from tool_runner import ToolRunner


def _print_voyage(v: dict, indent: str = "   ") -> None:
    """Print a voyage record."""
    archive = f" [{v['archive']}]" if v.get("archive") else ""
    print(f"{indent}{v['voyage_id']}: {v['ship_name']}{archive}")
    print(f"{indent}  Captain: {v.get('captain', 'Unknown')}")
    print(f"{indent}  Route: {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}")
    print(f"{indent}  Departure: {v.get('departure_date', '?')}")
    print(f"{indent}  Fate: {v.get('fate', '?')}")


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Voyage Search Demo")
    print("=" * 60)

    # ----- Search 1: Find a specific ship (DAS) ----------------------
    print("\n1. Search for the Batavia (DAS archive)")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", ship_name="Batavia")

    if "error" in result:
        print(f"   API unavailable: {result['error']}")
        print("   (DAS search requires network access -- continuing with offline archives)")
    else:
        print(f"   Found {result['voyage_count']} voyage(s)")
        for v in result["voyages"]:
            _print_voyage(v)

    # ----- Search 2: Multi-archive search (all offline) ---------------
    print("\n2. Search across ALL archives for wrecked voyages")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", fate="wrecked", max_results=10)
    if "error" not in result:
        print(f"   Found {result['voyage_count']} wrecked voyage(s)")
        archives_seen = set()
        for v in result["voyages"]:
            arch = v.get("archive", "?")
            archives_seen.add(arch)
            print(f"   {v['voyage_id']:16s} {v['ship_name']:30s} [{arch}]  {v.get('departure_date', '?')}")
        print(f"   Archives represented: {', '.join(sorted(archives_seen))}")

    # ----- Search 3: EIC-specific search (offline) --------------------
    print("\n3. Search EIC archive for famous ships")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", archive="eic", ship_name="Grosvenor")
    if "error" not in result:
        print(f"   Found {result['voyage_count']} EIC voyage(s)")
        for v in result["voyages"]:
            _print_voyage(v)

    # ----- Search 4: Carreira da India (offline) ----------------------
    print("\n4. Search Carreira da India for Vasco da Gama")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", archive="carreira", captain="Gama")
    if "error" not in result:
        print(f"   Found {result['voyage_count']} Carreira voyage(s)")
        for v in result["voyages"]:
            _print_voyage(v)

    # ----- Search 5: Manila Galleon (offline) -------------------------
    print("\n5. Search Manila Galleon trade")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", archive="galleon", max_results=5)
    if "error" not in result:
        print(f"   Found {result['voyage_count']} Galleon voyage(s)")
        for v in result["voyages"]:
            _print_voyage(v)

    # ----- Search 6: SOIC - Swedish East India Company (offline) ------
    print("\n6. Search SOIC for the Gotheborg")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", archive="soic", ship_name="Gotheborg")
    if "error" not in result:
        print(f"   Found {result['voyage_count']} SOIC voyage(s)")
        for v in result["voyages"]:
            _print_voyage(v)

    # ----- Search 7: Get full voyage details --------------------------
    print("\n7. Get full voyage details for eic:0001")
    print("-" * 40)

    voyage = await runner.run("maritime_get_voyage", voyage_id="eic:0001")
    if "error" not in voyage:
        detail = voyage["voyage"]
        print(f"   Voyage ID: {detail.get('voyage_id')}")
        print(f"   Ship: {detail.get('ship_name')} ({detail.get('tonnage', '?')} tons)")
        print(f"   Captain: {detail.get('captain')}")
        print(f"   Route: {detail.get('departure_port')} -> {detail.get('destination_port')}")
        print(f"   Departure: {detail.get('departure_date')}")
        print(f"   Fate: {detail.get('fate')}")
        if detail.get("particulars"):
            print(f"   Details: {detail['particulars'][:120]}...")
    else:
        print(f"   {voyage['error']}")

    # ----- Search 8: Date range across archives -----------------------
    print("\n8. Search voyages from 1497-1510 (Age of Discovery)")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", date_range="1497/1510", max_results=10)
    if "error" not in result:
        print(f"   Found {result['voyage_count']} voyage(s) in 1497-1510")
        for v in result["voyages"]:
            arch = v.get("archive", "?")
            print(f"   {v['voyage_id']:16s} {v['ship_name']:30s} [{arch}]  {v.get('departure_date', '?')}")

    # ----- Search 9: Text output mode --------------------------------
    print("\n9. Text output mode (EIC archive)")
    print("-" * 40)

    text = await runner.run_text("maritime_search_voyages", archive="eic", max_results=5)
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
