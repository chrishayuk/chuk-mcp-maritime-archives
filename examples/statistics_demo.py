#!/usr/bin/env python3
"""
Statistics Demo -- chuk-mcp-maritime-archives

Compute aggregate statistics across the maritime archives. Shows
total losses, lives lost, cargo value, and breakdowns by region,
cause, status, and decade.

Demonstrates:
    maritime_get_statistics (aggregate analysis)
    maritime_search_wrecks (underlying data)

Usage:
    python examples/statistics_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Statistics Demo")
    print("=" * 60)

    # ----- Aggregate statistics -------------------------------------
    print("\n1. Aggregate statistics across all archives")
    print("-" * 40)

    result = await runner.run("maritime_get_statistics")

    if "error" in result:
        print(f"   API unavailable: {result['error']}")
        print("   (This demo requires network access to the archives)")
        return

    stats = result["statistics"]

    summary = stats.get("summary", {})
    print(f"\n   Period: {stats.get('date_range', '?')}")
    print(f"   Archives: {', '.join(stats.get('archives_included', []))}")
    print("\n   Summary:")
    print(f"     Total losses: {summary.get('total_losses', 0)}")
    print(f"     Lives lost: {summary.get('lives_lost_total', 0):,}")
    print(f"     Cargo value lost: {summary.get('cargo_value_guilders_total', 0):,.0f} guilders")

    # Losses by region
    by_region = stats.get("losses_by_region", {})
    if by_region:
        print("\n   Losses by region:")
        for region, count in sorted(by_region.items(), key=lambda x: -x[1]):
            bar = "#" * (count * 3)
            print(f"     {region:25s}  {count:3d}  {bar}")

    # Losses by cause
    by_cause = stats.get("losses_by_cause", {})
    if by_cause:
        print("\n   Losses by cause:")
        for cause, count in sorted(by_cause.items(), key=lambda x: -x[1]):
            bar = "#" * (count * 3)
            print(f"     {cause:25s}  {count:3d}  {bar}")

    # Losses by status
    by_status = stats.get("losses_by_status", {})
    if by_status:
        print("\n   Wreck discovery status:")
        total = sum(by_status.values())
        for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total else 0
            print(f"     {status:25s}  {count:3d}  ({pct:.0f}%)")

    # Losses by decade
    by_decade = stats.get("losses_by_decade", {})
    if by_decade:
        print("\n   Losses by decade:")
        for decade, count in sorted(by_decade.items()):
            bar = "#" * (count * 3)
            print(f"     {decade}  {count:3d}  {bar}")

    # ----- Underlying data ------------------------------------------
    print("\n2. Underlying wreck data")
    print("-" * 40)

    wrecks = await runner.run("maritime_search_wrecks", max_results=10)
    if "error" not in wrecks:
        print(f"\n   Total wreck records: {wrecks['wreck_count']}")
        print("\n   Individual wrecks:")

        for w in wrecks["wrecks"]:
            status = w.get("status", "?")
            cause = w.get("loss_cause", "?")
            region = w.get("region", "?")
            print(
                f"     {w['ship_name']:25s}  {w.get('loss_date', '?'):12s}  {region:15s}  {cause:10s}  [{status}]"
            )
    else:
        print(f"   {wrecks['error']}")

    # ----- Text output mode -----------------------------------------
    print("\n3. Text output mode")
    print("-" * 40)
    text = await runner.run_text("maritime_get_statistics")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
