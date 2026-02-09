#!/usr/bin/env python3
"""
Voyage Search Demo -- chuk-mcp-maritime-archives

Search for VOC voyages using different filters and retrieve full
voyage details. Demonstrates the search-then-detail workflow
that an LLM would use to answer questions about historical voyages.

Demonstrates:
    maritime_search_voyages (multiple filter combinations)
    maritime_get_voyage (detail retrieval from search results)

Usage:
    python examples/voyage_search_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Voyage Search Demo")
    print("=" * 60)

    # ----- Search 1: Find a specific ship ----------------------------
    print("\n1. Search for the Batavia")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", ship_name="Batavia")

    if "error" in result:
        print(f"   API unavailable: {result['error']}")
        print("   (This demo requires network access to the DAS archive)")
        return

    print(f"   Found {result['voyage_count']} voyage(s)")

    first_id = None
    for v in result["voyages"]:
        print(f"   {v['voyage_id']}: {v['ship_name']}")
        print(f"     Captain: {v.get('captain', 'Unknown')}")
        print(f"     Route: {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}")
        print(f"     Departure: {v.get('departure_date', '?')}")
        print(f"     Fate: {v.get('fate', '?')}")
        if first_id is None:
            first_id = v["voyage_id"]

    # ----- Search 2: Find wrecked voyages ----------------------------
    print("\n2. Search for wrecked voyages")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", fate="wrecked", max_results=5)
    if "error" not in result:
        print(f"   Found {result['voyage_count']} wrecked voyage(s)")
        for v in result["voyages"]:
            fate_str = f" [{v['fate']}]" if v.get("fate") else ""
            print(f"   {v['voyage_id']}: {v['ship_name']}{fate_str}")
            if v.get("departure_date"):
                print(f"     Departed: {v['departure_date']} from {v.get('departure_port', '?')}")
    else:
        print(f"   {result['error']}")

    # ----- Search 3: Get full voyage details -------------------------
    if first_id:
        print(f"\n3. Get full voyage details for {first_id}")
        print("-" * 40)

        voyage = await runner.run("maritime_get_voyage", voyage_id=first_id)
        if "error" not in voyage:
            detail = voyage["voyage"]
            print(f"   Voyage ID: {detail.get('voyage_id', first_id)}")
            print(f"   Ship: {detail.get('ship_name', '?')} ({detail.get('ship_type', '?')})")
            print(f"   Tonnage: {detail.get('tonnage', '?')} lasten")
            print(f"   Captain: {detail.get('captain', '?')}")
            print(
                f"   Route: {detail.get('departure_port', '?')} -> {detail.get('destination_port', '?')}"
            )
            print(f"   Departure: {detail.get('departure_date', '?')}")
            print(f"   Fate: {detail.get('fate', '?')}")

            if detail.get("incident"):
                inc = detail["incident"]
                print("   Incident:")
                print(f"     Date: {inc.get('date', '?')}")
                print(f"     Cause: {inc.get('cause', '?')}")
                print(f"     Lives lost: {inc.get('lives_lost', '?')}")

            if detail.get("summary"):
                print(f"   Summary: {detail['summary'][:120]}...")
        else:
            print(f"   {voyage['error']}")
    else:
        print("\n3. (Skipped -- no voyage results from search)")

    # ----- Search 4: Date range filter --------------------------------
    print("\n4. Search voyages from 1620-1640")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", date_range="1620/1640", max_results=5)
    if "error" not in result:
        print(f"   Found {result['voyage_count']} voyage(s) in 1620-1640")
        for v in result["voyages"]:
            print(f"   {v['voyage_id']}: {v['ship_name']} ({v.get('departure_date', '?')})")
    else:
        print(f"   {result['error']}")

    # ----- Search 5: Text output mode --------------------------------
    print("\n5. Search results in text mode")
    print("-" * 40)

    text = await runner.run_text("maritime_search_voyages", ship_name="Batavia")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
