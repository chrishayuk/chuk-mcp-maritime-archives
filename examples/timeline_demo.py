#!/usr/bin/env python3
"""
Timeline Demo -- chuk-mcp-maritime-archives

Build a chronological timeline of events for a VOC voyage, combining
data from the DAS voyage database, route estimates, CLIWOC ship tracks,
and MAARER wreck records.

Demonstrates:
    maritime_get_timeline (basic and with positions)
    maritime_search_voyages (to find voyage IDs)

Usage:
    python examples/timeline_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Timeline Demo")
    print("=" * 60)

    # ----- 1. Find a wrecked voyage ------------------------------------
    print("\n1. Search for a wrecked voyage")
    print("-" * 40)

    voyages = await runner.run("maritime_search_voyages", fate="wrecked", max_results=5)
    if "error" in voyages:
        print(f"   {voyages['error']}")
        print("   (This demo requires DAS voyage data)")
        return

    voyage_id = None
    for v in voyages["voyages"]:
        print(f"   {v['voyage_id']}: {v['ship_name']} ({v.get('departure_date', '?')})")
        if voyage_id is None:
            voyage_id = v["voyage_id"]

    if not voyage_id:
        print("   No wrecked voyages found")
        return

    # ----- 2. Basic timeline (no positions) ----------------------------
    print(f"\n2. Timeline for {voyage_id} (basic)")
    print("-" * 40)

    timeline = await runner.run("maritime_get_timeline", voyage_id=voyage_id)

    if "error" in timeline:
        print(f"   {timeline['error']}")
    else:
        print(f"   Ship: {timeline.get('ship_name', '?')}")
        print(f"   Events: {timeline['event_count']}")
        print(f"   Sources: {', '.join(timeline.get('data_sources', []))}")
        print()
        for event in timeline["events"]:
            pos_str = ""
            pos = event.get("position")
            if pos and pos.get("lat") is not None:
                pos_str = f"  [{pos['lat']:.2f}N, {pos['lon']:.2f}E]"
            print(f"   {event['date']}  [{event['type']:20s}] {event['title']}{pos_str}")

    # ----- 3. Timeline with CLIWOC positions ---------------------------
    print(f"\n3. Timeline for {voyage_id} (with positions)")
    print("-" * 40)

    timeline_pos = await runner.run(
        "maritime_get_timeline",
        voyage_id=voyage_id,
        include_positions=True,
        max_positions=10,
    )

    if "error" not in timeline_pos:
        print(f"   Events: {timeline_pos['event_count']}")
        for event in timeline_pos["events"]:
            pos_str = ""
            pos = event.get("position")
            if pos and pos.get("lat") is not None:
                pos_str = f"  [{pos['lat']:.2f}N, {pos['lon']:.2f}E]"
            print(f"   {event['date']}  [{event['type']:20s}] {event['title']}{pos_str}")

    # ----- 4. GeoJSON LineString ---------------------------------------
    if "error" not in timeline and timeline.get("geojson"):
        print("\n4. GeoJSON track from timeline")
        print("-" * 40)
        geo = timeline["geojson"]
        coords = geo.get("geometry", {}).get("coordinates", [])
        print(f"   Type: {geo['geometry']['type']}")
        print(f"   Points: {len(coords)}")
        if coords:
            print(f"   Start: [{coords[0][0]:.2f}, {coords[0][1]:.2f}]")
            print(f"   End:   [{coords[-1][0]:.2f}, {coords[-1][1]:.2f}]")
        print()
        print(json.dumps(geo, indent=2))
    else:
        print("\n4. (No GeoJSON track available)")

    # ----- 5. Try a completed voyage -----------------------------------
    print("\n5. Timeline for a completed voyage")
    print("-" * 40)

    completed = await runner.run("maritime_search_voyages", fate="arrived", max_results=1)
    if "error" not in completed and completed["voyages"]:
        cv = completed["voyages"][0]
        print(f"   Voyage: {cv['voyage_id']} ({cv['ship_name']})")
        ct = await runner.run("maritime_get_timeline", voyage_id=cv["voyage_id"])
        if "error" not in ct:
            print(f"   Events: {ct['event_count']}")
            for event in ct["events"]:
                print(f"   {event['date']}  [{event['type']:20s}] {event['title']}")
        else:
            print(f"   {ct['error']}")
    else:
        print("   No completed voyages found in test data")

    # ----- 6. Text mode ------------------------------------------------
    print(f"\n6. Text output mode for {voyage_id}")
    print("-" * 40)

    text = await runner.run_text("maritime_get_timeline", voyage_id=voyage_id)
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
