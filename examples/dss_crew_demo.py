#!/usr/bin/env python3
"""
DSS Crew Demo -- chuk-mcp-maritime-archives

Explores the Dutch Ships and Sailors (DSS) Linked Data Cloud:
    - GZMVOC: Ship-level muster records from Asian waters (1691-1791)
    - MDB: Individual crew records from northern Dutch provinces (1803-1837)

Demonstrates:
    1. List DSS archive metadata
    2. Search GZMVOC ship muster records
    3. Get full muster details (crew composition, wages)
    4. Cross-link musters to DAS voyages
    5. Search MDB individual crew from northern provinces
    6. Compare wages between time periods
    7. Multi-archive crew search (VOC Opvarenden + DSS)

No network access required -- all data is local.

Usage:
    python examples/dss_crew_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 72)
    print("DUTCH SHIPS AND SAILORS (DSS) LINKED DATA")
    print("GZMVOC Muster Records & MDB Crew Records")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. List DSS archive metadata
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("1. DSS ARCHIVE METADATA")
    print("-" * 72)

    result = await runner.run("maritime_get_archive", archive_id="dss")
    arch = result.get("archive", result)
    print(f"  Archive: {arch.get('name', '?')}")
    print(f"  Organisation: {arch.get('organisation', '?')}")
    print(f"  Coverage: {arch.get('coverage_start', '?')}-{arch.get('coverage_end', '?')}")
    print(f"  Record types: {', '.join(arch.get('record_types', []))}")
    total = arch.get("total_records", 0)
    print(f"  Total records: {total:,}")

    # ------------------------------------------------------------------
    # 2. Search GZMVOC ship muster records
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("2. SEARCH GZMVOC MUSTERS — Ships Mustered at Batavia")
    print("-" * 72)

    result = await runner.run(
        "maritime_search_musters",
        location="Batavia",
    )
    print(f"  Found {result.get('muster_count', 0)} musters at Batavia")
    for m in result.get("musters", [])[:5]:
        crew = m.get("total_crew", "?")
        print(f"    {m['muster_id']}: {m['ship_name']} ({m.get('muster_date', '?')}) — {crew} crew")

    # ------------------------------------------------------------------
    # 3. Get full muster details
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("3. MUSTER DETAILS — Crew Composition & Wages")
    print("-" * 72)

    musters = result.get("musters", [])
    if musters:
        muster_id = musters[0]["muster_id"]
        detail = await runner.run("maritime_get_muster", muster_id=muster_id)
        muster = detail.get("muster", {})
        print(f"  Ship: {muster.get('ship_name', '?')}")
        print(f"  Captain: {muster.get('captain', '?')}")
        print(f"  Date: {muster.get('muster_date', '?')}")
        print(f"  Location: {muster.get('muster_location', '?')}")
        print(f"  European crew: {muster.get('total_european', '?')}")
        print(f"  Asian crew: {muster.get('total_asian', '?')}")
        print(f"  Total crew: {muster.get('total_crew', '?')}")
        print(f"  Monthly wages: {muster.get('monthly_wages_guilders', '?')} guilders")
        print(f"  Mean wage: {muster.get('mean_wage_guilders', '?')} guilders/month")
        ranks = muster.get("ranks_summary", {})
        if ranks:
            print("  Ranks:")
            for rank, count in sorted(ranks.items(), key=lambda x: -x[1]):
                print(f"    {rank}: {count}")

    # ------------------------------------------------------------------
    # 4. Cross-link to DAS voyage
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("4. CROSS-LINK — Muster → DAS Voyage")
    print("-" * 72)

    # Find musters with DAS voyage links
    all_musters = await runner.run("maritime_search_musters")
    linked = [m for m in all_musters.get("musters", []) if m.get("das_voyage_id")]
    if linked:
        m = linked[0]
        das_id = m["das_voyage_id"]
        print(f"  Muster {m['muster_id']} ({m['ship_name']}) links to {das_id}")

        # Try to get the linked DAS voyage
        voyage = await runner.run("maritime_get_voyage", voyage_id=das_id)
        if voyage and "voyage" in voyage:
            v = voyage["voyage"]
            print(f"  Voyage: {v.get('ship_name', '?')}")
            print(
                f"  Departure: {v.get('departure_date', '?')} from {v.get('departure_port', '?')}"
            )
            print(f"  Destination: {v.get('destination_port', '?')}")
        else:
            print(f"  (DAS voyage {das_id} not in local dataset — expected for curated data)")
    else:
        print("  No musters have DAS voyage links in this dataset.")

    # ------------------------------------------------------------------
    # 5. Search MDB individual crew
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("5. SEARCH DSS CREW — Sailors from Groningen")
    print("-" * 72)

    result = await runner.run(
        "maritime_search_crew",
        origin="Groningen",
        archive="dss",
    )
    print(f"  Found {result.get('crew_count', 0)} crew from Groningen")
    for c in result.get("crew", [])[:5]:
        print(f"    {c['crew_id']}: {c['name']} — {c.get('rank_english') or c.get('rank', '?')}")

    # Get a full crew record
    crew_list = result.get("crew", [])
    if crew_list:
        detail = await runner.run("maritime_get_crew_member", crew_id=crew_list[0]["crew_id"])
        cm = detail.get("crew_member", {})
        print(f"\n  Full record: {cm.get('name', '?')}")
        print(f"    Ship: {cm.get('ship_name', '?')}")
        print(f"    Rank: {cm.get('rank_english', '?')} ({cm.get('rank', '?')})")
        print(f"    Origin: {cm.get('origin', '?')}")
        print(f"    Age: {cm.get('age', '?')}")
        print(f"    Monthly pay: {cm.get('monthly_pay_guilders', '?')} guilders")
        print(f"    Destination: {cm.get('destination', '?')}")

    # ------------------------------------------------------------------
    # 6. Compare wages between time periods
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("6. WAGE COMPARISON — Early vs Late VOC (GZMVOC Musters)")
    print("-" * 72)

    result = await runner.run(
        "maritime_compare_wages",
        group1_start=1691,
        group1_end=1740,
        group2_start=1741,
        group2_end=1791,
        source="musters",
    )
    g1 = result.get("group1_label", "?")
    g2 = result.get("group2_label", "?")
    print(
        f"  {g1}: n={result.get('group1_n', 0)}, "
        f"mean={result.get('group1_mean_wage', 0):.2f}, "
        f"median={result.get('group1_median_wage', 0):.2f} guilders/month"
    )
    print(
        f"  {g2}: n={result.get('group2_n', 0)}, "
        f"mean={result.get('group2_mean_wage', 0):.2f}, "
        f"median={result.get('group2_median_wage', 0):.2f} guilders/month"
    )
    diff = result.get("difference_pct", 0)
    direction = "higher" if diff > 0 else "lower"
    print(f"  Change: {abs(diff):.1f}% {direction} in later period")

    # ------------------------------------------------------------------
    # 7. Multi-archive crew search
    # ------------------------------------------------------------------
    print("\n" + "-" * 72)
    print("7. MULTI-ARCHIVE CREW — Sailors Named 'Jan' Across Archives")
    print("-" * 72)

    # Search VOC Opvarenden
    voc = await runner.run("maritime_search_crew", name="Jan", archive="voc_crew", max_results=5)
    voc_count = voc.get("crew_count", 0)
    total_voc = voc.get("total_count", voc_count)
    print(f"  VOC Opvarenden: {total_voc} matches (showing {voc_count})")
    for c in voc.get("crew", [])[:3]:
        print(f"    {c['crew_id']}: {c['name']} — {c.get('rank', '?')}")

    # Search DSS (MDB)
    dss = await runner.run("maritime_search_crew", name="Jan", archive="dss", max_results=5)
    dss_count = dss.get("crew_count", 0)
    total_dss = dss.get("total_count", dss_count)
    print(f"  DSS (MDB): {total_dss} matches (showing {dss_count})")
    for c in dss.get("crew", [])[:3]:
        print(f"    {c['crew_id']}: {c['name']} — {c.get('rank', '?')}")

    print(f"\n  Total across archives: {total_voc + total_dss}")

    print("\n" + "=" * 72)
    print("Demo complete.")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
