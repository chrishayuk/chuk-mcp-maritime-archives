#!/usr/bin/env python3
"""
Crew Muster Demo -- chuk-mcp-maritime-archives

Search for VOC crew members in historical muster roll records.
The VOC Opvarenden database contains 774,200 personnel records
from 1633-1794, including name, rank, origin, pay, and fate.

Demonstrates:
    maritime_search_crew (by ship name)
    maritime_get_crew_member (full record)

Usage:
    python examples/crew_muster_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Crew Muster Demo")
    print("=" * 60)

    # ----- Search crew by ship name ---------------------------------
    print("\n1. Search crew of the Ridderschap van Holland")
    print("-" * 40)

    result = await runner.run("maritime_search_crew", ship_name="Ridderschap")
    print(f"   Found {result['crew_count']} crew record(s)")

    crew_ids = []
    for c in result["crew"]:
        rank = c.get("rank_english") or c.get("rank", "?")
        print(f"\n   {c['crew_id']}: {c['name']}")
        print(f"     Rank: {rank}")
        print(f"     Ship: {c.get('ship_name', '?')}")
        crew_ids.append(c["crew_id"])

    # ----- Get full crew member details -----------------------------
    print("\n2. Full crew member details")
    print("-" * 40)

    for crew_id in crew_ids:
        member = await runner.run("maritime_get_crew_member", crew_id=crew_id)

        if "crew_member" in member:
            m = member["crew_member"]
            print(f"\n   {m['name']}")
            print(f"     Crew ID: {m['crew_id']}")
            print(f"     Rank: {m.get('rank_english', m.get('rank', '?'))}")
            print(f"     Origin: {m.get('origin', '?')}")
            print(f"     Ship: {m.get('ship_name', '?')}")
            if m.get("monthly_pay_guilders"):
                print(f"     Monthly pay: {m['monthly_pay_guilders']} guilders")
            if m.get("embarkation_date"):
                print(f"     Embarked: {m['embarkation_date']}")
            if m.get("fate"):
                print(f"     Fate: {m['fate']}")

    # ----- Search all crew ------------------------------------------
    print("\n3. All crew in sample data")
    print("-" * 40)

    all_crew = await runner.run("maritime_search_crew")
    print(f"   Total crew records: {all_crew['crew_count']}")

    # Summarise by rank
    ranks: dict[str, int] = {}
    for c in all_crew["crew"]:
        rank = c.get("rank_english") or c.get("rank", "unknown")
        ranks[rank] = ranks.get(rank, 0) + 1

    print("\n   Breakdown by rank:")
    for rank, count in sorted(ranks.items()):
        print(f"     {rank}: {count}")

    # ----- Text output ----------------------------------------------
    print("\n4. Text output mode")
    print("-" * 40)
    text = await runner.run_text("maritime_search_crew", ship_name="Ridderschap")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
