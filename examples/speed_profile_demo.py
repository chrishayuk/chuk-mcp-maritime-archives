#!/usr/bin/env python3
"""
Speed Profile Demo -- chuk-mcp-maritime-archives

Show historical sailing speed statistics derived from CLIWOC ship track
data. Demonstrates per-segment speed profiles with seasonal variation.

Demonstrates:
    maritime_get_speed_profile (all-months and by departure month)
    maritime_estimate_position (with use_speed_profiles=True)

Usage:
    python examples/speed_profile_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Speed Profile Demo")
    print("=" * 60)

    # ----- 1. Outward outer route (all-months) -------------------------
    print("\n1. Speed profile: outward_outer route (all-months)")
    print("-" * 40)

    result = await runner.run("maritime_get_speed_profile", route_id="outward_outer")

    if "error" in result:
        print(f"   Error: {result['error']}")
        return

    print(f"   Route: {result['route_id']}")
    print(f"   Segments: {result['segment_count']}")
    print()
    for seg in result["segments"]:
        print(
            f"   {seg['segment_from']:25s} -> {seg['segment_to']:25s}  "
            f"mean={seg['mean_km_day']:6.1f} km/day  "
            f"(median={seg['median_km_day']:.0f}, std={seg['std_dev_km_day']:.0f}, "
            f"n={seg['sample_count']})"
        )

    # ----- 2. Seasonal comparison (October vs April departures) --------
    print("\n2. Seasonal comparison: October vs April departures")
    print("-" * 40)

    for month, label in [(10, "October"), (4, "April")]:
        result = await runner.run(
            "maritime_get_speed_profile",
            route_id="outward_outer",
            departure_month=month,
        )
        if "error" not in result:
            print(f"\n   {label} departures ({result['segment_count']} segments):")
            for seg in result["segments"]:
                month_str = (
                    f" [month {seg['departure_month']}]" if seg.get("departure_month") else " [all]"
                )
                print(
                    f"     {seg['segment_from']:25s} -> {seg['segment_to']:25s}  "
                    f"{seg['mean_km_day']:6.1f} km/day{month_str}"
                )
        else:
            print(f"   {label}: {result['error']}")

    # ----- 3. Return route ----------------------------------------------
    print("\n3. Speed profile: return route")
    print("-" * 40)

    result = await runner.run("maritime_get_speed_profile", route_id="return")
    if "error" not in result:
        print(f"   Route: {result['route_id']}  ({result['segment_count']} segments)")
        for seg in result["segments"]:
            print(
                f"   {seg['segment_from']:25s} -> {seg['segment_to']:25s}  "
                f"mean={seg['mean_km_day']:6.1f} km/day  n={seg['sample_count']}"
            )

    # ----- 4. Position estimate with speed profiles --------------------
    print("\n4. Position estimate enriched with speed data")
    print("-" * 40)

    est = await runner.run(
        "maritime_estimate_position",
        route_id="outward_outer",
        departure_date="1628-10-28",
        target_date="1628-12-27",
        use_speed_profiles=True,
    )
    if "error" not in est:
        e = est["estimate"]
        pos = e["estimated_position"]
        print(f"   Route: {e['route_name']}")
        print(f"   Elapsed: {e['elapsed_days']} days")
        print(f"   Position: {pos['lat']}N, {pos['lon']}E ({pos['region']})")
        seg = e["segment"]
        print(f"   Segment: {seg['from']} -> {seg['to']} ({seg['progress'] * 100:.0f}%)")
        if "speed_profile" in e:
            sp = e["speed_profile"]
            print(
                f"   Speed profile: {sp['mean_km_day']:.1f} km/day "
                f"(std={sp['std_dev_km_day']:.1f}, n={sp['sample_count']})"
            )
        else:
            print("   (No speed profile data for this segment)")
    else:
        print(f"   {est['error']}")

    # ----- 5. Text mode ------------------------------------------------
    print("\n5. Text output mode")
    print("-" * 40)

    text = await runner.run_text("maritime_get_speed_profile", route_id="outward_outer")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
