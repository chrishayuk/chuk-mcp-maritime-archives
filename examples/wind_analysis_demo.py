#!/usr/bin/env python3
"""
Wind Analysis Demo -- chuk-mcp-maritime-archives v0.21.0

Tests the chronometer vs wind change hypothesis using tortuosity analysis
and (when wind data is available) Beaufort force stratification.

If marine chronometers improved navigation, tortuosity (path_km / net_km)
should decrease over time. If tortuosity stays flat while the DiD speed
asymmetry holds, that confirms genuine wind change rather than better routing.

This demo uses live MCP tool calls for all analysis:
    maritime_aggregate_track_tortuosity  (tortuosity trends by decade/direction)
    maritime_track_tortuosity            (single-voyage tortuosity)
    maritime_wind_rose                   (Beaufort force distributions)
    maritime_did_speed_test              (DiD with optional wind conditioning)

No network access required -- all data is local.

Usage:
    python examples/wind_analysis_demo.py
"""

import asyncio

from tool_runner import ToolRunner

# Roaring Forties bounding box
RF_LAT_MIN = -50
RF_LAT_MAX = -30
RF_LON_MIN = 15
RF_LON_MAX = 110


async def main() -> None:
    runner = ToolRunner()

    print("=" * 72)
    print("WIND vs CHRONOMETER ANALYSIS")
    print("Tortuosity & Beaufort Stratification (v0.21.0)")
    print("=" * 72)
    print()
    print("  The DiD speed analysis found an asymmetric eastbound speed gain")
    print("  in the Southern Ocean post-1783. Two explanations:")
    print("    1) Genuine wind change (westerlies strengthened)")
    print("    2) Chronometer navigation (more direct routes)")
    print()
    print("  Tortuosity analysis resolves this: if ships sailed more")
    print("  directly after chronometers spread, R = path/net should drop.")
    print("  If R stays flat while speeds rise asymmetrically, that is wind.")

    # =================================================================
    # 1. TORTUOSITY BY DECADE
    # =================================================================
    print()
    print("=" * 72)
    print("1. TORTUOSITY BY DECADE (Roaring Forties, 30-50S)")
    print("=" * 72)

    tort_decade = await runner.run(
        "maritime_aggregate_track_tortuosity",
        group_by="decade",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    print(
        f"\n  Total voyages with >= {tort_decade['min_positions_required']} "
        f"positions: {tort_decade['total_voyages']}"
    )
    print()
    print(f"  {'Decade':<10} {'N':>5} {'Mean R':>8} {'Median':>8} {'Std':>7} {'95% CI':>16}")
    print(f"  {'-' * 10} {'-' * 5} {'-' * 8} {'-' * 8} {'-' * 7} {'-' * 16}")

    for g in tort_decade["groups"]:
        ci = f"[{g['ci_lower']:.3f}, {g['ci_upper']:.3f}]"
        print(
            f"  {g['group_key']:<10} {g['n']:>5} "
            f"{g['mean_tortuosity']:>8.4f} {g['median_tortuosity']:>8.4f} "
            f"{g['std_tortuosity']:>7.4f} {ci:>16}"
        )

    # =================================================================
    # 2. TORTUOSITY BY DIRECTION
    # =================================================================
    print()
    print("=" * 72)
    print("2. TORTUOSITY BY DIRECTION")
    print("=" * 72)

    tort_dir = await runner.run(
        "maritime_aggregate_track_tortuosity",
        group_by="direction",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    print()
    for g in tort_dir["groups"]:
        ci = f"[{g['ci_lower']:.3f}, {g['ci_upper']:.3f}]"
        print(
            f"  {g['group_key']:<12} N={g['n']:>4}  "
            f"Mean R={g['mean_tortuosity']:.4f}  "
            f"Median={g['median_tortuosity']:.4f}  CI={ci}"
        )

    print()
    print("  Interpretation: If eastbound R ~ westbound R, ships navigated")
    print("  equally directly in both directions (no chronometer advantage).")

    # =================================================================
    # 3. CHRONOMETER TEST: Period Comparison
    # =================================================================
    print()
    print("=" * 72)
    print("3. CHRONOMETER TEST: Pre vs Post-Chronometer Tortuosity")
    print("=" * 72)
    print()
    print("  Period 1: 1750-1779 (pre-chronometer)")
    print("  Period 2: 1800-1829 (post-chronometer)")

    tort_compare = await runner.run(
        "maritime_aggregate_track_tortuosity",
        group_by="decade",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        period1_years="1750/1779",
        period2_years="1800/1829",
        n_bootstrap=10000,
    )

    comp = tort_compare.get("comparison")
    if comp:
        print()
        print(f"  Pre-chronometer:  N={comp['period1_n']:<4}  Mean R={comp['period1_mean']:.4f}")
        print(f"  Post-chronometer: N={comp['period2_n']:<4}  Mean R={comp['period2_mean']:.4f}")
        print(f"  Difference:       {comp['diff']:+.4f}")
        print(f"  95% CI:           [{comp['ci_lower']:.4f}, {comp['ci_upper']:.4f}]")
        print(f"  p-value:          {comp['p_value']:.4f}")
        print(f"  Significant:      {comp['significant']}")
        print()
        if comp["significant"] and comp["diff"] < 0:
            print("  RESULT: Tortuosity decreased -> chronometers MAY have helped.")
        elif comp["significant"] and comp["diff"] > 0:
            print("  RESULT: Tortuosity increased -> counterintuitive, needs investigation.")
        else:
            print("  RESULT: No significant change in tortuosity -> chronometers did NOT")
            print("  make routes more direct. The DiD speed asymmetry is likely genuine")
            print("  wind change, not better navigation.")
    else:
        print("\n  Insufficient data for period comparison.")

    # =================================================================
    # 4. WIND ROSE (if wind data available)
    # =================================================================
    print()
    print("=" * 72)
    print("4. WIND ROSE — Beaufort Force Distribution")
    print("=" * 72)

    wr = await runner.run(
        "maritime_wind_rose",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        period1_years="1750/1779",
        period2_years="1800/1829",
    )

    if wr["has_wind_data"]:
        print(f"\n  Observations with wind data: {wr['total_with_wind']:,}")
        print(f"  Observations without:        {wr['total_without_wind']:,}")
        print()
        print(f"  {'Force':>5} {'Count':>8} {'%':>7} {'Mean km/day':>12}")
        print(f"  {'-' * 5} {'-' * 8} {'-' * 7} {'-' * 12}")
        for bc in wr["beaufort_counts"]:
            if bc["count"] > 0:
                spd = f"{bc['mean_speed_km_day']:.1f}" if bc.get("mean_speed_km_day") else "—"
                print(f"  {bc['force']:>5} {bc['count']:>8} {bc['percent']:>6.1f}% {spd:>12}")
    else:
        print()
        print("  No wind force data available in current dataset.")
        print("  Wind fields (W, D) are only available in CLIWOC 2.1 Full.")
        print("  Re-run scripts/download_cliwoc.py to extract wind data.")
        print()
        print("  Once available, the wind rose will show:")
        print("    - Beaufort force distribution by period")
        print("    - Mean speed at each force level")
        print("    - Whether wind distributions shifted (genuine wind change)")
        print("    - Whether speed-at-force changed (technology improvement)")

    # =================================================================
    # 5. SINGLE-VOYAGE TORTUOSITY EXAMPLE
    # =================================================================
    print()
    print("=" * 72)
    print("5. SINGLE-VOYAGE TORTUOSITY EXAMPLES")
    print("=" * 72)

    # Find a few voyages in the Roaring Forties
    search_result = await runner.run(
        "maritime_search_tracks",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        max_results=10,
    )

    shown = 0
    for t in search_result.get("tracks", []):
        tort = await runner.run(
            "maritime_track_tortuosity",
            voyage_id=t["voyage_id"],
            lat_min=RF_LAT_MIN,
            lat_max=RF_LAT_MAX,
            lon_min=RF_LON_MIN,
            lon_max=RF_LON_MAX,
        )
        if "error" not in tort:
            shown += 1
            name = tort.get("ship_name") or "Unknown"
            nat = tort.get("nationality") or "?"
            print(
                f"\n  Voyage {tort['voyage_id']}: {name} ({nat})"
                f"\n    Path: {tort['path_km']:.0f} km  "
                f"Net: {tort['net_km']:.0f} km  "
                f"R={tort['tortuosity_r']:.4f}  "
                f"Dir: {tort['inferred_direction']}  "
                f"Pos: {tort['n_in_box']}"
            )
            if shown >= 5:
                break

    if shown == 0:
        print("\n  No voyages with sufficient positions for tortuosity.")

    # =================================================================
    # Summary
    # =================================================================
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print()
    print("  Tortuosity analysis complements the DiD speed test:")
    print("  - If R drops over time -> chronometers helped (navigation gain)")
    print("  - If R stays flat while DiD is significant -> genuine wind change")
    print("  - Beaufort stratification (when available) makes it causal:")
    print("    * Speed at same Beaufort increases -> technology")
    print("    * Beaufort distributions shift -> real wind change")
    print("    * DiD scales with Beaufort -> wind change confirmed")
    print()
    print("  Together, these tools provide a publishable decomposition of")
    print("  the wind vs navigation question in 18th-century sailing data.")


if __name__ == "__main__":
    asyncio.run(main())
