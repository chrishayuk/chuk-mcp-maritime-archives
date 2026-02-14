#!/usr/bin/env python3
"""
Volcanic Signal Demo -- chuk-mcp-maritime-archives

Six novel research analyses using CLIWOC ship speed data:

1. LAKI ERUPTION 1783 — Did the largest volcanic event of the millennium
   show up in ship speeds through the Roaring Forties?

2. EASTBOUND/WESTBOUND RATIO — Decomposing wind change from technology
   improvement using directional speed asymmetry.

3. SEASONAL AMPLITUDE TREND — Did the winter/summer speed difference
   change over time, revealing jet stream evolution?

4. SPATIAL VARIATION — Did westerly intensification affect the western
   and eastern Indian Ocean sectors equally?

5. SEASONAL LAKI SIGNAL — Austral winter vs summer decomposition of the
   Laki signal using month_start/month_end filtering.

6. FORMAL DiD TEST — Difference-in-Differences (direction x period)
   with voyage-level aggregation and bootstrap confidence intervals.

All analysis uses live MCP tool calls via maritime_aggregate_track_speeds,
maritime_compare_speed_groups, and maritime_did_speed_test.

No network access required -- all data is local.

Usage:
    python examples/volcanic_signal_demo.py
"""

import asyncio

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

# Roaring Forties bounding box
RF_LAT_MIN = -50
RF_LAT_MAX = -30
RF_LON_MIN = 15
RF_LON_MAX = 110


async def section_laki(runner: ToolRunner) -> None:
    """Section 1: Laki eruption 1783 — volcanic signal in annual speeds."""
    print("=" * 72)
    print("1. LAKI ERUPTION 1783: Volcanic Signal in Ship Speeds")
    print("=" * 72)
    print()
    print("  In June 1783, the Laki fissure in Iceland erupted for eight")
    print("  months — the largest volcanic event of the millennium. The")
    print("  eruption injected massive quantities of sulfur dioxide into")
    print("  the atmosphere, causing the 'dry fog' across Europe and a")
    print("  measurable cooling of the Northern Hemisphere.")
    print()
    print("  Climate theory predicts that Northern Hemisphere cooling")
    print("  shifts the thermal equator southward, displacing the Southern")
    print("  Hemisphere westerly jet equatorward. This should WEAKEN the")
    print("  Roaring Forties — and show up as a dip in ship speeds.")
    print()
    print("  [maritime_aggregate_track_speeds group_by=year, 1775-1800]")
    print()

    result = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="year",
        year_start=1775,
        year_end=1800,
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    groups = result["groups"]
    if not groups:
        print("  No data available for this period.")
        return

    total_n = sum(g["n"] for g in groups)
    overall_mean = sum(g["mean_km_day"] * g["n"] for g in groups) / total_n if total_n else 0

    print(f"  Total observations: {total_n:,}")
    print(f"  Overall mean (1775-1800): {overall_mean:.1f} km/day")
    print()
    print(f"  {'Year':<8s}  {'N':>6s}  {'Mean':>7s}  {'Anomaly':>9s}  {'95% CI':>15s}  {'Signal'}")
    print("  " + "-" * 68)

    for g in groups:
        year = int(g["group_key"])
        anomaly = g["mean_km_day"] - overall_mean
        arrow = "+" if anomaly > 0 else ""
        # Flag the eruption years
        marker = ""
        if year == 1783:
            marker = "  << LAKI ERUPTION"
        elif year in (1784, 1785):
            marker = "  << post-eruption"

        print(
            f"  {g['group_key']:<8s}  {g['n']:>6,}  {g['mean_km_day']:>7.1f}  "
            f"{arrow}{anomaly:>7.1f}    "
            f"[{g['ci_lower']:.1f}, {g['ci_upper']:.1f}]{marker}"
        )

    # Identify the eruption-period anomaly
    pre_laki = [g for g in groups if 1778 <= int(g["group_key"]) <= 1782]
    post_laki = [g for g in groups if 1783 <= int(g["group_key"]) <= 1786]
    if pre_laki and post_laki:
        pre_n = sum(g["n"] for g in pre_laki)
        post_n = sum(g["n"] for g in post_laki)
        pre_mean = sum(g["mean_km_day"] * g["n"] for g in pre_laki) / pre_n if pre_n else 0
        post_mean = sum(g["mean_km_day"] * g["n"] for g in post_laki) / post_n if post_n else 0
        diff = post_mean - pre_mean
        print()
        print(f"  Pre-eruption mean  (1778-1782): {pre_mean:.1f} km/day (n={pre_n:,})")
        print(f"  Post-eruption mean (1783-1786): {post_mean:.1f} km/day (n={post_n:,})")
        print(f"  Difference: {diff:+.1f} km/day")

    # Statistical test: pre vs post Laki
    print()
    print("  [maritime_compare_speed_groups: pre-Laki vs post-Laki]")
    comparison = await runner.run(
        "maritime_compare_speed_groups",
        group1_years="1778/1782",
        group2_years="1783/1786",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
    )

    print(
        f"  Pre-Laki  (1778-1782): n={comparison['group1_n']:,}, "
        f"mean={comparison['group1_mean']:.1f} km/day"
    )
    print(
        f"  Post-Laki (1783-1786): n={comparison['group2_n']:,}, "
        f"mean={comparison['group2_mean']:.1f} km/day"
    )
    p_str = f"{comparison['p_value']:.6f}" if comparison["p_value"] > 0 else "< 1e-300"
    print(f"  Mann-Whitney z = {comparison['z_score']:.4f}, p = {p_str}")
    sig = "Yes" if comparison["significant"] else "No"
    print(f"  Significant at p < 0.05: {sig}")

    print()
    print("  Note: Whether or not the Laki signal is statistically")
    print("  detectable depends on sample size in these specific years.")
    print("  The 1783 eruption's atmospheric effects lasted ~2 years;")
    print("  any speed anomaly should appear in 1783-1785 and recover")
    print("  by 1786-1787.")


async def section_ew_ratio(runner: ToolRunner) -> None:
    """Section 2: E/W speed ratio — wind vs technology decomposition."""
    print("\n" + "=" * 72)
    print("2. EASTBOUND/WESTBOUND RATIO: Wind vs Technology")
    print("=" * 72)
    print()
    print("  The key insight: if ships got faster because of better")
    print("  technology (hull design, rigging, seamanship), BOTH eastbound")
    print("  and westbound ships would improve equally — the E/W ratio")
    print("  stays constant. But if the winds got stronger, eastbound")
    print("  ships (running before the westerlies) benefit MORE than")
    print("  westbound ships (fighting headwinds) — the E/W ratio")
    print("  INCREASES over time.")
    print()
    print("  This ratio is the smoking gun that separates wind from")
    print("  technology.")
    print()

    # Get eastbound and westbound speeds by decade
    eastbound = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="decade",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        direction="eastbound",
    )
    westbound = await runner.run(
        "maritime_aggregate_track_speeds",
        group_by="decade",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        direction="westbound",
    )

    eb_by_decade = {g["group_key"]: g for g in eastbound["groups"]}
    wb_by_decade = {g["group_key"]: g for g in westbound["groups"]}
    common_decades = sorted(set(eb_by_decade) & set(wb_by_decade))

    if not common_decades:
        print("  Insufficient data for E/W ratio analysis.")
        return

    print(
        f"  {'Decade':<10s}  {'East':>7s}  {'West':>7s}  "
        f"{'E/W Ratio':>10s}  {'E-W Diff':>9s}  {'Signal'}"
    )
    print("  " + "-" * 64)

    ratios = []
    for decade in common_decades:
        eb = eb_by_decade[decade]
        wb = wb_by_decade[decade]
        ratio = eb["mean_km_day"] / wb["mean_km_day"] if wb["mean_km_day"] > 0 else 0
        diff = eb["mean_km_day"] - wb["mean_km_day"]
        ratios.append((decade, ratio, diff, eb["n"], wb["n"]))

        bar_len = int((ratio - 1.0) * 20)
        bar = "#" * max(0, bar_len)
        print(
            f"  {decade + 's':<10s}  {eb['mean_km_day']:>7.1f}  "
            f"{wb['mean_km_day']:>7.1f}  {ratio:>10.3f}  "
            f"{diff:>+8.1f}  {bar}"
        )

    if len(ratios) >= 2:
        first_ratio = ratios[0][1]
        last_ratio = ratios[-1][1]
        ratio_change = ((last_ratio - first_ratio) / first_ratio) * 100
        print()
        print(f"  Earliest ratio ({ratios[0][0]}s): {first_ratio:.3f}")
        print(f"  Latest ratio   ({ratios[-1][0]}s): {last_ratio:.3f}")
        print(f"  Ratio change: {ratio_change:+.1f}%")
        print()
        if ratio_change > 5:
            print("  The E/W ratio INCREASED over time. This is consistent")
            print("  with strengthening westerlies — eastbound ships gained")
            print("  more than westbound ships, exactly as wind theory predicts.")
        elif ratio_change < -5:
            print("  The E/W ratio DECREASED over time. This suggests a")
            print("  technology-dominated signal where westbound tacking")
            print("  efficiency improved more than eastbound running.")
        else:
            print("  The E/W ratio stayed roughly constant, suggesting a")
            print("  mix of wind and technology effects.")


async def section_seasonal_amplitude(runner: ToolRunner) -> None:
    """Section 3: Seasonal amplitude trend — jet stream behavior."""
    print("\n" + "=" * 72)
    print("3. SEASONAL AMPLITUDE: Jet Stream Evolution")
    print("=" * 72)
    print()
    print("  The Southern Hemisphere westerlies have a strong seasonal")
    print("  cycle: strongest in austral winter (Jun-Aug), weakest in")
    print("  summer (Dec-Feb). If the jet stream strengthened uniformly,")
    print("  the winter/summer amplitude stays constant. If it strengthened")
    print("  preferentially in one season, the amplitude changes.")
    print()
    print("  We measure this by computing monthly speed patterns for three")
    print("  eras and comparing peak-to-trough amplitude.")
    print()

    eras = [
        ("1700/1749", 1700, 1749),
        ("1770/1809", 1770, 1809),
        ("1820/1855", 1820, 1855),
    ]

    era_results = []
    for label, y_start, y_end in eras:
        result = await runner.run(
            "maritime_aggregate_track_speeds",
            group_by="month",
            year_start=y_start,
            year_end=y_end,
            lat_min=RF_LAT_MIN,
            lat_max=RF_LAT_MAX,
            lon_min=RF_LON_MIN,
            lon_max=RF_LON_MAX,
        )
        era_results.append((label, result))

    # Print comparison table
    for label, result in era_results:
        groups = result["groups"]
        if not groups:
            print(f"  {label}: No data")
            continue

        total_n = sum(g["n"] for g in groups)
        era_mean = sum(g["mean_km_day"] * g["n"] for g in groups) / total_n if total_n else 0
        peak = max(groups, key=lambda g: g["mean_km_day"])
        trough = min(groups, key=lambda g: g["mean_km_day"])
        peak_month = MONTH_NAMES[int(peak["group_key"]) - 1]
        trough_month = MONTH_NAMES[int(trough["group_key"]) - 1]
        amplitude = peak["mean_km_day"] - trough["mean_km_day"]
        pct_amp = (amplitude / trough["mean_km_day"]) * 100 if trough["mean_km_day"] else 0

        print(f"  Era: {label} (n={total_n:,})")
        print(f"  {'Month':>6s}  {'Mean':>7s}  {'Anomaly':>8s}  {'Signal'}")
        print("  " + "-" * 45)

        for g in groups:
            month_idx = int(g["group_key"]) - 1
            name = MONTH_NAMES[month_idx] if 0 <= month_idx < 12 else g["group_key"]
            anomaly = g["mean_km_day"] - era_mean
            arrow = "+" if anomaly > 0 else ""
            bar_len = int(abs(anomaly) / 3)
            if anomaly > 0:
                bar = "|" + "#" * bar_len
            else:
                bar = " " * (10 - bar_len) + "." * bar_len + "|"
            print(f"  {name:>6s}  {g['mean_km_day']:>7.1f}  {arrow}{anomaly:>7.1f}  {bar}")

        print()
        print(f"  Mean: {era_mean:.1f} km/day")
        print(
            f"  Peak: {peak_month} ({peak['mean_km_day']:.1f}), "
            f"Trough: {trough_month} ({trough['mean_km_day']:.1f})"
        )
        print(f"  Seasonal amplitude: {amplitude:.1f} km/day ({pct_amp:.0f}%)")
        print()

    # Compare amplitudes
    amplitudes = []
    for label, result in era_results:
        groups = result["groups"]
        if groups:
            peak_speed = max(g["mean_km_day"] for g in groups)
            trough_speed = min(g["mean_km_day"] for g in groups)
            amplitudes.append((label, peak_speed - trough_speed))

    if len(amplitudes) >= 2:
        print("  Amplitude comparison:")
        for label, amp in amplitudes:
            bar = "#" * int(amp / 3)
            print(f"    {label}: {amp:.1f} km/day  {bar}")
        print()
        change = amplitudes[-1][1] - amplitudes[0][1]
        if abs(change) > 5:
            if change > 0:
                print("  Seasonal amplitude INCREASED, suggesting the jet")
                print("  stream strengthened more in winter than in summer.")
            else:
                print("  Seasonal amplitude DECREASED, suggesting more")
                print("  uniform strengthening across seasons.")
        else:
            print("  Seasonal amplitude remained roughly stable, suggesting")
            print("  the westerlies strengthened uniformly across seasons.")


async def section_spatial(runner: ToolRunner) -> None:
    """Section 4: Spatial variation — western vs eastern sectors."""
    print("\n" + "=" * 72)
    print("4. SPATIAL VARIATION: Western vs Eastern Indian Ocean")
    print("=" * 72)
    print()
    print("  The Roaring Forties span 95 degrees of longitude between")
    print("  the Cape of Good Hope (15 E) and Sunda Strait (110 E).")
    print("  We split this into two sectors to test whether westerly")
    print("  intensification was geographically uniform:")
    print()
    print("  Western sector: 15-55 E (Cape -> South of Madagascar)")
    print("  Eastern sector: 55-110 E (Madagascar -> Sunda Strait)")
    print()

    sectors = [
        ("Western (15-55 E)", 15, 55),
        ("Eastern (55-110 E)", 55, 110),
    ]

    sector_data = []
    for label, lon_min, lon_max in sectors:
        result = await runner.run(
            "maritime_aggregate_track_speeds",
            group_by="decade",
            lat_min=RF_LAT_MIN,
            lat_max=RF_LAT_MAX,
            lon_min=lon_min,
            lon_max=lon_max,
        )
        sector_data.append((label, result))

    for label, result in sector_data:
        groups = result["groups"]
        if not groups:
            print(f"  {label}: No data")
            continue

        total_n = sum(g["n"] for g in groups)
        overall_mean = sum(g["mean_km_day"] * g["n"] for g in groups) / total_n if total_n else 0

        print(f"  {label} (n={total_n:,}, mean={overall_mean:.1f} km/day)")
        print(f"  {'Decade':<10s}  {'N':>6s}  {'Mean':>7s}  {'Anomaly':>9s}  {'Trend'}")
        print("  " + "-" * 50)

        for g in groups:
            anomaly = g["mean_km_day"] - overall_mean
            arrow = "+" if anomaly > 0 else ""
            bar_len = int(abs(anomaly) / 5)
            bar = ("+" * bar_len) if anomaly > 0 else ("-" * bar_len)
            print(
                f"  {g['group_key'] + 's':<10s}  {g['n']:>6,}  "
                f"{g['mean_km_day']:>7.1f}  {arrow}{anomaly:>7.1f}  {bar}"
            )
        print()

    # Compare trends
    if len(sector_data) == 2 and all(d[1]["groups"] for d in sector_data):
        print("  Sector comparison:")
        for label, result in sector_data:
            groups = result["groups"]
            early = [g for g in groups if int(g["group_key"]) <= 1760]
            late = [g for g in groups if int(g["group_key"]) >= 1830]
            if early and late:
                early_mean = sum(g["mean_km_day"] * g["n"] for g in early) / sum(
                    g["n"] for g in early
                )
                late_mean = sum(g["mean_km_day"] * g["n"] for g in late) / sum(g["n"] for g in late)
                pct = ((late_mean - early_mean) / early_mean) * 100
                print(f"    {label}: {early_mean:.1f} -> {late_mean:.1f} km/day ({pct:+.1f}%)")
        print()
        print("  If both sectors show similar percentage increases, the")
        print("  westerly intensification was geographically uniform. If")
        print("  one sector changed more, it suggests spatial structure")
        print("  in the wind field evolution.")


async def section_laki_seasonal(runner: ToolRunner) -> None:
    """Section 5: Seasonal decomposition of the Laki signal."""
    print("\n" + "=" * 72)
    print("5. SEASONAL LAKI SIGNAL: Austral Winter vs Summer")
    print("=" * 72)
    print()
    print("  If the Laki eruption weakened Southern Hemisphere westerlies,")
    print("  the effect should be stronger in austral winter (Jun-Aug) when")
    print("  the jet stream is strongest and most sensitive to hemispheric")
    print("  temperature gradients.")
    print()
    print("  Using month_start/month_end seasonal filters to isolate the")
    print("  signal by season — the most diagnostic test for volcanic")
    print("  aerosol forcing on the westerlies.")

    seasons = [
        ("Austral winter (Jun-Aug)", 6, 8),
        ("Austral summer (Dec-Feb)", 12, 2),
    ]

    for label, m_start, m_end in seasons:
        print()
        print(f"  --- {label} ---")
        print(f"  [maritime_compare_speed_groups: pre vs post Laki, months {m_start}-{m_end}]")

        result = await runner.run(
            "maritime_compare_speed_groups",
            group1_years="1778/1782",
            group2_years="1783/1786",
            lat_min=RF_LAT_MIN,
            lat_max=RF_LAT_MAX,
            lon_min=RF_LON_MIN,
            lon_max=RF_LON_MAX,
            direction="eastbound",
            month_start=m_start,
            month_end=m_end,
        )

        n1, n2 = result["group1_n"], result["group2_n"]
        if n1 == 0 or n2 == 0:
            print(f"  Insufficient data: pre={n1}, post={n2}")
            continue

        diff = result["group2_mean"] - result["group1_mean"]
        pct = (diff / result["group1_mean"] * 100) if result["group1_mean"] else 0
        p_str = f"{result['p_value']:.6f}" if result["p_value"] > 0 else "< 1e-300"
        sig = "SIGNIFICANT" if result["significant"] else "not significant"

        print(f"  Pre-Laki:  n={n1:>5,}, mean={result['group1_mean']:.1f} km/day")
        print(f"  Post-Laki: n={n2:>5,}, mean={result['group2_mean']:.1f} km/day")
        print(f"  Difference: {diff:+.1f} km/day ({pct:+.1f}%)")
        print(f"  Mann-Whitney z={result['z_score']:.4f}, p={p_str} ({sig})")
        print(f"  Cohen's d = {result['effect_size']:.3f}")

    print()
    print("  Interpretation: If the winter signal is stronger than summer,")
    print("  that confirms volcanic aerosol forcing acting through the")
    print("  meridional temperature gradient → jet stream pathway.")
    print("  Equal signals would suggest a more uniform atmospheric effect.")


async def section_did_test(runner: ToolRunner) -> None:
    """Section 6: Formal Difference-in-Differences test."""
    print("\n" + "=" * 72)
    print("6. FORMAL DiD TEST: Direction x Period Interaction")
    print("=" * 72)
    print()
    print("  Difference-in-Differences isolates wind changes from technology:")
    print("  DiD = (post_east - pre_east) - (post_west - pre_west)")
    print()
    print("  A significant positive DiD means eastbound gained more than")
    print("  westbound — proof of strengthened westerlies, not just better ships.")
    print()
    print("  Using voyage-level aggregation for statistically independent")
    print("  samples (daily observations within a voyage are autocorrelated).")

    result = await runner.run(
        "maritime_did_speed_test",
        period1_years="1750/1783",
        period2_years="1784/1810",
        lat_min=RF_LAT_MIN,
        lat_max=RF_LAT_MAX,
        lon_min=RF_LON_MIN,
        lon_max=RF_LON_MAX,
        aggregate_by="voyage",
    )

    print()
    print("  2x2 Cell Summary (voyage-level means):")
    print(
        f"    Pre-Laki  eastbound: n={result['period1_eastbound_n']:>4}, "
        f"mean={result['period1_eastbound_mean']:.1f} km/day"
    )
    print(
        f"    Pre-Laki  westbound: n={result['period1_westbound_n']:>4}, "
        f"mean={result['period1_westbound_mean']:.1f} km/day"
    )
    print(
        f"    Post-Laki eastbound: n={result['period2_eastbound_n']:>4}, "
        f"mean={result['period2_eastbound_mean']:.1f} km/day"
    )
    print(
        f"    Post-Laki westbound: n={result['period2_westbound_n']:>4}, "
        f"mean={result['period2_westbound_mean']:.1f} km/day"
    )
    print()
    print(f"  Eastbound diff:  {result['eastbound_diff']:+.1f} km/day")
    print(f"  Westbound diff:  {result['westbound_diff']:+.1f} km/day")
    print()
    sig = "SIGNIFICANT" if result["significant"] else "not significant"
    p_str = f"{result['did_p_value']:.6f}" if result["did_p_value"] > 0.0001 else "< 0.0001"
    print(f"  DiD estimate: {result['did_estimate']:+.1f} km/day")
    print(f"  95% CI: [{result['did_ci_lower']:.1f}, {result['did_ci_upper']:.1f}]")
    print(f"  p = {p_str} ({sig} at p<0.05)")
    print(f"  Bootstrap iterations: {result['n_bootstrap']}")

    print()
    print("  Interpretation: If the DiD is significantly positive, then")
    print("  eastbound speeds (running before the westerlies) gained more")
    print("  than westbound speeds — conclusive evidence that the wind")
    print("  itself strengthened, not just shipbuilding technology.")


async def main() -> None:
    runner = ToolRunner()

    print("=" * 72)
    print("VOLCANIC SIGNALS & WIND PATTERNS")
    print("Novel Research Analyses from CLIWOC Ship Speed Data (1662-1855)")
    print("=" * 72)
    print()
    print("  Six independent analyses probing the Roaring Forties")
    print("  ship speed record for climate signals invisible in any")
    print("  other historical archive.")
    print()
    print("  All analysis uses live MCP tool calls against ~261K daily")
    print("  logbook positions from CLIWOC 2.1 Full.")

    await section_laki(runner)
    await section_ew_ratio(runner)
    await section_seasonal_amplitude(runner)
    await section_spatial(runner)
    await section_laki_seasonal(runner)
    await section_did_test(runner)

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print()
    print("  1. LAKI 1783: The volcanic eruption's atmospheric effects")
    print("     should appear as a transient speed dip in 1783-1785,")
    print("     testing whether ship logs can detect single volcanic")
    print("     events — a question never before addressed with this data.")
    print()
    print("  2. E/W RATIO: The eastbound/westbound speed ratio is the")
    print("     cleanest test for wind vs technology. If the ratio")
    print("     increases over time, the wind got stronger. If it stays")
    print("     constant, technology improved equally in both directions.")
    print()
    print("  3. SEASONAL AMPLITUDE: How the winter/summer speed swing")
    print("     evolved reveals whether the Southern Hemisphere jet")
    print("     stream strengthened uniformly or preferentially in one")
    print("     season — a finding with implications for understanding")
    print("     modern jet stream behaviour under climate change.")
    print()
    print("  4. SPATIAL VARIATION: Whether the western and eastern")
    print("     Indian Ocean sectors show equal intensification tests")
    print("     for spatial structure in the westerly wind field — do")
    print("     winds strengthen everywhere equally, or are there")
    print("     preferred zones of change?")
    print()
    print("  5. SEASONAL LAKI: Austral winter (Jun-Aug) vs summer (Dec-Feb)")
    print("     decomposition tests whether the Laki signal acts through")
    print("     the expected jet-stream pathway — stronger in winter when")
    print("     the meridional temperature gradient matters most.")
    print()
    print("  6. FORMAL DiD: The Difference-in-Differences test with voyage-")
    print("     level aggregation provides the methodologically correct")
    print("     interaction test — are eastbound gains significantly larger")
    print("     than westbound gains? With bootstrap CI and proper p-values.")
    print()
    print("  Each of these analyses could be a standalone research paper.")
    print("  Together they demonstrate that maritime logbook data — ")
    print("  mundane administrative records from 200 years ago — contain")
    print("  extractable climate signals at annual, decadal, and spatial")
    print("  resolutions previously thought impossible.")
    print()
    print("  Data source: CLIWOC 2.1 Full -- ~261K daily positions, 1662-1855")
    print("  Tools: chuk-mcp-maritime-archives MCP server")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
