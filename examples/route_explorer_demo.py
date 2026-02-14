#!/usr/bin/env python3
"""
Route Explorer Demo -- chuk-mcp-maritime-archives

Explore 18 historical sailing routes across 5 nations with waypoints,
durations, hazards, and seasonal notes. Demonstrates position estimation --
given a departure date and route, estimate where a ship was on any
given date using linear interpolation between waypoints.

Routes cover VOC (Dutch), EIC (British), Carreira da India (Portuguese),
Manila Galleon (Spanish), and SOIC (Swedish) sailing routes.

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
    print("\n--- All historical sailing routes ---")
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
    print("\n--- Outward routes (Europe to Asia, all nations) ---")
    result = await runner.run("maritime_list_routes", direction="outward")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    print("\n--- Intra-Asian routes ---")
    result = await runner.run("maritime_list_routes", direction="intra_asian")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    print("\n--- Pacific routes (Manila Galleon) ---")
    result = await runner.run("maritime_list_routes", direction="pacific_westbound")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")
    result = await runner.run("maritime_list_routes", direction="pacific_eastbound")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    # ---------------------------------------------------------------
    # 3. Filter by port
    # ---------------------------------------------------------------
    print("\n--- Routes departing from Lisbon ---")
    result = await runner.run("maritime_list_routes", departure_port="Lisbon")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    print("\n--- Routes to Canton ---")
    result = await runner.run("maritime_list_routes", destination_port="Canton")
    for route in result["routes"]:
        print(f"  {route['route_id']:20s}  {route['name']}")

    # ---------------------------------------------------------------
    # 4. Full route detail -- VOC outer route
    # ---------------------------------------------------------------
    print("\n--- VOC Outer route detail ---")
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
    # 5. Position estimation -- VOC Batavia voyage
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
    # 6. Carreira da India route detail
    # ---------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Carreira da India -- Lisbon to Goa")
    print("-" * 60)
    result = await runner.run("maritime_get_route", route_id="carreira_outward")
    route = result["route"]
    print(f"\n  {route['name']}")
    print(f"  Duration: ~{route['typical_duration_days']} days")
    print(f"  Waypoints ({len(route['waypoints'])}):")
    for wp in route["waypoints"]:
        stop = f" (stop: {wp['stop_days']}d)" if wp.get("stop_days", 0) > 0 else ""
        print(
            f"    Day {wp['cumulative_days']:3d}: {wp['name']:25s}  "
            f"({wp['lat']:7.2f}, {wp['lon']:7.2f}){stop}"
        )

    # ---------------------------------------------------------------
    # 7. Manila Galleon Pacific crossing estimation
    # ---------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Manila Galleon -- Acapulco to Manila (westbound)")
    print("-" * 60)
    print("\n  Scenario: A galleon departs Acapulco on 1600-03-15")
    print("  westbound via the trade winds. Track across the Pacific.\n")

    departure = "1600-03-15"
    check_dates = [
        ("1600-03-15", "Departure from Acapulco"),
        ("1600-04-01", "Open Pacific"),
        ("1600-04-20", "Mid-Pacific (~day 36)"),
        ("1600-05-10", "Approaching Guam (~day 56)"),
        ("1600-06-01", "Western Pacific"),
        ("1600-06-13", "Arriving Manila (~day 90)"),
    ]

    for target, note in check_dates:
        result = await runner.run(
            "maritime_estimate_position",
            route_id="galleon_westbound",
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
    # 8. Cross-nation comparison: outward routes
    # ---------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Cross-Nation Comparison -- Outward Routes")
    print("-" * 60)

    outward_routes = [
        ("outward_outer", "VOC (Dutch)"),
        ("eic_outward", "EIC (British)"),
        ("carreira_outward", "Carreira (Portuguese)"),
        ("soic_outward", "SOIC (Swedish)"),
    ]
    print(f"\n  {'Route':<22s}  {'Nation':<20s}  Duration  Waypoints")
    for route_id, nation in outward_routes:
        result = await runner.run("maritime_get_route", route_id=route_id)
        route = result["route"]
        print(
            f"  {route_id:<22s}  {nation:<20s}  "
            f"~{route['typical_duration_days']:3d} days  "
            f"{len(route['waypoints']):2d} waypoints"
        )

    # ---------------------------------------------------------------
    # 9. Text mode -- Japan route
    # ---------------------------------------------------------------
    print("\n--- Text mode: Japan route ---")
    text = await runner.run_text("maritime_get_route", route_id="japan")
    print(text)

    # ---------------------------------------------------------------
    # 10. Text mode -- position estimate
    # ---------------------------------------------------------------
    print("\n--- Text mode: EIC return position estimate ---")
    text = await runner.run_text(
        "maritime_estimate_position",
        route_id="eic_return",
        departure_date="1750-01-15",
        target_date="1750-04-01",
    )
    print(text)

    # ---------------------------------------------------------------
    # 11. Full JSON for a position estimate
    # ---------------------------------------------------------------
    print("\n--- Full JSON: SOIC outward position estimate ---")
    result = await runner.run(
        "maritime_estimate_position",
        route_id="soic_outward",
        departure_date="1745-02-01",
        target_date="1745-06-15",
    )
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("Demo complete! 18 routes across 5 nations enable LLMs to")
    print("estimate where a ship was on any date -- useful for")
    print("investigating wrecks and reconstructing lost voyages.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
