#!/usr/bin/env python3
"""
Voyage Search Demo -- chuk-mcp-maritime-archives

Search for VOC voyages using different filters and retrieve full
voyage details. Demonstrates the search-then-detail workflow
that an LLM would use to answer questions about historical voyages.

Demonstrates:
    maritime_search_voyages (multiple filter combinations)
    maritime_get_voyage (detail retrieval)

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
    print(f"   Found {result['voyage_count']} voyage(s)")

    for v in result["voyages"]:
        print(f"   {v['voyage_id']}: {v['ship_name']}")
        print(f"     Captain: {v.get('captain', 'Unknown')}")
        print(f"     Route: {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}")
        print(f"     Departure: {v.get('departure_date', '?')}")
        print(f"     Fate: {v.get('fate', '?')}")

    # ----- Search 2: Find wrecked voyages ----------------------------
    print("\n2. Search for wrecked voyages")
    print("-" * 40)

    result = await runner.run("maritime_search_voyages", fate="wrecked")
    print(f"   Found {result['voyage_count']} wrecked voyage(s)")

    for v in result["voyages"]:
        fate_str = f" [{v['fate']}]" if v.get("fate") else ""
        print(f"   {v['voyage_id']}: {v['ship_name']}{fate_str}")
        if v.get("departure_date"):
            print(f"     Departed: {v['departure_date']} from {v.get('departure_port', '?')}")

    # ----- Search 3: Get full voyage details -------------------------
    print("\n3. Get full voyage details for the Batavia")
    print("-" * 40)

    voyage = await runner.run("maritime_get_voyage", voyage_id="das:3456")
    detail = voyage["voyage"]
    print(f"   Voyage ID: {detail['voyage_id']}")
    print(f"   Ship: {detail['ship_name']} ({detail.get('ship_type', '?')})")
    print(f"   Tonnage: {detail.get('tonnage', '?')} lasten")
    print(f"   Captain: {detail.get('captain', '?')}")
    print(f"   Route: {detail.get('departure_port', '?')} -> {detail.get('destination_port', '?')}")
    print(f"   Departure: {detail.get('departure_date', '?')}")
    print(f"   Fate: {detail.get('fate', '?')}")

    if detail.get("incident"):
        inc = detail["incident"]
        print(f"   Incident:")
        print(f"     Date: {inc.get('date', '?')}")
        print(f"     Cause: {inc.get('cause', '?')}")
        print(f"     Lives lost: {inc.get('lives_lost', '?')}")
        if inc.get("position"):
            pos = inc["position"]
            print(f"     Position: {pos.get('lat', '?')}N, {pos.get('lon', '?')}E")

    if detail.get("summary"):
        print(f"   Summary: {detail['summary'][:100]}...")

    # ----- Search 4: Text output mode --------------------------------
    print("\n4. Search results in text mode")
    print("-" * 40)

    text = await runner.run_text("maritime_search_voyages", ship_name="Batavia")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
