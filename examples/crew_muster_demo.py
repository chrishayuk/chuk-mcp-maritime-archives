#!/usr/bin/env python3
"""
Crew Muster Demo -- chuk-mcp-maritime-archives

Search for VOC crew members in historical muster roll records.
The VOC Opvarenden database contains up to 774,200 personnel records
from 1633-1794, including name, rank, origin, pay, and fate.

Requires running ``scripts/download_crew.py`` first to download
the crew dataset from the Nationaal Archief (~80 MB).

Demonstrates:
    maritime_search_crew (by ship name, by rank)
    maritime_get_crew_member (full record from search results)

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

    if "error" in result:
        print(f"   No crew data: {result['error']}")
        print("   (Run scripts/download_crew.py to download crew records)")
        return

    print(f"   Found {result['crew_count']} crew record(s)")

    crew_ids = []
    for c in result["crew"]:
        rank = c.get("rank_english") or c.get("rank", "?")
        print(f"\n   {c['crew_id']}: {c['name']}")
        print(f"     Rank: {rank}")
        print(f"     Ship: {c.get('ship_name', '?')}")
        crew_ids.append(c["crew_id"])

    # ----- Get full crew member details -----------------------------
    if crew_ids:
        print("\n2. Full crew member details")
        print("-" * 40)

        for crew_id in crew_ids[:3]:
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
    else:
        print("\n2. (Skipped -- no crew results from search)")

    # ----- Search all crew ------------------------------------------
    print("\n3. Search all crew records")
    print("-" * 40)

    all_crew = await runner.run("maritime_search_crew", max_results=20)
    if "error" not in all_crew:
        print(f"   Total crew records: {all_crew['crew_count']}")

        ranks: dict[str, int] = {}
        for c in all_crew["crew"]:
            rank = c.get("rank_english") or c.get("rank", "unknown")
            ranks[rank] = ranks.get(rank, 0) + 1

        if ranks:
            print("\n   Breakdown by rank:")
            for rank, count in sorted(ranks.items()):
                print(f"     {rank}: {count}")
    else:
        print(f"   {all_crew['error']}")

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
