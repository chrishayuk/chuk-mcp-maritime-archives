#!/usr/bin/env python3
"""
Crew Demographics Demo -- chuk-mcp-maritime-archives

Aggregate crew demographics, reconstruct careers, and analyse
survival rates across the VOC Opvarenden dataset (774K records).

Demonstrates:
    maritime_crew_demographics (by rank, origin, decade, fate)
    maritime_crew_career (career reconstruction)
    maritime_crew_survival_analysis (mortality and desertion rates)

Usage:
    python examples/crew_demographics_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Crew Demographics Demo")
    print("=" * 60)

    # ----- Rank distribution -------------------------------------------
    print("\n1. Crew demographics by rank")
    print("-" * 40)

    result = await runner.run("maritime_crew_demographics", group_by="rank", top_n=10)

    if "error" in result:
        print(f"   Error: {result['error']}")
        print("   (Run scripts/download_crew.py to download crew records)")
        return

    print(f"   Total records: {result['total_records']:,}")
    print(f"   Groups: {result['group_count']}")
    for g in result["groups"][:5]:
        print(f"     {g['group_key']:>20s}: {g['count']:>8,}  ({g['percentage']:.1f}%)")

    # ----- Origin distribution -----------------------------------------
    print("\n2. Top crew origins")
    print("-" * 40)

    result = await runner.run("maritime_crew_demographics", group_by="origin", top_n=10)
    for g in result["groups"][:5]:
        print(f"     {g['group_key']:>20s}: {g['count']:>8,}  ({g['percentage']:.1f}%)")
    if result.get("other_count"):
        print(f"     {'(other)':>20s}: {result['other_count']:>8,}")

    # ----- Decade trends -----------------------------------------------
    print("\n3. Crew by decade (filtered to sailors)")
    print("-" * 40)

    result = await runner.run(
        "maritime_crew_demographics",
        group_by="decade",
        rank="matroos",
        top_n=20,
    )
    for g in result["groups"]:
        print(f"     {g['group_key']:>8s}: {g['count']:>8,}")

    # ----- Fate breakdown ----------------------------------------------
    print("\n4. Fate distribution")
    print("-" * 40)

    result = await runner.run("maritime_crew_demographics", group_by="fate")
    for g in result["groups"]:
        pct = g["percentage"]
        bar = "#" * int(pct / 2)
        print(f"     {g['group_key']:>20s}: {pct:5.1f}%  {bar}")

    # ----- Career reconstruction ---------------------------------------
    print("\n5. Career reconstruction: Jan Pietersz van der Horst")
    print("-" * 40)

    result = await runner.run("maritime_crew_career", name="Jan Pietersz van der Horst")
    print(f"   Individuals found: {result['individual_count']}")
    for ind in result["individuals"][:3]:
        print(f"\n   {ind['name']} (origin: {ind.get('origin', '?')})")
        print(f"     Voyages: {ind['voyage_count']}")
        if ind.get("ranks_held"):
            print(f"     Ranks: {' -> '.join(ind['ranks_held'])}")
        if ind.get("distinct_ships"):
            print(f"     Ships: {', '.join(ind['distinct_ships'])}")
        if ind.get("career_span_years"):
            print(f"     Career span: {ind['career_span_years']} years")
        print(f"     Final fate: {ind.get('final_fate', '?')}")

    # ----- Survival by rank --------------------------------------------
    print("\n6. Survival analysis by rank")
    print("-" * 40)

    result = await runner.run("maritime_crew_survival_analysis", group_by="rank", top_n=10)
    print(f"   Records with known fate: {result['total_with_known_fate']:,}")
    for g in result["groups"][:5]:
        print(
            f"     {g['group_key']:>20s}: n={g['total']:>6,}  "
            f"survived={g['survival_rate']:.1f}%  "
            f"died={g['mortality_rate']:.1f}%  "
            f"deserted={g['desertion_rate']:.1f}%"
        )

    # ----- Survival by decade ------------------------------------------
    print("\n7. Survival trends by decade")
    print("-" * 40)

    result = await runner.run("maritime_crew_survival_analysis", group_by="decade", top_n=20)
    for g in result["groups"]:
        print(
            f"     {g['group_key']:>8s}: mortality={g['mortality_rate']:5.1f}%  "
            f"desertion={g['desertion_rate']:5.1f}%  (n={g['total']:,})"
        )

    # ----- Text mode ---------------------------------------------------
    print("\n8. Text mode output")
    print("-" * 40)

    result = await runner.run_text(
        "maritime_crew_survival_analysis",
        group_by="rank",
        top_n=5,
    )
    print(result)

    print(f"\n{'=' * 60}")
    print("Crew demographics demo complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
