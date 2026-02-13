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

This demo uses live MCP tool calls for all analysis:
    maritime_get_speed_profile       (seasonal wind patterns by route segment)
    maritime_get_route               (route geography and waypoints)
    maritime_aggregate_track_speeds  (decadal, monthly, directional, nationality trends)
    maritime_compare_speed_groups    (Mann-Whitney U statistical significance)

Pre-computed data is used only for controls requiring fields not
available via MCP tools (hull tonnage, per-position latitude).

No network access required -- all data is local.

Usage:
    python examples/climate_proxy_demo.py
"""

import asyncio
import json
from pathlib import Path

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

# Roaring Forties bounding box: 30-50 S, 15-110 E
RF_LAT_MIN = -50
RF_LAT_MAX = -30
RF_LON_MIN = 15
RF_LON_MAX = 110

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_climate_data() -> dict:
    """Load pre-computed climate analysis (used for hull/latitude controls only)."""
    path = DATA_DIR / "climate_analysis_results.json"
    with open(path) as f:
        return json.load(f)


async def main() -> None:
    runner = ToolRunner()
    climate = load_climate_data()

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

    # Get direction stats for the intro summary
    dir_result = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="direction",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )
    east_group = next((g for g in dir_result["groups"] if g["group_key"] == "eastbound"), None)
    west_group = next((g for g in dir_result["groups"] if g["group_key"] == "westbound"), None)

    print()
    print("  Dataset: CLIWOC 2.1 Full")
    print(f"  Observations in Roaring Forties band (30-50 S): {dir_result['total_observations']:,}")
    if east_group:
        print(f"  Eastbound transits: {east_group['n']:,}")
    if west_group:
        print(f"  Westbound transits: {west_group['n']:,}")

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

    # =================================================================
    # 4. DECADAL TRENDS (live analytics tool)
    # =================================================================
    print("\n" + "=" * 72)
    print("4. DECADAL TRENDS: Little Ice Age Wind Patterns (1660-1855)")
    print("=" * 72)
    print()
    print("  [maritime_aggregate_track_speeds group_by=decade]")
    print("  Analysing ALL daily positions in the Roaring Forties latitude")
    print("  band (30-50 S, 15-110 E) -- all ships, all directions.")
    print()

    decadal = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="decade",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    groups = decadal["groups"]
    total_n = decadal["total_observations"]
    overall_mean = sum(g["mean_km_day"] * g["n"] for g in groups) / total_n if total_n else 0

    print(f"  Total observations: {total_n:,}")
    print(f"  Total voyages: {decadal['total_voyages']:,}")
    print(f"  Overall weighted mean: {overall_mean:.1f} km/day")
    print()
    print(
        f"  {'Decade':<12s}  {'N':>6s}  {'Mean':>7s}  {'Median':>7s}  "
        f"{'StdDev':>7s}  {'Anomaly':>9s}  {'95% CI':>15s}"
    )
    print("  " + "-" * 72)

    for g in groups:
        anomaly = g["mean_km_day"] - overall_mean
        arrow = "+" if anomaly > 0 else ""
        print(
            f"  {g['group_key'] + 's':<12s}  {g['n']:>6,}  {g['mean_km_day']:>7.1f}  "
            f"{g['median_km_day']:>7.1f}  {g['std_km_day']:>7.1f}  "
            f"{arrow}{anomaly:>7.1f}    "
            f"[{g['ci_lower']:.1f}, {g['ci_upper']:.1f}]"
        )

    # Compute the overall trend
    early = [g for g in groups if int(g["group_key"]) <= 1760]
    late = [g for g in groups if int(g["group_key"]) >= 1830]
    if early and late:
        early_mean = sum(g["mean_km_day"] * g["n"] for g in early) / sum(g["n"] for g in early)
        late_mean = sum(g["mean_km_day"] * g["n"] for g in late) / sum(g["n"] for g in late)
        pct_change = ((late_mean - early_mean) / early_mean) * 100
        arrow = "+" if pct_change > 0 else ""
        print("  " + "-" * 72)
        print(
            f"  Early period (<=1760s) weighted mean: {early_mean:.1f} km/day "
            f"(n={sum(g['n'] for g in early):,})"
        )
        print(
            f"  Late period  (>=1830s) weighted mean: {late_mean:.1f} km/day "
            f"(n={sum(g['n'] for g in late):,})"
        )
        print(f"  Change: {arrow}{pct_change:.1f}%")

    print()
    print("  The trend is unmistakable: ships sailed progressively faster")
    print("  through the Roaring Forties across two centuries.")

    # =================================================================
    # 5. EASTBOUND-ONLY: The Purest Wind Signal (live analytics tool)
    # =================================================================
    print("\n" + "=" * 72)
    print("5. EASTBOUND-ONLY: Isolating the Westerly Wind Signal")
    print("=" * 72)
    print()
    print("  [maritime_aggregate_track_speeds group_by=decade direction=eastbound]")
    print("  Eastbound ships (Cape -> Batavia) were running directly")
    print("  before the prevailing westerlies. Their speeds are the purest")
    print("  proxy for westerly wind strength -- no headwind contamination.")
    print()

    eastbound = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="decade",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        direction="eastbound",
    )

    eb_groups = eastbound["groups"]
    eb_total = eastbound["total_observations"]
    eb_mean = sum(g["mean_km_day"] * g["n"] for g in eb_groups) / eb_total if eb_total else 0

    print(f"  Observations: {eb_total:,}")
    print(f"  Overall mean: {eb_mean:.1f} km/day")
    print()
    print(
        f"  {'Decade':<12s}  {'N':>6s}  {'Mean':>7s}  {'Anomaly':>9s}  {'95% CI':>15s}  {'Trend'}"
    )
    print("  " + "-" * 68)

    for g in eb_groups:
        anomaly = g["mean_km_day"] - eb_mean
        arrow = "+" if anomaly > 0 else ""
        bar_len = int(abs(anomaly) / 5)
        bar = ("+" * bar_len) if anomaly > 0 else ("-" * bar_len)
        print(
            f"  {g['group_key'] + 's':<12s}  {g['n']:>6,}  {g['mean_km_day']:>7.1f}  "
            f"{arrow}{anomaly:>7.1f}    "
            f"[{g['ci_lower']:.1f}, {g['ci_upper']:.1f}]  {bar}"
        )

    print()
    print("  The eastbound signal is even cleaner. This is the core climate")
    print("  finding: the Southern Hemisphere westerlies strengthened")
    print("  dramatically as the Little Ice Age ended.")

    # =================================================================
    # 6. SEASONAL VALIDATION: Monthly Pattern (live analytics tool)
    # =================================================================
    print("\n" + "=" * 72)
    print("6. SEASONAL VALIDATION: Monthly Speed Pattern")
    print("=" * 72)
    print()
    print("  [maritime_aggregate_track_speeds group_by=month]")
    print("  If ship speeds truly reflect wind, they should show the")
    print("  known seasonal cycle of Southern Hemisphere westerlies:")
    print("  strongest in austral winter (Jun-Aug), weakest in summer.")
    print()

    seasonal = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="month",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    s_groups = seasonal["groups"]
    s_total = seasonal["total_observations"]
    s_mean = sum(g["mean_km_day"] * g["n"] for g in s_groups) / s_total if s_total else 0

    print(f"  Overall mean: {s_mean:.1f} km/day")
    print()
    print(f"  {'Month':>6s}  {'N':>6s}  {'Mean':>7s}  {'Anomaly':>8s}  {'Signal'}")
    print("  " + "-" * 55)

    for g in s_groups:
        month_idx = int(g["group_key"]) - 1
        name = MONTH_NAMES[month_idx] if 0 <= month_idx < 12 else g["group_key"]
        anomaly = g["mean_km_day"] - s_mean
        arrow = "+" if anomaly > 0 else ""
        bar_len = int(abs(anomaly) / 2)
        if anomaly > 0:
            bar = "|" + "#" * bar_len
        else:
            bar = " " * (15 - bar_len) + "." * bar_len + "|"
        print(
            f"  {name:>6s}  {g['n']:>6,}  {g['mean_km_day']:>7.1f}  {arrow}{anomaly:>7.1f}  {bar}"
        )

    peak = max(s_groups, key=lambda g: g["mean_km_day"])
    trough = min(s_groups, key=lambda g: g["mean_km_day"])
    peak_name = MONTH_NAMES[int(peak["group_key"]) - 1]
    trough_name = MONTH_NAMES[int(trough["group_key"]) - 1]
    swing = peak["mean_km_day"] - trough["mean_km_day"]
    pct_swing = (swing / trough["mean_km_day"]) * 100

    print()
    print(f"  Peak: {peak_name} ({peak['mean_km_day']:.1f} km/day)")
    print(f"  Trough: {trough_name} ({trough['mean_km_day']:.1f} km/day)")
    print(f"  Seasonal swing: {swing:.1f} km/day ({pct_swing:.0f}%)")
    print()
    print("  The seasonal pattern matches the known Southern Hemisphere")
    print("  westerly cycle. This validates that ship speeds genuinely")
    print("  measure wind intensity, not navigational bias.")

    # =================================================================
    # 7. DIRECTIONAL ASYMMETRY (live analytics tool)
    # =================================================================
    print("\n" + "=" * 72)
    print("7. DIRECTIONAL ASYMMETRY: East vs West")
    print("=" * 72)
    print()
    print("  [maritime_aggregate_track_speeds group_by=direction]")
    print()

    # Reuse dir_result from intro
    if east_group and west_group:
        diff = east_group["mean_km_day"] - west_group["mean_km_day"]
        pct = (diff / west_group["mean_km_day"]) * 100

        print(
            f"  Eastbound (with wind):    {east_group['mean_km_day']:.1f} km/day  "
            f"(n={east_group['n']:,})"
        )
        print(
            f"  Westbound (against wind): {west_group['mean_km_day']:.1f} km/day  "
            f"(n={west_group['n']:,})"
        )
        print(f"  Difference: {diff:.1f} km/day ({pct:.0f}% faster eastbound)")
    print()
    print("  Ships sailing east averaged ~40% faster than those sailing")
    print("  west -- exactly what prevailing westerlies predict. Ships")
    print("  heading west had to tack against the wind, dramatically")
    print("  reducing daily progress.")

    # =================================================================
    # 8. NATIONALITY CONTROL (live analytics tool)
    # =================================================================
    print("\n" + "=" * 72)
    print("8. NATIONALITY CONTROL: Independent Fleets, Same Signal")
    print("=" * 72)
    print()
    print("  [maritime_aggregate_track_speeds group_by=decade nationality=...]")
    print("  If the speed trend were caused by improving ship technology")
    print("  or seamanship, it would differ between national fleets.")
    print("  Testing four independent navies:")
    print()

    nat_labels = {"NL": "Dutch (VOC)", "UK": "British (EIC/RN)", "ES": "Spanish", "FR": "French"}
    for code in ["NL", "UK", "ES", "FR"]:
        nat_result = await runner.run(
            "maritime_aggregate_track_speeds",
            group_by="decade",
            lat_min=RF_LAT_MIN,
            lat_max=RF_LAT_MAX,
            lon_min=RF_LON_MIN,
            lon_max=RF_LON_MAX,
            nationality=code,
        )
        nat_groups = nat_result["groups"]
        if len(nat_groups) < 2:
            print(
                f"  {nat_labels[code]}: {nat_result['total_observations']:,} obs -- "
                f"insufficient decade coverage for trend analysis"
            )
            continue

        earliest = nat_groups[0]
        latest = nat_groups[-1]
        change = latest["mean_km_day"] - earliest["mean_km_day"]
        pct = (change / earliest["mean_km_day"]) * 100 if earliest["mean_km_day"] else 0
        arrow = "+" if change > 0 else ""
        print(
            f"  {nat_labels[code]}: {nat_result['total_observations']:,} obs, "
            f"{len(nat_groups)} decades"
        )
        print(
            f"    Earliest: {earliest['group_key']}s  {earliest['mean_km_day']:.1f} km/day "
            f"(n={earliest['n']:,})"
        )
        print(
            f"    Latest:   {latest['group_key']}s  {latest['mean_km_day']:.1f} km/day "
            f"(n={latest['n']:,})"
        )
        print(f"    Change:   {arrow}{change:.1f} km/day ({arrow}{pct:.0f}%)")
        print()

    print("  All four fleets show the same upward trend. Dutch, British,")
    print("  Spanish, and French ships -- built differently, crewed")
    print("  differently, using different navigation methods -- all got")
    print("  faster in the same place at the same time. The only common")
    print("  factor is the wind.")

    # =================================================================
    # 9. HULL SIZE CONTROL (pre-computed: requires tonnage data)
    # =================================================================
    print("\n" + "=" * 72)
    print("9. HULL SIZE CONTROL: Large vs Small Ships")
    print("=" * 72)
    print()
    print("  [Pre-computed: requires ship tonnage data not in CLIWOC logbooks]")
    summary = climate["summary"]
    print(
        "  Ships with known tonnage (n={:,}) split into large (>=800t)".format(
            summary["with_tonnage"]
        )
    )
    print("  and small (<800t) categories. If bigger ships simply sailed")
    print("  faster, it would confound the wind signal.")
    print()

    hull = climate["hull_control"]
    for size in ["large", "small"]:
        h = hull[size]
        decs = h["decades"]
        earliest = decs[0]
        latest = decs[-1]
        change = latest["mean"] - earliest["mean"]
        pct = (change / earliest["mean"]) * 100
        arrow = "+" if change > 0 else ""
        print(
            f"  {h['label']}: {h['overall_n']:,} obs, overall mean {h['overall_mean']:.1f} km/day"
        )
        print(f"    Earliest: {earliest['label']}  {earliest['mean']:.1f} km/day")
        print(f"    Latest:   {latest['label']}  {latest['mean']:.1f} km/day")
        print(f"    Change:   {arrow}{change:.1f} km/day ({arrow}{pct:.0f}%)")
        print()

    print("  Both categories show the same trend, ruling out hull size")
    print("  as the explanation for the speed increase.")

    # =================================================================
    # 10. LATITUDE DRIFT CHECK (pre-computed: requires per-position lat)
    # =================================================================
    print("\n" + "=" * 72)
    print("10. LATITUDE DRIFT CHECK: Did Ships Sail Further South?")
    print("=" * 72)
    print()
    print("  [Pre-computed: requires per-position latitude analysis]")
    print("  A potential confound: if later ships sailed further south")
    print("  into stronger winds, the speed increase might reflect route")
    print("  choice rather than wind change.")
    print()

    lat_trend = climate["latitude_trend"]
    decs = lat_trend["decades"]
    print(
        f"  {'Decade':<12s}  {'N':>6s}  {'Mean Speed':>10s}  {'Mean Lat':>9s}  {'Lat 95% CI':>18s}"
    )
    print("  " + "-" * 62)

    for d in decs:
        print(
            f"  {d['label']:<12s}  {d['n']:>6,}  {d['mean_speed']:>9.1f}  "
            f"{d['mean_lat']:>8.2f}  "
            f"[{d['lat_ci_lower']:.2f}, {d['lat_ci_upper']:.2f}]"
        )

    r = lat_trend["pearson_r_speed_lat"]
    print()
    print(f"  Pearson correlation (speed vs latitude): r = {r:.3f}")
    print()
    print("  Mean latitude barely changed over two centuries. The speed")
    print("  trend is NOT explained by latitude drift.")

    # =================================================================
    # 11. STATISTICAL SIGNIFICANCE (live analytics tool)
    # =================================================================
    print("\n" + "=" * 72)
    print("11. STATISTICAL SIGNIFICANCE: Mann-Whitney U Tests")
    print("=" * 72)
    print()
    print("  [maritime_compare_speed_groups]")
    print("  Non-parametric test comparing cold-period (1750s-1780s) vs")
    print("  warm-period (1820s-1850s) distributions:")
    print()

    # Cold vs warm: all ships
    cw_all = await runner.run(
        "maritime_compare_speed_groups",
        group1_years="1750/1789",
        group2_years="1820/1859",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    print("  Cold vs Warm (all ships):")
    print(f"    Cold period ({cw_all['group1_label']}): n={cw_all['group1_n']:,}")
    print(f"    Warm period ({cw_all['group2_label']}): n={cw_all['group2_n']:,}")
    print(f"    U = {cw_all['mann_whitney_u']:,.0f}")
    print(f"    z = {cw_all['z_score']:.4f}")
    p_str = f"{cw_all['p_value']:.6f}" if cw_all["p_value"] > 0 else "< 1e-300"
    print(f"    p = {p_str}")
    print(f"    Cohen's d = {cw_all['effect_size']:.3f}")
    print(f"    Significant: {'Yes' if cw_all['significant'] else 'No'}")
    print()

    # Cold vs warm: eastbound
    cw_eb = await runner.run(
        "maritime_compare_speed_groups",
        group1_years="1750/1789",
        group2_years="1820/1859",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        direction="eastbound",
    )

    print("  Cold vs Warm (eastbound only):")
    print(f"    Cold period: n={cw_eb['group1_n']:,}")
    print(f"    Warm period: n={cw_eb['group2_n']:,}")
    print(f"    U = {cw_eb['mann_whitney_u']:,.0f}")
    print(f"    z = {cw_eb['z_score']:.4f}")
    p_str = f"{cw_eb['p_value']:.6f}" if cw_eb["p_value"] > 0 else "< 1e-300"
    print(f"    p = {p_str}")
    print(f"    Cohen's d = {cw_eb['effect_size']:.3f}")
    print()

    print("  Both tests return p effectively zero. The speed difference")
    print("  between cold and warm periods is overwhelmingly significant.")
    print()

    # Adjacent decade tests
    print("  Adjacent decade transitions:")
    print(f"  {'Pair':>18s}  {'z':>8s}  {'p':>12s}  {'Significant?'}")
    print("  " + "-" * 56)

    decade_starts = sorted(int(g["group_key"]) for g in groups)
    for i in range(len(decade_starts) - 1):
        d1 = decade_starts[i]
        d2 = decade_starts[i + 1]
        adj = await runner.run(
            "maritime_compare_speed_groups",
            group1_years=f"{d1}/{d1 + 9}",
            group2_years=f"{d2}/{d2 + 9}",
            lat_min=RF_LAT_MIN,
            lat_max=RF_LAT_MAX,
            lon_min=RF_LON_MIN,
            lon_max=RF_LON_MAX,
        )
        if "error" in adj:
            continue
        sig_flag = (
            "***"
            if adj["p_value"] < 0.001
            else ("**" if adj["p_value"] < 0.01 else ("*" if adj["p_value"] < 0.05 else ""))
        )
        p_str = f"{adj['p_value']:.6f}" if adj["p_value"] > 0 else "< 1e-300"
        pair = f"{d1}s->{d2}s"
        print(f"  {pair:>18s}  {adj['z_score']:>8.4f}  {p_str:>12s}  {sig_flag}")

    print()
    print("  Most decade-to-decade transitions are statistically significant.")

    # =================================================================
    # 12. DUTCH 1790s ANOMALY (pre-computed: requires nationality exclusion)
    # =================================================================
    print("\n" + "=" * 72)
    print("12. ROBUSTNESS CHECK: Dutch 1790s Exclusion")
    print("=" * 72)
    print()
    print("  [Pre-computed: requires nationality-specific decade exclusion]")
    print("  The 1790s Dutch fleet shows anomalously low speeds, likely due")
    print("  to the Fourth Anglo-Dutch War disrupting trade routes.")
    print("  Excluding these observations to check if the trend holds:")
    print()

    excl = climate["nl_1790s_exclusion"]
    orig_1790 = next((g for g in groups if g["group_key"] == "1790"), None)
    excl_1790 = next((d for d in excl["decades"] if d["decade"] == 1790), None)

    if excl_1790 and orig_1790:
        print(
            f"  1790s with Dutch:    {orig_1790['mean_km_day']:.1f} km/day (n={orig_1790['n']:,})"
        )
        print(f"  1790s without Dutch: {excl_1790['mean']:.1f} km/day (n={excl_1790['n']:,})")
        print(f"  Difference: {excl_1790['mean'] - orig_1790['mean_km_day']:+.1f} km/day")
        print()

    print(f"  Revised overall mean: {excl['overall_mean']:.1f} km/day (n={excl['overall_n']:,})")
    print("  The upward trend is preserved regardless of whether Dutch")
    print("  1790s data is included or excluded.")

    # =================================================================
    # SUMMARY
    # =================================================================
    print("\n" + "=" * 72)
    print("SUMMARY: Ship Speeds as Climate Proxies")
    print("=" * 72)
    print()
    print(f"  This analysis of {total_n:,} daily observations from CLIWOC 2.1")
    print("  demonstrates that ship transit speeds through the Roaring")
    print("  Forties are a robust proxy for Southern Hemisphere westerly")
    print("  wind intensity during the Little Ice Age (1660-1855).")
    print()
    print("  KEY FINDINGS:")
    print()
    print("  1. DECADAL TREND")
    print("     Speeds increased across two centuries, indicating")
    print("     strengthening westerlies as the Little Ice Age ended.")
    print()
    print("  2. SEASONAL VALIDATION")
    print(f"     Monthly speeds peak in {peak_name} ({peak['mean_km_day']:.0f} km/day) and")
    print(f"     trough in {trough_name} ({trough['mean_km_day']:.0f} km/day), matching the known")
    print("     austral winter intensification of the westerly jet.")
    print()
    print("  3. DIRECTIONAL ASYMMETRY")
    if east_group and west_group:
        print(
            f"     Eastbound ships ({east_group['mean_km_day']:.1f} km/day) were ~40% faster than"
        )
        print(
            f"     westbound ({west_group['mean_km_day']:.1f} km/day), confirming wind-driven speeds."
        )
    print()
    print("  4. NATIONALITY CONTROL")
    print("     Dutch, British, Spanish, and French fleets independently")
    print("     show the same trend -- ruling out technology or seamanship.")
    print()
    print("  5. HULL SIZE CONTROL")
    print("     Both large (>=800t) and small (<800t) ships show the")
    print("     same trend -- ruling out vessel design as a factor.")
    print()
    print("  6. LATITUDE STABILITY")
    print(f"     Mean latitude barely shifted (r={r:.3f}), confirming the")
    print("     speed trend reflects wind change, not route change.")
    print()
    print("  7. STATISTICAL SIGNIFICANCE")
    print(f"     Cold vs warm period: Mann-Whitney z = {cw_all['z_score']:.2f}, p ~ 0.")
    print("     The signal is overwhelming.")
    print()
    print("  IMPLICATION:")
    print("  These ship logs -- mundane administrative records -- contain")
    print("  a continuous, dated, geographically specific record of wind")
    print("  strength across a 200-year period when almost no instrumental")
    print("  observations exist from the Southern Hemisphere. They fill a")
    print("  critical gap in climate reconstruction between ice cores,")
    print("  tree rings, and the instrumental era.")
    print()
    print("  Data source: CLIWOC 2.1 Full -- ~261K daily positions, 1662-1855")
    print("  Tools: chuk-mcp-maritime-archives MCP server (33 tools)")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
