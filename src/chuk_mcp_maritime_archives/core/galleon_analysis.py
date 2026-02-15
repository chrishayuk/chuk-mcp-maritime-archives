"""
Manila Galleon transit time analysis for climate signal detection.

Loads galleon voyage records and computes transit times (departure→arrival)
for ENSO phase classification and other climate analyses. The Manila
Galleon trade (1565-1815) provides 250 years of Pacific crossings directly
through the ENSO-affected trade wind belt.
"""

from __future__ import annotations

import json
import logging
import statistics
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

_GALLEON_VOYAGES: list[dict[str, Any]] = []


def _load_galleon(data_dir: Path | None = None) -> None:
    """Load galleon voyage data from JSON file."""
    global _GALLEON_VOYAGES
    if _GALLEON_VOYAGES:
        return

    path = (data_dir or _DEFAULT_DATA_DIR) / "galleon_voyages.json"
    if not path.exists():
        logger.warning("Galleon data file not found: %s", path)
        return

    with open(path) as f:
        _GALLEON_VOYAGES = json.load(f)
    logger.info("Loaded %d galleon voyages from %s", len(_GALLEON_VOYAGES), path)


def _parse_date(d: str | None) -> date | None:
    """Parse a YYYY-MM-DD string to a date object."""
    if not d:
        return None
    try:
        parts = d.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def galleon_transit_times(
    trade_direction: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    fate: str | None = None,
    max_results: int = 500,
) -> dict[str, Any]:
    """Compute transit times for Manila Galleon voyages.

    Transit time = arrival_date - departure_date (in days).

    Args:
        trade_direction: Filter by "eastbound" (Acapulco→Manila) or
            "westbound" (Manila→Acapulco)
        year_start: Earliest departure year (inclusive)
        year_end: Latest departure year (inclusive)
        fate: Filter by voyage fate ("completed", "wrecked", etc.)
        max_results: Maximum records to return

    Returns:
        Dict with transit records and summary statistics.
    """
    _load_galleon()

    records: list[dict[str, Any]] = []
    skipped_no_dates = 0

    for v in _GALLEON_VOYAGES:
        dep = _parse_date(v.get("departure_date"))
        arr = _parse_date(v.get("arrival_date"))

        if dep is None or arr is None:
            skipped_no_dates += 1
            continue

        transit_days = (arr - dep).days
        if transit_days <= 0:
            skipped_no_dates += 1
            continue

        # Apply filters
        if trade_direction and v.get("trade_direction") != trade_direction:
            continue
        if year_start and dep.year < year_start:
            continue
        if year_end and dep.year > year_end:
            continue
        if fate and v.get("fate") != fate:
            continue

        records.append(
            {
                "voyage_id": v["voyage_id"],
                "ship_name": v.get("ship_name"),
                "captain": v.get("captain"),
                "tonnage": v.get("tonnage"),
                "departure_date": v.get("departure_date"),
                "departure_port": v.get("departure_port"),
                "arrival_date": v.get("arrival_date"),
                "destination_port": v.get("destination_port"),
                "trade_direction": v.get("trade_direction"),
                "fate": v.get("fate"),
                "transit_days": transit_days,
                "year": dep.year,
            }
        )

    total = len(records)
    truncated = total > max_results
    records = records[:max_results]

    # Compute summary stats
    all_days = [r["transit_days"] for r in records]
    eb_days = [r["transit_days"] for r in records if r["trade_direction"] == "eastbound"]
    wb_days = [r["transit_days"] for r in records if r["trade_direction"] == "westbound"]

    def _stats(days: list[int]) -> dict[str, Any] | None:
        if not days:
            return None
        return {
            "n": len(days),
            "mean": round(statistics.mean(days), 1),
            "median": round(statistics.median(days), 1),
            "std": round(statistics.stdev(days), 1) if len(days) > 1 else 0.0,
            "min": min(days),
            "max": max(days),
        }

    return {
        "total_matching": total,
        "returned": len(records),
        "truncated": truncated,
        "skipped_no_dates": skipped_no_dates,
        "records": records,
        "summary": _stats(all_days),
        "eastbound_summary": _stats(eb_days),
        "westbound_summary": _stats(wb_days),
        "trade_direction_filter": trade_direction,
        "year_start_filter": year_start,
        "year_end_filter": year_end,
        "fate_filter": fate,
    }


# Load on import
_load_galleon()
