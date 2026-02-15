#!/usr/bin/env python3
"""
ENSO Investigation Demo -- chuk-mcp-maritime-archives v0.21.3

Simulates the multi-region ENSO investigation that an LLM (e.g. GPT-5.2)
would run via MCP tool calls, demonstrating three v0.21.3 features that
prevent LLM context-window overflow:

    1. output_mode="csv"  -- 3-4x fewer tokens than JSON for tabular data
    2. fields="..."       -- return only needed columns
    3. exclude_years="..."-- define Neutral baselines server-side

This demo runs the full ENSO detection pipeline:
    - Region 1: Tropical Pacific trade-wind belt (primary signal)
    - Region 2: Indian Ocean monsoon (teleconnection)
    - Region 3: South Atlantic trades (independent confirmation)
    - Seasonal split: DJF (ENSO peak) vs JJA (control)
    - Neutral baseline: all years excluding known ENSO events
    - CSV export for cluster-bootstrap analysis

No network access required -- all data is local.

Usage:
    python examples/enso_investigation_demo.py
"""

from __future__ import annotations

from chuk_mcp_maritime_archives.core.cliwoc_tracks import (
    compare_speed_groups,
    did_speed_test,
    export_speeds,
    wind_rose,
)
from chuk_mcp_maritime_archives.models.responses import (
    SpeedExportResponse,
    SpeedSample,
    format_response,
)

# ── ENSO chronology (strong events, Gergis & Fowler 2009 + Quinn 1987) ──

EL_NINO_YEARS = "1720,1728,1747,1761,1775,1783,1791,1804,1814,1828,1845"
LA_NINA_YEARS = "1714,1722,1733,1750,1763,1776,1785,1793,1806,1816,1830"
ALL_ENSO_YEARS = f"{EL_NINO_YEARS},{LA_NINA_YEARS}"

# ── Region bounding boxes ──

REGIONS = {
    "Tropical Pacific": {"lat_min": -15, "lat_max": 20, "lon_min": 110, "lon_max": 290},
    "Indian Ocean": {"lat_min": -10, "lat_max": 20, "lon_min": 50, "lon_max": 100},
    "South Atlantic": {"lat_min": -30, "lat_max": 0, "lon_min": -40, "lon_max": 15},
}


def _print_comparison(label: str, result: dict) -> None:
    """Print a compact speed comparison result."""
    print(f"  {label}")
    print(f"    Period1: N={result['period1_n']:<4} mean={result['period1_mean']:.1f} km/day")
    print(f"    Period2: N={result['period2_n']:<4} mean={result['period2_mean']:.1f} km/day")
    print(
        f"    p={result['p_value']:.4f}  d={result['effect_size']:.3f}"
        f"  {'*** SIGNIFICANT' if result['significant'] else '(not significant)'}"
    )
    print()


def main() -> None:
    print("=" * 72)
    print("ENSO INVESTIGATION — Token-Efficient MCP Analysis (v0.21.3)")
    print("=" * 72)
    print()
    print("  Demonstrates CSV output, field selection, and exclude_years")
    print("  to keep LLM context usage low during multi-region ENSO analysis.")
    print()

    # =================================================================
    # 1. MULTI-REGION El Nino vs La Nina (DIRECT CONTRAST)
    # =================================================================
    print("=" * 72)
    print("1. El Nino vs La Nina — Multi-Region Speed Comparison (Eastbound)")
    print("=" * 72)
    print()

    for region_name, bbox in REGIONS.items():
        result = compare_speed_groups(
            period1_years=EL_NINO_YEARS,
            period2_years=LA_NINA_YEARS,
            direction="eastbound",
            aggregate_by="voyage",
            **bbox,
        )
        _print_comparison(f"{region_name} (eastbound):", result)

    # =================================================================
    # 2. NEUTRAL BASELINE using exclude_years (NEW in v0.21.3)
    # =================================================================
    print("=" * 72)
    print("2. El Nino vs NEUTRAL Baseline (using exclude_years)")
    print("=" * 72)
    print()
    print("  exclude_years removes from BOTH periods uniformly.")
    print("  To get El Nino vs Neutral: exclude only La Nina years,")
    print("  so period1 (El Nino list) loses nothing (no overlap),")
    print("  and period2 (full range) becomes all-years-minus-La-Nina.")
    print()

    for region_name, bbox in REGIONS.items():
        result = compare_speed_groups(
            period1_years=EL_NINO_YEARS,
            period2_years="1662/1855",
            direction="eastbound",
            aggregate_by="voyage",
            exclude_years=LA_NINA_YEARS,
            **bbox,
        )
        _print_comparison(f"{region_name} El Nino vs ~Neutral:", result)

    # =================================================================
    # 3. SEASONAL SPLIT — DJF vs JJA
    # =================================================================
    print("=" * 72)
    print("3. Seasonal ENSO Test — DJF (peak) vs JJA (control)")
    print("=" * 72)
    print()

    pacific = REGIONS["Tropical Pacific"]
    for season, m_start, m_end in [("DJF", 11, 2), ("JJA", 6, 8)]:
        result = compare_speed_groups(
            period1_years=EL_NINO_YEARS,
            period2_years=LA_NINA_YEARS,
            direction="eastbound",
            aggregate_by="voyage",
            month_start=m_start,
            month_end=m_end,
            **pacific,
        )
        _print_comparison(f"Tropical Pacific {season}:", result)

    # =================================================================
    # 4. DiD TEST with exclude_years
    # =================================================================
    print("=" * 72)
    print("4. DiD Speed Test — El Nino vs Neutral (direction x period)")
    print("=" * 72)
    print()

    did_result = did_speed_test(
        period1_years=EL_NINO_YEARS,
        period2_years="1662/1855",
        exclude_years=LA_NINA_YEARS,
        aggregate_by="voyage",
        n_bootstrap=2000,
        **pacific,
    )
    print(f"  DiD estimate: {did_result['did_estimate']:+.1f} km/day")
    print(f"  95% CI: [{did_result['did_ci_lower']:.1f}, {did_result['did_ci_upper']:.1f}]")
    print(f"  p-value: {did_result['did_p_value']:.4f}")
    print(f"  Significant: {did_result['significant']}")
    print()

    # =================================================================
    # 5. WIND ROSE — direction shift check
    # =================================================================
    print("=" * 72)
    print("5. Wind Rose — Direction Distribution (El Nino vs La Nina)")
    print("=" * 72)
    print()

    wr = wind_rose(
        period1_years=EL_NINO_YEARS,
        period2_years=LA_NINA_YEARS,
        **pacific,
    )
    if wr.get("has_direction_data"):
        print(f"  Total with direction: {wr['total_with_direction']:,}")
        print()
        print(f"  {'Sector':>6} {'Count':>8} {'%':>7}")
        print(f"  {'-' * 6} {'-' * 8} {'-' * 7}")
        for dc in wr["direction_counts"]:
            if dc["count"] > 0:
                print(f"  {dc['sector']:>6} {dc['count']:>8} {dc['percent']:>6.1f}%")
    else:
        print("  No wind direction data available.")
    print()

    # =================================================================
    # 6. CSV EXPORT — compact data for offline analysis
    # =================================================================
    print("=" * 72)
    print("6. CSV Export — Token-Efficient Data Export")
    print("=" * 72)
    print()

    result = export_speeds(
        direction="eastbound",
        aggregate_by="observation",
        month_start=11,
        month_end=2,
        max_results=20,
        **pacific,
    )
    samples = [
        SpeedSample(**{k: v for k, v in s.items() if v is not None}) for s in result["samples"]
    ]
    resp = SpeedExportResponse(
        total_matching=result["total_matching"],
        returned=result["returned"],
        offset=result.get("offset", 0),
        has_more=result.get("has_more", False),
        next_offset=result.get("next_offset"),
        aggregate_by=result["aggregate_by"],
        samples=samples,
    )

    # Full JSON (verbose)
    json_out = format_response(resp, output_mode="json")
    json_tokens = len(json_out.split())
    print(f"  a) JSON output: ~{json_tokens} tokens ({len(json_out):,} chars)")

    # CSV (compact)
    csv_out = format_response(resp, output_mode="csv")
    csv_tokens = len(csv_out.split())
    print(f"  b) CSV output:  ~{csv_tokens} tokens ({len(csv_out):,} chars)")

    # CSV with field selection (minimal)
    csv_minimal = format_response(
        resp,
        output_mode="csv",
        fields=["voyage_id", "year", "speed_km_day"],
    )
    csv_min_tokens = len(csv_minimal.split())
    print(f"  c) CSV + fields: ~{csv_min_tokens} tokens ({len(csv_minimal):,} chars)")

    if json_tokens > 0:
        print(
            f"\n  Compression ratio: CSV={json_tokens / max(csv_tokens, 1):.1f}x, "
            f"CSV+fields={json_tokens / max(csv_min_tokens, 1):.1f}x fewer tokens"
        )

    print()
    print("  Sample CSV output (first 5 lines):")
    for line in csv_minimal.strip().split("\n")[:5]:
        print(f"    {line}")
    print()

    # =================================================================
    # Summary
    # =================================================================
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print()
    print("  v0.21.3 token-efficiency features:")
    print("    - output_mode='csv': ~3-4x fewer tokens than JSON")
    print("    - fields='...': select only needed columns (~5-10x reduction)")
    print("    - exclude_years='...': remove years from both periods uniformly")


if __name__ == "__main__":
    main()
