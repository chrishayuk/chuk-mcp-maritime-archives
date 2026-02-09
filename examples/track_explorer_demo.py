#!/usr/bin/env python3
"""
Track Explorer Demo -- chuk-mcp-maritime-archives

Explore CLIWOC historical ship track data (1662-1855): ~261K daily
logbook positions from 8 European maritime nations.

Demonstrates:
    maritime_search_tracks (search by nationality, year range)
    maritime_get_track (full position history for a voyage)
    maritime_nearby_tracks (find ships near a position on a date)

No network access required -- all data is local.

Usage:
    python examples/track_explorer_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Track Explorer Demo")
    print("=" * 60)

    # ---------------------------------------------------------------
    # 1. Search all tracks (first 10)
    # ---------------------------------------------------------------
    print("\n--- All CLIWOC tracks (first 10) ---")
    result = await runner.run("maritime_search_tracks", max_results=10)
    print(f"  Found {result['track_count']} tracks:")
    for t in result["tracks"]:
        nat = t.get("nationality") or "?"
        print(
            f"  Voyage {t['voyage_id']:5d}  [{nat}]  "
            f"{t.get('start_date', '?'):12s} to {t.get('end_date', '?'):12s}  "
            f"{t.get('position_count', 0)} positions"
        )

    # ---------------------------------------------------------------
    # 2. Search by nationality
    # ---------------------------------------------------------------
    print("\n--- Dutch tracks (first 5) ---")
    result = await runner.run("maritime_search_tracks", nationality="NL", max_results=5)
    for t in result["tracks"]:
        print(
            f"  Voyage {t['voyage_id']:5d}  "
            f"{t.get('start_date', '?'):12s} to {t.get('end_date', '?'):12s}  "
            f"~{t.get('duration_days', '?')} days"
        )

    print("\n--- Spanish tracks (first 5) ---")
    result = await runner.run("maritime_search_tracks", nationality="ES", max_results=5)
    for t in result["tracks"]:
        print(
            f"  Voyage {t['voyage_id']:5d}  "
            f"{t.get('start_date', '?'):12s} to {t.get('end_date', '?'):12s}  "
            f"~{t.get('duration_days', '?')} days"
        )

    # ---------------------------------------------------------------
    # 3. Search by year range
    # ---------------------------------------------------------------
    print("\n--- British tracks from 1780-1790 ---")
    result = await runner.run(
        "maritime_search_tracks",
        nationality="UK",
        year_start=1780,
        year_end=1790,
        max_results=5,
    )
    print(f"  Found {result['track_count']} tracks:")
    for t in result["tracks"]:
        print(
            f"  Voyage {t['voyage_id']:5d}  "
            f"{t.get('start_date', '?'):12s} to {t.get('end_date', '?'):12s}  "
            f"{t.get('position_count', 0)} positions"
        )

    # ---------------------------------------------------------------
    # 4. Get full track detail
    # ---------------------------------------------------------------
    print("\n--- Full track detail ---")
    # Get first Dutch track
    search = await runner.run("maritime_search_tracks", nationality="NL", max_results=1)
    vid = search["tracks"][0]["voyage_id"]
    result = await runner.run("maritime_get_track", voyage_id=vid)
    track = result["track"]

    print(f"  CLIWOC Voyage {track['voyage_id']}")
    print(f"  Nationality: {track.get('nationality', '?')}")
    print(f"  Period: {track.get('start_date', '?')} to {track.get('end_date', '?')}")
    print(f"  Duration: ~{track.get('duration_days', '?')} days")
    print(f"  Positions: {track.get('position_count', 0)}")
    print("\n  First 10 positions:")
    for pos in track["positions"][:10]:
        print(
            f"    {pos.get('date', '?'):12s}  "
            f"lat={pos.get('lat', '?'):8.4f}  "
            f"lon={pos.get('lon', '?'):8.4f}"
        )
    if len(track["positions"]) > 10:
        print(f"    ... and {len(track['positions']) - 10} more")

    # ---------------------------------------------------------------
    # 5. Find nearby ships
    # ---------------------------------------------------------------
    print("\n" + "-" * 60)
    print("Nearby Ships -- who else was in the area?")
    print("-" * 60)

    # Use a position from the track we just looked at
    mid_pos = track["positions"][len(track["positions"]) // 2]
    search_lat = mid_pos["lat"]
    search_lon = mid_pos["lon"]
    search_date = mid_pos["date"]

    print(f"\n  Searching near ({search_lat}, {search_lon}) on {search_date}")
    print("  Radius: 1000km")
    result = await runner.run(
        "maritime_nearby_tracks",
        lat=search_lat,
        lon=search_lon,
        date=search_date,
        radius_km=1000,
    )

    if "track_count" in result:
        print(f"  Found {result['track_count']} ships nearby:")
        for t in result["tracks"]:
            nat = t.get("nationality") or "?"
            mp = t["matching_position"]
            print(
                f"    Voyage {t['voyage_id']:5d} [{nat}]  "
                f"at ({mp['lat']:.2f}, {mp['lon']:.2f})  "
                f"{t['distance_km']}km away"
            )
    else:
        print(f"  {result.get('error', 'No results')}")

    # ---------------------------------------------------------------
    # 6. Text mode -- track search
    # ---------------------------------------------------------------
    print("\n--- Text mode: French tracks ---")
    text = await runner.run_text("maritime_search_tracks", nationality="FR", max_results=3)
    print(text)

    # ---------------------------------------------------------------
    # 7. Text mode -- track detail
    # ---------------------------------------------------------------
    print("\n--- Text mode: track detail ---")
    text = await runner.run_text("maritime_get_track", voyage_id=vid)
    print(text)

    # ---------------------------------------------------------------
    # 8. Full JSON for a nearby search
    # ---------------------------------------------------------------
    print("\n--- Full JSON: nearby tracks ---")
    result = await runner.run(
        "maritime_nearby_tracks",
        lat=search_lat,
        lon=search_lon,
        date=search_date,
        radius_km=500,
        max_results=3,
    )
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("Demo complete! CLIWOC track tools let LLMs search ~261K")
    print("historical ship positions to find context around maritime")
    print("events, reconstruct routes, and discover nearby vessels.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
