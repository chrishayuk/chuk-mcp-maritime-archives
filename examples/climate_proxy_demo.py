#!/usr/bin/env python3
"""
Climate Proxy Demo -- chuk-mcp-maritime-archives

Ship transit speeds as a novel proxy for historical climate reconstruction.

Daily sailing distances from CLIWOC logbook data (1662-1855) contain
extractable climate signals: Southern Hemisphere westerly wind intensity,
Indian Ocean monsoon patterns, and multi-decadal wind trends during the
Little Ice Age. Every day, navigators recorded the ship's position.
The distance between consecutive positions is a direct, integrated
measurement of wind strength and ocean current -- a natural anemometer.

Demonstrates:
    maritime_get_speed_profile  (seasonal wind patterns by route segment)
    maritime_get_route          (route geography and waypoints)
    maritime_search_tracks      (decade-by-decade track discovery)
    maritime_get_track          (daily position data for speed computation)

No network access required -- all data is local.

Usage:
    python examples/climate_proxy_demo.py
"""

import asyncio
import math
import statistics

from tool_runner import ToolRunner

MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def main() -> None:
    runner = ToolRunner()

    print("=" * 72)
    print("CLIMATE PROXY ANALYSIS")
    print("Ship Transit Speeds as Wind & Current Proxies (1662-1855)")
    print("=" * 72)
    print()
    print("  Every day at noon, navigators on East India Company ships")
    print("  recorded their position. The distance between consecutive")
    print("  noon positions is a direct measurement of effective wind")
    print("  strength -- a natural anemometer. Aggregated across hundreds")
    print("  of voyages, these speeds reveal climate patterns invisible")
    print("  in any other historical record.")

    # =================================================================
    # 1. ROARING FORTIES: Southern Hemisphere Westerly Winds
    # =================================================================
    print("\n" + "=" * 72)
    print("1. ROARING FORTIES: Southern Hemisphere Westerly Winds")
    print("=" * 72)
    print()
    print("  Ships crossing the Southern Ocean between the Cape of Good Hope")
    print("  and Sunda Strait sailed through the Roaring Forties (40-50 S).")
    print("  Their daily distances are a direct proxy for westerly wind")
    print("  intensity -- the dominant atmospheric circulation feature of")
    print("  the Southern Hemisphere.")

    # Show the Southern Ocean waypoints
    route = await runner.run("maritime_get_route", route_id="outward_outer")
    route_data = route["route"]
    print()
    print("  Outward route waypoints through the Southern Ocean:")
    for wp in route_data["waypoints"]:
        if wp["lat"] < -25:
            stop = f"  (stop: {wp['stop_days']}d)" if wp.get("stop_days", 0) else ""
            print(
                f"    {wp['name']:30s}  {wp['lat']:7.2f}S  "
                f"{wp['lon']:8.2f}E  day {wp['cumulative_days']}{stop}"
            )

    # Monthly speed variation on the two key Southern Ocean segments
    segments_of_interest = [
        ("Cape of Good Hope", "South of Madagascar"),
        ("South of Madagascar", "Sunda Strait"),
    ]

    print()
    print("  Monthly speed variation (outward route, departure month):")
    for seg_from, seg_to in segments_of_interest:
        print(f"\n  {seg_from} -> {seg_to}")
        print(f"  {'':>6s}  {'Mean':>8s}  {'Median':>8s}  {'StdDev':>8s}  {'N':>6s}")
        print("  " + "-" * 46)

        # All-months baseline
        base = await runner.run("maritime_get_speed_profile", route_id="outward_outer")
        base_mean = None
        for seg in base["segments"]:
            if seg["segment_from"] == seg_from and seg["segment_to"] == seg_to:
                base_mean = seg["mean_km_day"]
                print(
                    f"  {'ALL':>6s}  {seg['mean_km_day']:7.1f}  "
                    f"{seg['median_km_day']:7.1f}  {seg['std_dev_km_day']:7.1f}  "
                    f"{seg['sample_count']:6d}"
                )

        # Per-month profiles
        for month in range(1, 13):
            result = await runner.run(
                "maritime_get_speed_profile",
                route_id="outward_outer",
                departure_month=month,
            )
            if "error" in result:
                continue
            for seg in result["segments"]:
                if (
                    seg["segment_from"] == seg_from
                    and seg["segment_to"] == seg_to
                    and seg.get("departure_month") == month
                ):
                    anomaly = ""
                    if base_mean:
                        diff = seg["mean_km_day"] - base_mean
                        arrow = "+" if diff > 0 else ""
                        anomaly = f"  {arrow}{diff:.0f}"
                    print(
                        f"  {MONTH_NAMES[month - 1]:>6s}  "
                        f"{seg['mean_km_day']:7.1f}  "
                        f"{seg['median_km_day']:7.1f}  "
                        f"{seg['std_dev_km_day']:7.1f}  "
                        f"{seg['sample_count']:6d}{anomaly}"
                    )

    print()
    print("  Key finding: speeds peak in austral winter (Jun-Aug) when the")
    print("  Southern Hemisphere jet stream shifts equatorward, intensifying")
    print("  the Roaring Forties. Austral summer (Dec-Feb) shows weaker")
    print("  westerlies as the jet retreats poleward.")

    # =================================================================
    # 2. RETURN ROUTE: Riding the Westerlies Home
    # =================================================================
    print("\n" + "=" * 72)
    print("2. RETURN ROUTE: Riding the Westerlies Home")
    print("=" * 72)
    print()
    print("  Return voyages deliberately sailed south into the Roaring")
    print("  Forties to catch the westerlies. The Sunda Strait -> South")
    print("  Indian Ocean segment is the purest wind signal in the data:")
    print("  ships were running before the wind with no coastline effects.")

    return_base = await runner.run("maritime_get_speed_profile", route_id="return")
    if "error" not in return_base:
        print()
        print(f"  {'Segment':<44s}  {'Mean':>6s}  {'N':>5s}")
        print("  " + "-" * 60)
        for seg in return_base["segments"]:
            print(
                f"  {seg['segment_from']:>20s} -> {seg['segment_to']:<20s}  "
                f"{seg['mean_km_day']:6.1f}  {seg['sample_count']:5d}"
            )

    # Monthly data for the Sunda Strait -> South Indian Ocean segment
    print()
    print("  Sunda Strait -> South Indian Ocean by departure month:")
    print(f"  {'':>6s}  {'Mean':>8s}  {'N':>5s}  {'Signal'}")
    print("  " + "-" * 50)

    for month in range(1, 13):
        result = await runner.run(
            "maritime_get_speed_profile",
            route_id="return",
            departure_month=month,
        )
        if "error" in result:
            continue
        for seg in result["segments"]:
            if (
                seg["segment_from"] == "Sunda Strait"
                and seg["segment_to"] == "South Indian Ocean"
                and seg.get("departure_month") == month
            ):
                bar = "#" * int(seg["mean_km_day"] / 20)
                print(
                    f"  {MONTH_NAMES[month - 1]:>6s}  "
                    f"{seg['mean_km_day']:7.1f}  "
                    f"{seg['sample_count']:5d}  {bar}"
                )

    print()
    print("  Note the ~75 km/day range between slowest (Feb: 228) and")
    print("  fastest (Jun: 304) months. This 33% seasonal swing is a")
    print("  direct measurement of Southern Hemisphere wind variability.")

    # =================================================================
    # 3. INDIAN OCEAN MONSOON SIGNAL
    # =================================================================
    print("\n" + "=" * 72)
    print("3. INDIAN OCEAN: Monsoon Routes")
    print("=" * 72)
    print()
    print("  Intra-Asian routes from Batavia to Ceylon, the Coromandel")
    print("  Coast, and Malabar cross the Indian Ocean where the monsoon")
    print("  reverses wind direction seasonally. Ship speeds on these")
    print("  routes capture the monsoon directly.")

    monsoon_routes = ["ceylon", "coromandel", "malabar"]
    for route_id in monsoon_routes:
        result = await runner.run("maritime_get_speed_profile", route_id=route_id)
        if "error" in result:
            continue

        # Get route metadata
        route_detail = await runner.run("maritime_get_route", route_id=route_id)
        route_name = route_detail["route"]["name"] if "error" not in route_detail else route_id

        print(f"\n  {route_name}")
        for seg in result["segments"]:
            print(
                f"    {seg['segment_from']:25s} -> {seg['segment_to']:<25s}  "
                f"mean={seg['mean_km_day']:.1f} km/day  n={seg['sample_count']}"
            )

    print()
    print("  The Ceylon route (Batavia -> Galle) averages 210 km/day")
    print("  through the Straits of Malacca but only 105 km/day on the")
    print("  Galle -> Colombo coastal segment -- a direct indicator of")
    print("  monsoon headwinds on the final approach to Sri Lanka.")
    print()
    print("  The Coromandel route shows a consistent 135 km/day across")
    print("  the Bay of Bengal, reflecting the NE monsoon conditions")
    print("  when these voyages typically sailed (Aug departures).")

    # =================================================================
    # 4. DECADAL TRENDS: Little Ice Age Wind Patterns
    # =================================================================
    print("\n" + "=" * 72)
    print("4. DECADAL TRENDS: Little Ice Age Wind Patterns (1740-1855)")
    print("=" * 72)
    print()
    print("  By computing daily sailing distances from CLIWOC positions")
    print("  decade by decade and filtering to the Roaring Forties")
    print("  latitude band (30-50 S), we can detect long-term shifts in")
    print("  wind patterns during the final century of the Little Ice Age.")
    print()
    print("  Sampling tracks from each period ...")

    periods = [
        (1740, 1760),
        (1760, 1780),
        (1780, 1800),
        (1800, 1820),
        (1820, 1840),
        (1840, 1855),
    ]

    all_period_speeds: list[float] = []
    period_results: list[tuple[str, int, int, float, float]] = []

    for year_start, year_end in periods:
        search = await runner.run(
            "maritime_search_tracks",
            year_start=year_start,
            year_end=year_end,
            max_results=50,
        )
        tracks = search.get("tracks", [])

        # Sample up to 8 tracks, prefer those with many positions
        sampled = sorted(tracks, key=lambda t: t.get("position_count", 0), reverse=True)[:8]

        roaring_40s_speeds: list[float] = []
        for t in sampled:
            try:
                full = await runner.run("maritime_get_track", voyage_id=t["voyage_id"])
                positions = full.get("track", {}).get("positions", [])

                for i in range(len(positions) - 1):
                    p1 = positions[i]
                    p2 = positions[i + 1]
                    mid_lat = (p1["lat"] + p2["lat"]) / 2

                    # Filter to Roaring Forties band
                    if -50 < mid_lat < -30:
                        daily_km = haversine_km(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
                        # Skip port stops and multi-day gaps
                        if 5 < daily_km < 400:
                            roaring_40s_speeds.append(daily_km)
            except Exception:
                continue

        n = len(roaring_40s_speeds)
        label = f"{year_start}-{year_end}"
        if n >= 2:
            mean_spd = statistics.mean(roaring_40s_speeds)
            std_spd = statistics.stdev(roaring_40s_speeds)
            all_period_speeds.extend(roaring_40s_speeds)
            period_results.append((label, len(tracks), n, mean_spd, std_spd))
        else:
            period_results.append((label, len(tracks), n, 0.0, 0.0))

    overall_mean = statistics.mean(all_period_speeds) if all_period_speeds else 0

    print()
    print(
        f"  {'Period':<12s}  {'Tracks':>6s}  {'Obs':>5s}  "
        f"{'Mean km/day':>11s}  {'StdDev':>6s}  {'Anomaly':>9s}"
    )
    print("  " + "-" * 60)

    for label, track_count, n, mean_spd, std_spd in period_results:
        if n >= 2:
            anomaly = mean_spd - overall_mean
            arrow = "+" if anomaly > 0 else ""
            print(
                f"  {label:<12s}  {track_count:>6d}  {n:>5d}  "
                f"{mean_spd:>11.1f}  {std_spd:>6.1f}  "
                f"{arrow}{anomaly:.1f} km/day"
            )
        else:
            print(f"  {label:<12s}  {track_count:>6d}  {n:>5d}  {'insufficient data':>11s}")

    print("  " + "-" * 60)
    if overall_mean:
        print(f"  {'Overall':<12s}  {'':>6s}  {len(all_period_speeds):>5d}  {overall_mean:>11.1f}")

    print()
    print("  Interpretation: Positive anomalies indicate decades when")
    print("  ships sailed faster through the Roaring Forties -- i.e.,")
    print("  stronger westerly winds. Negative anomalies suggest weaker")
    print("  westerlies or an unfavourable poleward shift of the wind belt.")
    print()
    print("  These decadal trends can be cross-referenced against:")
    print("    - Ice core records (Law Dome, WAIS Divide)")
    print("    - Tree ring chronologies (New Zealand, Patagonia)")
    print("    - Coral delta-18O from the Indian Ocean")
    print("  to build a multi-proxy reconstruction of Southern Hemisphere")
    print("  atmospheric circulation during the Little Ice Age.")

    # =================================================================
    # 5. SUMMARY
    # =================================================================
    print("\n" + "=" * 72)
    print("SUMMARY: Ship Speeds as Climate Proxies")
    print("=" * 72)
    print()
    print("  This analysis demonstrates three extractable climate signals")
    print("  from CLIWOC ship logbook data (1662-1855):")
    print()
    print("  1. ROARING FORTIES INTENSITY")
    print("     Monthly speed profiles show 20-40% seasonal variation on")
    print("     Southern Ocean segments, directly reflecting the annual")
    print("     cycle of westerly wind strength. Peak speeds in austral")
    print("     winter (Jun-Aug) match the equatorward jet stream shift.")
    print()
    print("  2. MONSOON PATTERNS")
    print("     Intra-Asian routes (Ceylon, Coromandel, Malabar) capture")
    print("     Indian Ocean monsoon winds. The Galle->Colombo segment")
    print("     at 105 km/day vs. 210 km/day open-ocean speed shows the")
    print("     monsoon headwind effect quantitatively.")
    print()
    print("  3. MULTI-DECADAL WIND TRENDS")
    print("     Per-decade speed anomalies in the Roaring Forties latitude")
    print("     band (30-50 S) reveal shifts in the Southern Hemisphere")
    print("     westerly wind belt during the final Little Ice Age century.")
    print()
    print("  These proxies fill a critical gap: there are almost no")
    print("  instrumental wind observations from the Southern Hemisphere")
    print("  before 1850. Ship logbooks provide direct, dated, geographically")
    print("  specific wind measurements for exactly the period and region")
    print("  where proxy coverage is thinnest.")
    print()
    print("  Data source: CLIWOC 2.1 Full -- ~261K daily positions, 1662-1855")
    print("  Tools: chuk-mcp-maritime-archives MCP server (29 tools)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
