"""
CLIWOC ship track data — historical logbook positions (1662-1855).

Loads ~261K ship positions from ``data/cliwoc_tracks.json`` (produced by
``scripts/download_cliwoc.py``) and provides search/filter functions for
finding historical ship tracks by nationality, date range, and proximity.

Covers 8 nationalities: NL (Dutch), UK (British), ES (Spanish),
FR (French), SE (Swedish), US (American), DE (German), DK (Danish).

Data source: CLIWOC Slim and Routes (Figshare)
https://figshare.com/articles/dataset/CLIWOC_Slim_and_Routes/11941224
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Loaded from JSON
_TRACKS: list[dict[str, Any]] = []
_TRACK_INDEX: dict[int, dict[str, Any]] = {}  # voyage_id -> track
_METADATA: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_tracks(data_dir: Path | None = None) -> None:
    """Load CLIWOC track data from JSON file."""
    global _TRACKS, _TRACK_INDEX, _METADATA
    if _TRACKS:
        return

    path = (data_dir or _DEFAULT_DATA_DIR) / "cliwoc_tracks.json"
    if not path.exists():
        logger.warning("CLIWOC tracks not found: %s (run scripts/download_cliwoc.py)", path)
        return

    with open(path) as f:
        data = json.load(f)

    _TRACKS = data.get("tracks", [])
    _TRACK_INDEX = {t["voyage_id"]: t for t in _TRACKS}
    _METADATA = {k: v for k, v in data.items() if k != "tracks"}
    logger.info(
        "Loaded %d CLIWOC tracks (%d positions) from %s",
        len(_TRACKS),
        _METADATA.get("total_positions", 0),
        path.name,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def search_tracks(
    nationality: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """
    Search CLIWOC ship tracks by nationality and/or date range.

    Returns track summaries (without positions) for matching voyages.

    Args:
        nationality: Two-letter code (NL, UK, ES, FR, SE, US, DE, DK)
        year_start: Earliest year to include
        year_end: Latest year to include
        max_results: Maximum results to return (default: 50)
    """
    _load_tracks()
    results = []

    for track in _TRACKS:
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue
        # Return summary without positions
        results.append(_track_summary(track))
        if len(results) >= max_results:
            break

    return results


def get_track(voyage_id: int) -> dict[str, Any] | None:
    """
    Get full track detail including all positions for a CLIWOC voyage.

    Args:
        voyage_id: CLIWOC voyage ID (integer)

    Returns:
        Full track dict with positions, or None if not found.
    """
    _load_tracks()
    return _TRACK_INDEX.get(voyage_id)


def nearby_tracks(
    lat: float,
    lon: float,
    date: str,
    radius_km: float = 200.0,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """
    Find ships near a given position on a given date.

    Searches all CLIWOC positions for the specified date and returns
    tracks with positions within the given radius.

    Args:
        lat: Latitude of search point
        lon: Longitude of search point
        date: Date to search (YYYY-MM-DD)
        radius_km: Search radius in kilometres (default: 200)
        max_results: Maximum results (default: 20)

    Returns:
        List of dicts with track summary + distance_km + matching position.
    """
    _load_tracks()
    hits: list[dict[str, Any]] = []

    for track in _TRACKS:
        # Quick date range filter (normalize for consistent comparison)
        start = _normalize_date(track.get("start_date"))
        end = _normalize_date(track.get("end_date"))
        if start and end:
            if date < start or date > end:
                continue

        # Check each position for this date
        for pos in track.get("positions", []):
            if pos.get("date") != date:
                continue
            dist = _haversine_km(lat, lon, pos["lat"], pos["lon"])
            if dist <= radius_km:
                hits.append(
                    {
                        **_track_summary(track),
                        "distance_km": round(dist, 1),
                        "matching_position": {
                            "date": pos["date"],
                            "lat": pos["lat"],
                            "lon": pos["lon"],
                        },
                    }
                )
                break  # one hit per track

    # Sort by distance
    hits.sort(key=lambda h: h["distance_km"])
    return hits[:max_results]


def list_nationalities() -> dict[str, int]:
    """Return nationality codes with track counts."""
    _load_tracks()
    return dict(_METADATA.get("nationalities", {}))


def get_track_count() -> int:
    """Return total number of loaded tracks."""
    _load_tracks()
    return len(_TRACKS)


def get_position_count() -> int:
    """Return total number of loaded positions."""
    _load_tracks()
    return _METADATA.get("total_positions", 0)


def get_date_range() -> str:
    """Return date range string (e.g. '1662-1854')."""
    _load_tracks()
    return _METADATA.get("date_range", "unknown")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _track_summary(track: dict[str, Any]) -> dict[str, Any]:
    """Return a track dict without the positions list."""
    return {k: v for k, v in track.items() if k != "positions"}


def _normalize_date(d: str | None) -> str | None:
    """Normalize a date string to YYYY-MM-DD with zero-padding."""
    if not d:
        return d
    parts = d.split("-")
    if len(parts) == 3:
        return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    return d


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    R = 6371.0  # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Load on import
_load_tracks()
