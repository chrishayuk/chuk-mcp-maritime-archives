#!/usr/bin/env python3
"""
Route Explorer Demo -- chuk-mcp-maritime-archives

Explore the 8 standard VOC sailing routes with waypoints, durations,
hazards, and seasonal notes. Demonstrates position estimation --
given a departure date and route, estimate where a ship was on any
given date using linear interpolation between waypoints.

Demonstrates:
    maritime_list_routes (list and filter routes)
    maritime_get_route (full route with waypoints)
    maritime_estimate_position (interpolate ship position by date)

No network access required -- all data is local.

Usage:
    python examples/route_explorer_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Route Explorer Demo")
    print("=" * 60)

    # ---------------------------------------------------------------
    # 1. List all routes
    # ---------------------------------------------------------------
    print("\n--- All VOC sailing routes ---")
    result = await runner.run("maritime_list_routes")
    print(f"  {result['route_count']} routes available:\n")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")
        print(
            f"  {'':20s}  direction: {route['direction']}  "
            f"duration: ~{route['typical_duration_days']} days  "
            f"waypoints: {route['waypoint_count']}"
        )

    # ---------------------------------------------------------------
    # 2. Filter by direction
    # ---------------------------------------------------------------
    print("\n--- Outward routes only ---")
    result = await runner.run("maritime_list_routes", direction="outward")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    print("\n--- Intra-Asian routes ---")
    result = await runner.run("maritime_list_routes", direction="intra_asian")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    # ---------------------------------------------------------------
    # 3. Full route detail
    # ---------------------------------------------------------------
    print("\n--- Outer route detail ---")
    result = await runner.run("maritime_get_route", route_id="outward_outer")
    route = result["route"]

    print(f"  {route['name']}")
    print(f"  {route['description'][:100]}...")
    print(f"\n  Season: {route['season_notes'][:80]}...")
    print("\n  Hazards:")
    for h in route["hazards"]:
        print(f"    - {h}")
    print(f"\n  Waypoints ({len(route['waypoints'])}):")
    for wp in route["waypoints"]:
        stop = f" (stop: {wp['stop_days']}d)" if wp.get("stop_days", 0) > 0 else ""
        print(
            f"    Day {wp['cumulative_days']:3d}: {wp['name']:25s}  "
            f"({wp['lat']:7.2f}, {wp['lon']:7.2f})  "
            f"{wp['region']}{stop}"
        )

    # ---------------------------------------------------------------
    # 4. Position estimation -- Batavia voyage example
    # ---------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Position Estimation -- Track a ship across the ocean")
    print("-" * 60)
    print("\n  Scenario: A retourschip departs Texel on 1629-10-28")
    print("  on the outer route to Batavia. Where is it on each date?\n")

    departure = "1629-10-28"
    check_dates = [
        ("1629-10-28", "Departure day"),
        ("1629-11-05", "A week out -- English Channel"),
        ("1629-12-15", "Two months -- mid-Atlantic"),
        ("1630-02-15", "At the Cape (~day 110)"),
        ("1630-03-01", "Cape refreshment stop"),
        ("1630-04-15", "Indian Ocean crossing"),
        ("1630-05-05", "Approaching Sunda Strait"),
    ]

    for target, note in check_dates:
        result = await runner.run(
            "maritime_estimate_position",
            route_id="outward_outer",
            departure_date=departure,
            target_date=target,
        )
        est = result.get("estimate", result)
        pos = est.get("estimated_position", {})
        print(
            f"  {target}  ({note:30s})  "
            f"lat={pos.get('lat', '?'):7}  lon={pos.get('lon', '?'):7}  "
            f"conf={est.get('confidence', '?')}  "
            f"day {est.get('elapsed_days', '?')}/{est.get('total_route_days', '?')}"
        )

    # ---------------------------------------------------------------
    # 5. Text mode -- route detail
    # ---------------------------------------------------------------
    print("\n--- Text mode: Japan route ---")
    text = await runner.run_text("maritime_get_route", route_id="japan")
    print(text)

    # ---------------------------------------------------------------
    # 6. Text mode -- position estimate
    # ---------------------------------------------------------------
    print("\n--- Text mode: position estimate ---")
    text = await runner.run_text(
        "maritime_estimate_position",
        route_id="return",
        departure_date="1740-11-01",
        target_date="1741-01-15",
    )
    print(text)

    # ---------------------------------------------------------------
    # 7. Full JSON for a position estimate
    # ---------------------------------------------------------------
    print("\n--- Full JSON: position estimate ---")
    result = await runner.run(
        "maritime_estimate_position",
        route_id="ceylon",
        departure_date="1700-01-15",
        target_date="1700-02-01",
    )
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("Demo complete! Route tools enable LLMs to estimate")
    print("where a ship was on any date -- useful for investigating")
    print("wrecks and reconstructing lost voyages.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
