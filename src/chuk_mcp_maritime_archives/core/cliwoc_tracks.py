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
import random
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Loaded from JSON
_TRACKS: list[dict[str, Any]] = []
_TRACK_INDEX: dict[int, dict[str, Any]] = {}  # voyage_id -> track
_DAS_INDEX: dict[str, dict[str, Any]] = {}  # das_number -> track
_SHIP_NAME_INDEX: dict[str, list[dict[str, Any]]] = {}  # upper(ship_name) -> [tracks]
_METADATA: dict[str, Any] = {}
_FUZZY_INDEX: Any = None  # ShipNameIndex, built lazily


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_tracks(data_dir: Path | None = None) -> None:
    """Load CLIWOC track data from JSON file."""
    global _TRACKS, _TRACK_INDEX, _DAS_INDEX, _SHIP_NAME_INDEX, _METADATA
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

    # Build optional indexes (only populated when CLIWOC 2.1 Full data is present)
    for t in _TRACKS:
        das_num = t.get("das_number")
        if das_num:
            _DAS_INDEX[str(das_num)] = t
        ship = t.get("ship_name")
        if ship:
            key = ship.upper()
            if key not in _SHIP_NAME_INDEX:
                _SHIP_NAME_INDEX[key] = []
            _SHIP_NAME_INDEX[key].append(t)

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
    ship_name: str | None = None,
    max_results: int = 50,
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
) -> list[dict[str, Any]]:
    """
    Search CLIWOC ship tracks by nationality, date range, ship name, and/or region.

    Returns track summaries (without positions) for matching voyages.

    Args:
        nationality: Two-letter code (NL, UK, ES, FR, SE, US, DE, DK)
        year_start: Earliest year to include
        year_end: Latest year to include
        ship_name: Ship name or partial name (case-insensitive; requires CLIWOC 2.1 Full data)
        max_results: Maximum results to return (default: 50)
        lat_min: Minimum latitude (track must have at least one position in bbox)
        lat_max: Maximum latitude
        lon_min: Minimum longitude
        lon_max: Maximum longitude
    """
    _load_tracks()
    has_bbox = any(v is not None for v in (lat_min, lat_max, lon_min, lon_max))
    results = []

    for track in _TRACKS:
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue
        if ship_name:
            track_ship = track.get("ship_name", "")
            if not track_ship or ship_name.upper() not in track_ship.upper():
                continue
        if has_bbox and not _track_in_bbox(track, lat_min, lat_max, lon_min, lon_max):
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
# Cross-archive linking
# ---------------------------------------------------------------------------


def get_track_by_das_number(das_number: str) -> dict[str, Any] | None:
    """
    Find CLIWOC track linked to a DAS voyage by DASnumber.

    Only available when CLIWOC 2.1 Full data has been downloaded (the Slim
    dataset does not include DASnumber). Returns full track with positions.
    """
    _load_tracks()
    return _DAS_INDEX.get(str(das_number))


def find_track_for_voyage(
    ship_name: str,
    departure_date: str | None = None,
    nationality: str = "NL",
    min_confidence: float = 0.50,
) -> tuple[dict[str, Any] | None, float]:
    """
    Find a CLIWOC track matching a voyage by ship name and date overlap.

    Uses fuzzy matching via entity resolution (Levenshtein + Soundex + date
    proximity scoring). Returns ``(track_summary, confidence)`` where
    confidence is 0.0-1.0.

    Args:
        ship_name: Ship name from voyage record
        departure_date: Departure date (YYYY-MM-DD) for date proximity scoring
        nationality: Expected nationality (default NL for DAS voyages)
        min_confidence: Minimum confidence threshold (default 0.50)

    Returns:
        Tuple of (track_summary_dict_or_None, confidence_float).
    """
    global _FUZZY_INDEX

    _load_tracks()
    if not ship_name:
        return None, 0.0

    if not _TRACKS:
        return None, 0.0

    # Build fuzzy index lazily on first use
    if _FUZZY_INDEX is None:
        from .entity_resolution import ShipNameIndex

        _FUZZY_INDEX = ShipNameIndex(
            records=_TRACKS,
            name_field="ship_name",
            id_field="voyage_id",
        )

    matches = _FUZZY_INDEX.find_matches(
        query_name=ship_name,
        query_date=departure_date,
        query_nationality=nationality,
        min_confidence=min_confidence,
        max_results=5,
    )

    if not matches:
        return None, 0.0

    # Return the best match
    best = matches[0]
    cid = best.candidate_id
    try:
        track = _TRACK_INDEX.get(int(cid)) if str(cid).isdigit() else None
    except (ValueError, TypeError):
        track = None
    if track:
        return _track_summary(track), best.confidence

    return None, 0.0


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


def _track_in_bbox(
    track: dict[str, Any],
    lat_min: float | None,
    lat_max: float | None,
    lon_min: float | None,
    lon_max: float | None,
) -> bool:
    """Check if any position in a track falls within a bounding box."""
    for pos in track.get("positions", []):
        lat, lon = pos.get("lat"), pos.get("lon")
        if lat is None or lon is None:
            continue
        if lat_min is not None and lat < lat_min:
            continue
        if lat_max is not None and lat > lat_max:
            continue
        if lon_min is not None and lon < lon_min:
            continue
        if lon_max is not None and lon > lon_max:
            continue
        return True
    return False


def _pos_in_bbox(
    lat: float,
    lon: float,
    lat_min: float | None,
    lat_max: float | None,
    lon_min: float | None,
    lon_max: float | None,
) -> bool:
    """Check if a single position falls within a bounding box."""
    if lat_min is not None and lat < lat_min:
        return False
    if lat_max is not None and lat > lat_max:
        return False
    if lon_min is not None and lon < lon_min:
        return False
    if lon_max is not None and lon > lon_max:
        return False
    return True


def _infer_direction(lon1: float, lon2: float) -> str:
    """Infer sailing direction from longitude change, handling 180° wrap."""
    dlon = lon2 - lon1
    # Handle antimeridian wrap
    if dlon > 180:
        dlon -= 360
    elif dlon < -180:
        dlon += 360
    return "eastbound" if dlon >= 0 else "westbound"


def _month_in_range(month: int, start: int | None, end: int | None) -> bool:
    """Check if month is within [start, end], handling wrap-around (e.g., 11→2)."""
    if start is None and end is None:
        return True
    s = start if start is not None else 1
    e = end if end is not None else 12
    if s <= e:
        return s <= month <= e
    return month >= s or month <= e


def _parse_period(period_str: str) -> frozenset[int]:
    """Parse a period string into a set of years.

    Accepts two formats:
        "YYYY/YYYY" — contiguous range (inclusive)
        "YYYY,YYYY,YYYY,..." — explicit year list
    """
    if "/" in period_str:
        parts = period_str.split("/")
        return frozenset(range(int(parts[0]), int(parts[1]) + 1))
    return frozenset(int(y.strip()) for y in period_str.split(","))


_COMPASS_SECTORS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def _wind_dir_to_sector(degrees: int | float) -> str | None:
    """Convert wind direction in degrees (1-360) to 8-point compass sector."""
    if degrees is None or degrees < 0 or degrees > 360:
        return None
    return _COMPASS_SECTORS[int(((degrees + 22.5) % 360) / 45)]


def _parse_date(d: str) -> date | None:
    """Parse a YYYY-MM-DD string to a date object."""
    try:
        parts = d.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def _compute_daily_speeds(
    track: dict[str, Any],
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    exclude_anchored: bool = True,
) -> list[dict[str, Any]]:
    """Compute daily speeds from consecutive positions in a track.

    Returns list of dicts with: date, lat, lon, km_day, direction.
    Filters by bounding box, speed bounds, and anchored status.
    """
    positions = track.get("positions", [])
    if len(positions) < 2:
        return []

    has_bbox = any(v is not None for v in (lat_min, lat_max, lon_min, lon_max))
    speeds: list[dict[str, Any]] = []

    for i in range(1, len(positions)):
        p1, p2 = positions[i - 1], positions[i]

        # Skip anchored positions (ship not sailing)
        if exclude_anchored and (p1.get("anch") == 1 or p2.get("anch") == 1):
            continue

        lat1, lon1 = p1.get("lat"), p1.get("lon")
        lat2, lon2 = p2.get("lat"), p2.get("lon")
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            continue

        # Use midpoint for position filtering
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        if has_bbox and not _pos_in_bbox(mid_lat, mid_lon, lat_min, lat_max, lon_min, lon_max):
            continue

        d1 = _parse_date(p1.get("date", ""))
        d2 = _parse_date(p2.get("date", ""))
        if d1 is None or d2 is None:
            continue

        days = (d2 - d1).days
        if days <= 0:
            continue

        dist = _haversine_km(lat1, lon1, lat2, lon2)
        km_day = dist / days

        if km_day < min_speed or km_day > max_speed:
            continue

        speeds.append(
            {
                "date": p2.get("date", ""),
                "lat": round(mid_lat, 2),
                "lon": round(mid_lon, 2),
                "km_day": round(km_day, 1),
                "direction": _infer_direction(lon1, lon2),
                "wind_force": p2.get("wf"),
                "wind_direction": p2.get("wd"),
                "logged_dist": p2.get("dist"),
            }
        )

    return speeds


def _group_key(obs: dict[str, Any], group_by: str, track: dict[str, Any]) -> str | None:
    """Compute a group key for an observation."""
    if group_by == "decade":
        d = _parse_date(obs["date"])
        if d is None:
            return None
        return str((d.year // 10) * 10)
    if group_by == "year":
        d = _parse_date(obs["date"])
        if d is None:
            return None
        return str(d.year)
    if group_by == "month":
        d = _parse_date(obs["date"])
        if d is None:
            return None
        return str(d.month)
    if group_by == "direction":
        return obs.get("direction")
    if group_by == "nationality":
        return track.get("nationality")
    if group_by == "beaufort":
        wf = obs.get("wind_force")
        return str(wf) if wf is not None else None
    return None


def _compute_group_stats(values: list[float]) -> dict[str, Any]:
    """Compute descriptive statistics for a list of speed values."""
    n = len(values)
    if n == 0:
        return {"n": 0, "mean_km_day": 0, "median_km_day": 0, "std_km_day": 0}

    mean = statistics.mean(values)
    med = statistics.median(values)
    std = statistics.stdev(values) if n > 1 else 0.0
    sorted_vals = sorted(values)

    # 95% confidence interval for the mean
    se = std / math.sqrt(n) if n > 0 else 0.0
    ci_lower = mean - 1.96 * se
    ci_upper = mean + 1.96 * se

    # Percentiles
    p25_idx = max(0, int(n * 0.25) - 1)
    p75_idx = min(n - 1, int(n * 0.75))

    return {
        "n": n,
        "mean_km_day": round(mean, 1),
        "median_km_day": round(med, 1),
        "std_km_day": round(std, 1),
        "ci_lower": round(ci_lower, 1),
        "ci_upper": round(ci_upper, 1),
        "p25_km_day": round(sorted_vals[p25_idx], 1),
        "p75_km_day": round(sorted_vals[p75_idx], 1),
    }


# ---------------------------------------------------------------------------
# Track Analytics — Public API
# ---------------------------------------------------------------------------


def compute_track_speeds(
    voyage_id: int,
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
) -> dict[str, Any] | None:
    """Compute daily sailing speeds for a single voyage.

    Returns dict with voyage metadata and list of daily speed observations,
    or None if voyage not found.
    """
    _load_tracks()
    track = _TRACK_INDEX.get(voyage_id)
    if track is None:
        return None

    speeds = _compute_daily_speeds(track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed)
    km_values = [s["km_day"] for s in speeds]
    mean_speed = statistics.mean(km_values) if km_values else 0.0

    return {
        "voyage_id": voyage_id,
        "ship_name": track.get("ship_name"),
        "nationality": track.get("nationality"),
        "observation_count": len(speeds),
        "mean_km_day": round(mean_speed, 1),
        "speeds": speeds,
    }


def aggregate_track_speeds(
    group_by: str = "decade",
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    direction: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    aggregate_by: str = "observation",
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    wind_force_min: int | None = None,
    wind_force_max: int | None = None,
) -> dict[str, Any]:
    """Aggregate daily sailing speeds across all matching tracks by dimension.

    Args:
        group_by: Grouping dimension — "decade", "month", "direction",
            "nationality", "beaufort"
        lat_min/lat_max/lon_min/lon_max: Bounding box for position filtering
        nationality: Filter tracks by nationality code
        year_start/year_end: Filter tracks by year range
        direction: Filter observations by "eastbound" or "westbound"
        month_start/month_end: Filter by month (1-12), supports wrap-around (11-2 = Nov-Feb)
        aggregate_by: Unit of analysis — "observation" (each daily speed) or
            "voyage" (one mean speed per voyage, statistically independent)
        min_speed/max_speed: Speed bounds in km/day
        wind_force_min/wind_force_max: Beaufort force bounds (0-12).
            Requires wind data in positions (re-run download script).

    Returns:
        Dict with total_observations, total_voyages, groups list, methodology.
    """
    _load_tracks()
    voyage_level = aggregate_by == "voyage"
    groups: dict[str, list[float]] = defaultdict(list)
    # For voyage-level: collect per (voyage_id, group_key), then reduce
    voyage_groups: dict[tuple[int, str], list[float]] = defaultdict(list)
    voyage_ids: set[int] = set()
    total_obs = 0

    for track in _TRACKS:
        # Apply track-level filters
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue

        speeds = _compute_daily_speeds(
            track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed
        )
        if not speeds:
            continue

        vid = track["voyage_id"]
        for obs in speeds:
            # Apply direction filter
            if direction and obs.get("direction") != direction:
                continue

            # Apply month filter
            if month_start is not None or month_end is not None:
                d = _parse_date(obs["date"])
                if d is None or not _month_in_range(d.month, month_start, month_end):
                    continue

            # Apply wind force filter
            if wind_force_min is not None or wind_force_max is not None:
                wf = obs.get("wind_force")
                if wf is None:
                    continue
                if wind_force_min is not None and wf < wind_force_min:
                    continue
                if wind_force_max is not None and wf > wind_force_max:
                    continue

            key = _group_key(obs, group_by, track)
            if key is None:
                continue

            if voyage_level:
                voyage_groups[(vid, key)].append(obs["km_day"])
            else:
                groups[key].append(obs["km_day"])
            voyage_ids.add(vid)
            total_obs += 1

    # Reduce voyage-level groups to one mean per voyage per group
    if voyage_level:
        for (vid, key), speeds_list in voyage_groups.items():
            groups[key].append(statistics.mean(speeds_list))
        total_obs = sum(len(v) for v in groups.values())

    # Compute stats per group
    group_results = []
    for key in sorted(groups.keys(), key=lambda k: (k.isdigit(), int(k) if k.isdigit() else 0, k)):
        stats = _compute_group_stats(groups[key])
        stats["group_key"] = key
        group_results.append(stats)

    return {
        "total_observations": total_obs,
        "total_voyages": len(voyage_ids),
        "group_by": group_by,
        "aggregate_by": aggregate_by,
        "groups": group_results,
        "latitude_band": [lat_min, lat_max] if lat_min is not None or lat_max is not None else None,
        "longitude_band": [lon_min, lon_max]
        if lon_min is not None or lon_max is not None
        else None,
        "direction_filter": direction,
        "nationality_filter": nationality,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
        "wind_force_min_filter": wind_force_min,
        "wind_force_max_filter": wind_force_max,
    }


def compare_speed_groups(
    period1_years: str,
    period2_years: str,
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    direction: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    aggregate_by: str = "observation",
    include_samples: bool = False,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    wind_force_min: int | None = None,
    wind_force_max: int | None = None,
    exclude_years: str | None = None,
) -> dict[str, Any]:
    """Compare speed distributions between two time periods using Mann-Whitney U.

    Args:
        period1_years: Period as "YYYY/YYYY" range or "YYYY,YYYY,..." list
        period2_years: Period as "YYYY/YYYY" range or "YYYY,YYYY,..." list
        month_start/month_end: Filter by month (1-12), supports wrap-around
        aggregate_by: "observation" (each daily speed) or "voyage" (one mean
            per voyage, statistically independent samples)
        include_samples: If True, include raw speed arrays in response
        wind_force_min/wind_force_max: Beaufort force bounds (0-12)
        exclude_years: Years to exclude from both periods, as "YYYY/YYYY"
            range or "YYYY,YYYY,..." list.
        Other args: same as aggregate_track_speeds

    Returns:
        Dict with group statistics, Mann-Whitney U, z-score, p-value, effect size.
    """
    _load_tracks()
    voyage_level = aggregate_by == "voyage"

    y1_set = _parse_period(period1_years)
    y2_set = _parse_period(period2_years)
    if exclude_years:
        excl = _parse_period(exclude_years)
        y1_set = y1_set - excl
        y2_set = y2_set - excl

    def _collect_speeds(years: frozenset[int]) -> list[float]:
        values: list[float] = []
        if not years:
            return values
        yr_min, yr_max = min(years), max(years)
        # For voyage-level: collect per-voyage, then reduce to means
        per_voyage: dict[int, list[float]] = defaultdict(list)
        for track in _TRACKS:
            if nationality and track.get("nationality") != nationality.upper():
                continue
            t_start = track.get("year_start") or 9999
            t_end = track.get("year_end") or 0
            if t_start > yr_max or t_end < yr_min:
                continue

            speeds = _compute_daily_speeds(
                track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed
            )
            for obs in speeds:
                if direction and obs.get("direction") != direction:
                    continue
                d = _parse_date(obs["date"])
                if d and d.year in years:
                    if month_start is not None or month_end is not None:
                        if not _month_in_range(d.month, month_start, month_end):
                            continue
                    if wind_force_min is not None or wind_force_max is not None:
                        wf = obs.get("wind_force")
                        if wf is None:
                            continue
                        if wind_force_min is not None and wf < wind_force_min:
                            continue
                        if wind_force_max is not None and wf > wind_force_max:
                            continue
                    if voyage_level:
                        per_voyage[track["voyage_id"]].append(obs["km_day"])
                    else:
                        values.append(obs["km_day"])
        if voyage_level:
            for voy_speeds in per_voyage.values():
                values.append(statistics.mean(voy_speeds))
        return values

    g1 = _collect_speeds(y1_set)
    g2 = _collect_speeds(y2_set)

    n1, n2 = len(g1), len(g2)
    g1_mean = statistics.mean(g1) if g1 else 0.0
    g2_mean = statistics.mean(g2) if g2 else 0.0
    g1_std = statistics.stdev(g1) if len(g1) > 1 else 0.0
    g2_std = statistics.stdev(g2) if len(g2) > 1 else 0.0

    # Mann-Whitney U test (large-sample normal approximation)
    u_stat, z_score, p_value = _mann_whitney_u(g1, g2)

    # Cohen's d effect size
    pooled_std = math.sqrt(((n1 - 1) * g1_std**2 + (n2 - 1) * g2_std**2) / max(n1 + n2 - 2, 1))
    cohens_d = (g2_mean - g1_mean) / pooled_std if pooled_std > 0 else 0.0

    result: dict[str, Any] = {
        "period1_label": period1_years,
        "period1_n": n1,
        "period1_mean": round(g1_mean, 1),
        "period1_std": round(g1_std, 1),
        "period2_label": period2_years,
        "period2_n": n2,
        "period2_mean": round(g2_mean, 1),
        "period2_std": round(g2_std, 1),
        "mann_whitney_u": round(u_stat, 1),
        "z_score": round(z_score, 4),
        "p_value": round(p_value, 6),
        "significant": p_value < 0.05,
        "effect_size": round(cohens_d, 3),
        "aggregate_by": aggregate_by,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
        "wind_force_min_filter": wind_force_min,
        "wind_force_max_filter": wind_force_max,
    }
    if include_samples:
        result["period1_samples"] = [round(v, 1) for v in g1]
        result["period2_samples"] = [round(v, 1) for v in g2]
    return result


def _bootstrap_did(
    pre_east: list[float],
    pre_west: list[float],
    post_east: list[float],
    post_west: list[float],
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> tuple[float, float, float, float]:
    """Bootstrap Difference-in-Differences with CI and p-value.

    Returns (did_estimate, ci_lower, ci_upper, p_value).
    """
    if not pre_east or not pre_west or not post_east or not post_west:
        return 0.0, 0.0, 0.0, 1.0

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs)

    did = (_mean(post_east) - _mean(pre_east)) - (_mean(post_west) - _mean(pre_west))

    rng = random.Random(seed)
    boot_dids: list[float] = []
    for _ in range(n_bootstrap):
        pe = rng.choices(pre_east, k=len(pre_east))
        pw = rng.choices(pre_west, k=len(pre_west))
        oe = rng.choices(post_east, k=len(post_east))
        ow = rng.choices(post_west, k=len(post_west))
        boot_did = (_mean(oe) - _mean(pe)) - (_mean(ow) - _mean(pw))
        boot_dids.append(boot_did)

    boot_dids.sort()
    ci_lower = boot_dids[max(0, int(0.025 * n_bootstrap) - 1)]
    ci_upper = boot_dids[min(n_bootstrap - 1, int(0.975 * n_bootstrap))]

    # Two-tailed p-value
    n_le_zero = sum(1 for d in boot_dids if d <= 0)
    n_ge_zero = sum(1 for d in boot_dids if d >= 0)
    p_value = 2 * min(n_le_zero, n_ge_zero) / n_bootstrap
    p_value = min(p_value, 1.0)
    if p_value == 0.0:
        p_value = 1.0 / n_bootstrap  # minimum reportable p

    return did, ci_lower, ci_upper, p_value


def did_speed_test(
    period1_years: str,
    period2_years: str,
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    aggregate_by: str = "voyage",
    n_bootstrap: int = 10000,
    seed: int = 42,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    wind_force_min: int | None = None,
    wind_force_max: int | None = None,
    exclude_years: str | None = None,
) -> dict[str, Any]:
    """Formal 2×2 Difference-in-Differences test: direction × period.

    Tests whether the difference between eastbound and westbound speeds changed
    significantly between two time periods. This isolates directional wind
    changes from symmetric technology improvements.

    DiD = (period2_east - period1_east) - (period2_west - period1_west)

    A significant positive DiD means eastbound speeds gained more than westbound,
    indicating strengthened westerlies (not just better ships).

    Args:
        period1_years: Period as "YYYY/YYYY" range or "YYYY,YYYY,..." list
        period2_years: Period as "YYYY/YYYY" range or "YYYY,YYYY,..." list
        lat_min/lat_max/lon_min/lon_max: Bounding box for position filtering
        nationality: Filter tracks by nationality code
        month_start/month_end: Filter by month (1-12), supports wrap-around
        aggregate_by: "voyage" (default, statistically independent) or
            "observation" (more data points but autocorrelated)
        n_bootstrap: Number of bootstrap iterations (default: 10000)
        seed: Random seed for reproducibility (default: 42)
        wind_force_min/wind_force_max: Beaufort force bounds (0-12)
        min_speed/max_speed: Speed bounds in km/day
        exclude_years: Years to exclude from both periods, as "YYYY/YYYY"
            range or "YYYY,YYYY,..." list.

    Returns:
        Dict with 4-cell summary, marginal diffs, DiD estimate,
        bootstrap CI, and p-value.
    """
    _load_tracks()
    voyage_level = aggregate_by == "voyage"

    y1_set = _parse_period(period1_years)
    y2_set = _parse_period(period2_years)
    if exclude_years:
        excl = _parse_period(exclude_years)
        y1_set = y1_set - excl
        y2_set = y2_set - excl

    def _collect_by_direction(years: frozenset[int]) -> tuple[list[float], list[float]]:
        """Collect speeds split by direction for a time period."""
        east_obs: list[float] = []
        west_obs: list[float] = []
        if not years:
            return east_obs, west_obs
        east_voy: dict[int, list[float]] = defaultdict(list)
        west_voy: dict[int, list[float]] = defaultdict(list)
        yr_min, yr_max = min(years), max(years)

        for track in _TRACKS:
            if nationality and track.get("nationality") != nationality.upper():
                continue
            t_start = track.get("year_start") or 9999
            t_end = track.get("year_end") or 0
            if t_start > yr_max or t_end < yr_min:
                continue

            speeds = _compute_daily_speeds(
                track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed
            )
            vid = track["voyage_id"]
            for obs in speeds:
                d = _parse_date(obs["date"])
                if not d or d.year not in years:
                    continue
                if month_start is not None or month_end is not None:
                    if not _month_in_range(d.month, month_start, month_end):
                        continue
                if wind_force_min is not None or wind_force_max is not None:
                    wf = obs.get("wind_force")
                    if wf is None:
                        continue
                    if wind_force_min is not None and wf < wind_force_min:
                        continue
                    if wind_force_max is not None and wf > wind_force_max:
                        continue
                direction = obs.get("direction", "")
                if direction == "eastbound":
                    if voyage_level:
                        east_voy[vid].append(obs["km_day"])
                    else:
                        east_obs.append(obs["km_day"])
                elif direction == "westbound":
                    if voyage_level:
                        west_voy[vid].append(obs["km_day"])
                    else:
                        west_obs.append(obs["km_day"])

        if voyage_level:
            for voy_speeds in east_voy.values():
                east_obs.append(statistics.mean(voy_speeds))
            for voy_speeds in west_voy.values():
                west_obs.append(statistics.mean(voy_speeds))
        return east_obs, west_obs

    pre_east, pre_west = _collect_by_direction(y1_set)
    post_east, post_west = _collect_by_direction(y2_set)

    def _safe_mean(xs: list[float]) -> float:
        return statistics.mean(xs) if xs else 0.0

    pe_mean = _safe_mean(pre_east)
    pw_mean = _safe_mean(pre_west)
    oe_mean = _safe_mean(post_east)
    ow_mean = _safe_mean(post_west)

    east_diff = oe_mean - pe_mean
    west_diff = ow_mean - pw_mean

    did_est, ci_lower, ci_upper, p_value = _bootstrap_did(
        pre_east, pre_west, post_east, post_west, n_bootstrap, seed
    )

    return {
        "period1_label": period1_years,
        "period2_label": period2_years,
        "aggregate_by": aggregate_by,
        "n_bootstrap": n_bootstrap,
        "period1_eastbound_n": len(pre_east),
        "period1_eastbound_mean": round(pe_mean, 1),
        "period1_westbound_n": len(pre_west),
        "period1_westbound_mean": round(pw_mean, 1),
        "period2_eastbound_n": len(post_east),
        "period2_eastbound_mean": round(oe_mean, 1),
        "period2_westbound_n": len(post_west),
        "period2_westbound_mean": round(ow_mean, 1),
        "eastbound_diff": round(east_diff, 1),
        "westbound_diff": round(west_diff, 1),
        "did_estimate": round(did_est, 1),
        "did_ci_lower": round(ci_lower, 1),
        "did_ci_upper": round(ci_upper, 1),
        "did_p_value": round(p_value, 6),
        "significant": p_value < 0.05,
        "latitude_band": [lat_min, lat_max] if lat_min is not None or lat_max is not None else None,
        "longitude_band": [lon_min, lon_max]
        if lon_min is not None or lon_max is not None
        else None,
        "nationality_filter": nationality,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
        "wind_force_min_filter": wind_force_min,
        "wind_force_max_filter": wind_force_max,
    }


def _mann_whitney_u(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """Mann-Whitney U test with large-sample normal approximation.

    Returns (U, z, p_value). No scipy dependency.
    """
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return 0.0, 0.0, 1.0

    # Rank all observations combined
    combined = [(v, 0) for v in x] + [(v, 1) for v in y]
    combined.sort(key=lambda t: t[0])

    # Assign ranks (average ties)
    ranks: list[float] = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 1) / 2  # 1-based average rank
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    # Sum of ranks for group 1
    r1 = sum(ranks[k] for k in range(len(combined)) if combined[k][1] == 0)

    # U statistic
    u1 = r1 - n1 * (n1 + 1) / 2

    # Normal approximation
    mean_u = n1 * n2 / 2
    std_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if std_u == 0:
        return u1, 0.0, 1.0

    z = (u1 - mean_u) / std_u

    # Two-tailed p-value from normal distribution (no scipy needed)
    p = math.erfc(abs(z) / math.sqrt(2))

    return u1, z, p


# ---------------------------------------------------------------------------
# Bootstrap Mean Difference (two-sample)
# ---------------------------------------------------------------------------


def _bootstrap_mean_diff(
    group1: list[float],
    group2: list[float],
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> tuple[float, float, float, float]:
    """Bootstrap difference in means with CI and p-value.

    Returns (diff, ci_lower, ci_upper, p_value).
    """
    if not group1 or not group2:
        return 0.0, 0.0, 0.0, 1.0

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs)

    diff = _mean(group2) - _mean(group1)

    rng = random.Random(seed)
    boot_diffs: list[float] = []
    for _ in range(n_bootstrap):
        b1 = rng.choices(group1, k=len(group1))
        b2 = rng.choices(group2, k=len(group2))
        boot_diffs.append(_mean(b2) - _mean(b1))

    boot_diffs.sort()
    ci_lower = boot_diffs[max(0, int(0.025 * n_bootstrap) - 1)]
    ci_upper = boot_diffs[min(n_bootstrap - 1, int(0.975 * n_bootstrap))]

    n_le_zero = sum(1 for d in boot_diffs if d <= 0)
    n_ge_zero = sum(1 for d in boot_diffs if d >= 0)
    p_value = 2 * min(n_le_zero, n_ge_zero) / n_bootstrap
    p_value = min(p_value, 1.0)
    if p_value == 0.0:
        p_value = 1.0 / n_bootstrap

    return diff, ci_lower, ci_upper, p_value


# ---------------------------------------------------------------------------
# Tortuosity — per-voyage route efficiency
# ---------------------------------------------------------------------------


def compute_track_tortuosity(
    voyage_id: int,
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    exclude_anchored: bool = True,
) -> dict[str, Any] | None:
    """Compute route tortuosity for a single voyage within a bounding box.

    Tortuosity = path_km / net_km. Values >= 1.0, where 1.0 = perfectly
    direct route and higher = more meandering.

    Returns dict with path_km, net_km, tortuosity_r, inferred_direction,
    n_in_box, or None if voyage not found or insufficient positions.
    """
    _load_tracks()
    track = _TRACK_INDEX.get(voyage_id)
    if track is None:
        return None

    has_bbox = any(v is not None for v in (lat_min, lat_max, lon_min, lon_max))

    # Collect positions within bbox (excluding anchored positions)
    in_box: list[dict[str, Any]] = []
    for pos in track.get("positions", []):
        if exclude_anchored and pos.get("anch") == 1:
            continue
        lat, lon = pos.get("lat"), pos.get("lon")
        if lat is None or lon is None:
            continue
        if has_bbox and not _pos_in_bbox(lat, lon, lat_min, lat_max, lon_min, lon_max):
            continue
        in_box.append(pos)

    if len(in_box) < 2:
        return None

    # Compute actual path distance, filtering by speed bounds
    path_km = 0.0
    valid_positions: list[dict[str, Any]] = [in_box[0]]
    for i in range(1, len(in_box)):
        p1, p2 = in_box[i - 1], in_box[i]
        d1 = _parse_date(p1.get("date", ""))
        d2 = _parse_date(p2.get("date", ""))
        if d1 is None or d2 is None:
            continue
        days = (d2 - d1).days
        if days <= 0:
            continue
        dist = _haversine_km(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        km_day = dist / days
        if km_day < min_speed or km_day > max_speed:
            continue
        path_km += dist
        valid_positions.append(p2)

    if len(valid_positions) < 2 or path_km <= 0:
        return None

    first = valid_positions[0]
    last = valid_positions[-1]
    net_km = _haversine_km(first["lat"], first["lon"], last["lat"], last["lon"])

    if net_km <= 0:
        return None

    tortuosity_r = path_km / net_km
    inferred_direction = _infer_direction(first["lon"], last["lon"])

    return {
        "voyage_id": voyage_id,
        "ship_name": track.get("ship_name"),
        "nationality": track.get("nationality"),
        "path_km": round(path_km, 1),
        "net_km": round(net_km, 1),
        "tortuosity_r": round(tortuosity_r, 4),
        "inferred_direction": inferred_direction,
        "n_in_box": len(valid_positions),
    }


def _compute_voyage_tortuosity(
    track: dict[str, Any],
    lat_min: float | None,
    lat_max: float | None,
    lon_min: float | None,
    lon_max: float | None,
    min_speed: float,
    max_speed: float,
    min_positions: int,
    month_start: int | None,
    month_end: int | None,
) -> dict[str, Any] | None:
    """Compute tortuosity for a track within bbox. Returns dict or None."""
    has_bbox = any(v is not None for v in (lat_min, lat_max, lon_min, lon_max))

    in_box: list[dict[str, Any]] = []
    for pos in track.get("positions", []):
        lat, lon = pos.get("lat"), pos.get("lon")
        if lat is None or lon is None:
            continue
        if has_bbox and not _pos_in_bbox(lat, lon, lat_min, lat_max, lon_min, lon_max):
            continue
        # Apply month filter
        if month_start is not None or month_end is not None:
            d = _parse_date(pos.get("date", ""))
            if d is None or not _month_in_range(d.month, month_start, month_end):
                continue
        in_box.append(pos)

    if len(in_box) < min_positions:
        return None

    path_km = 0.0
    valid_positions: list[dict[str, Any]] = [in_box[0]]
    for i in range(1, len(in_box)):
        p1, p2 = in_box[i - 1], in_box[i]
        d1 = _parse_date(p1.get("date", ""))
        d2 = _parse_date(p2.get("date", ""))
        if d1 is None or d2 is None:
            continue
        days = (d2 - d1).days
        if days <= 0:
            continue
        dist = _haversine_km(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        km_day = dist / days
        if km_day < min_speed or km_day > max_speed:
            continue
        path_km += dist
        valid_positions.append(p2)

    if len(valid_positions) < min_positions or path_km <= 0:
        return None

    first = valid_positions[0]
    last = valid_positions[-1]
    net_km = _haversine_km(first["lat"], first["lon"], last["lat"], last["lon"])
    if net_km <= 0:
        return None

    tortuosity_r = path_km / net_km
    inferred_direction = _infer_direction(first["lon"], last["lon"])

    # Determine the year from the midpoint of the segment
    mid_pos = valid_positions[len(valid_positions) // 2]
    mid_date = _parse_date(mid_pos.get("date", ""))

    return {
        "voyage_id": track["voyage_id"],
        "tortuosity_r": tortuosity_r,
        "path_km": path_km,
        "net_km": net_km,
        "inferred_direction": inferred_direction,
        "n_in_box": len(valid_positions),
        "year": mid_date.year if mid_date else None,
        "nationality": track.get("nationality"),
    }


def _tortuosity_group_key(info: dict[str, Any], group_by: str) -> str | None:
    """Compute group key for a tortuosity result."""
    if group_by == "decade":
        yr = info.get("year")
        return str((yr // 10) * 10) if yr else None
    if group_by == "year":
        yr = info.get("year")
        return str(yr) if yr else None
    if group_by == "direction":
        return info.get("inferred_direction")
    if group_by == "nationality":
        return info.get("nationality")
    return None


def _compute_tortuosity_stats(values: list[float]) -> dict[str, Any]:
    """Compute descriptive statistics for tortuosity values."""
    n = len(values)
    if n == 0:
        return {
            "n": 0,
            "mean_tortuosity": 0,
            "median_tortuosity": 0,
            "std_tortuosity": 0,
            "ci_lower": 0,
            "ci_upper": 0,
        }

    mean = statistics.mean(values)
    med = statistics.median(values)
    std = statistics.stdev(values) if n > 1 else 0.0
    se = std / math.sqrt(n) if n > 0 else 0.0
    sorted_vals = sorted(values)
    p25_idx = max(0, int(n * 0.25) - 1)
    p75_idx = min(n - 1, int(n * 0.75))

    return {
        "n": n,
        "mean_tortuosity": round(mean, 4),
        "median_tortuosity": round(med, 4),
        "std_tortuosity": round(std, 4),
        "ci_lower": round(mean - 1.96 * se, 4),
        "ci_upper": round(mean + 1.96 * se, 4),
        "p25_tortuosity": round(sorted_vals[p25_idx], 4),
        "p75_tortuosity": round(sorted_vals[p75_idx], 4),
    }


def aggregate_track_tortuosity(
    group_by: str = "decade",
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    direction: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    min_positions: int = 5,
    r_min: float | None = None,
    r_max: float | None = None,
    period1_years: str | None = None,
    period2_years: str | None = None,
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> dict[str, Any]:
    """Aggregate route tortuosity across matching tracks.

    For each voyage, computes path_km/net_km within the bbox.
    Groups by decade/year/direction/nationality.
    Optionally compares two periods with bootstrap CI/p-value.

    Args:
        group_by: Grouping dimension — "decade", "year", "direction", "nationality"
        lat_min/lat_max/lon_min/lon_max: Bounding box
        nationality: Filter by nationality code
        year_start/year_end: Filter by year range
        direction: Filter by inferred direction ("eastbound" or "westbound")
        month_start/month_end: Month filter (supports wrap-around)
        min_speed/max_speed: Speed bounds for position pair validation
        min_positions: Minimum positions in bbox segment (default: 5)
        r_min: Minimum tortuosity R to include (e.g. 1.0 to exclude artifacts)
        r_max: Maximum tortuosity R to include (e.g. 5.0 to exclude loiterers)
        period1_years/period2_years: Two periods for bootstrap comparison.
            "YYYY/YYYY" range or "YYYY,YYYY,..." year list.
        n_bootstrap: Bootstrap iterations (default: 10000)
        seed: Random seed (default: 42)

    Returns:
        Dict with groups, optional comparison, filter metadata.
    """
    _load_tracks()

    groups: dict[str, list[float]] = defaultdict(list)
    period1_vals: list[float] = []
    period2_vals: list[float] = []
    total_voyages = 0

    # Parse period ranges if provided
    p1_set: frozenset[int] | None = None
    p2_set: frozenset[int] | None = None
    if period1_years and period2_years:
        p1_set = _parse_period(period1_years)
        p2_set = _parse_period(period2_years)

    for track in _TRACKS:
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue

        info = _compute_voyage_tortuosity(
            track,
            lat_min,
            lat_max,
            lon_min,
            lon_max,
            min_speed,
            max_speed,
            min_positions,
            month_start,
            month_end,
        )
        if info is None:
            continue

        # Apply direction filter
        if direction and info["inferred_direction"] != direction:
            continue

        tort = info["tortuosity_r"]

        # Apply tortuosity R bounds filter
        if r_min is not None and tort < r_min:
            continue
        if r_max is not None and tort > r_max:
            continue

        total_voyages += 1

        # Group
        key = _tortuosity_group_key(info, group_by)
        if key is not None:
            groups[key].append(tort)

        # Period comparison
        yr = info.get("year")
        if yr and p1_set is not None and p2_set is not None:
            if yr in p1_set:
                period1_vals.append(tort)
            elif yr in p2_set:
                period2_vals.append(tort)

    # Compute group stats
    group_results = []
    for key in sorted(groups.keys(), key=lambda k: (k.isdigit(), int(k) if k.isdigit() else 0, k)):
        stats = _compute_tortuosity_stats(groups[key])
        stats["group_key"] = key
        group_results.append(stats)

    result: dict[str, Any] = {
        "total_voyages": total_voyages,
        "min_positions_required": min_positions,
        "group_by": group_by,
        "groups": group_results,
        "latitude_band": [lat_min, lat_max] if lat_min is not None or lat_max is not None else None,
        "longitude_band": [lon_min, lon_max]
        if lon_min is not None or lon_max is not None
        else None,
        "direction_filter": direction,
        "nationality_filter": nationality,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
        "r_min_filter": r_min,
        "r_max_filter": r_max,
    }

    # Period comparison
    if period1_years and period2_years and period1_vals and period2_vals:
        diff, ci_lo, ci_hi, p_val = _bootstrap_mean_diff(
            period1_vals, period2_vals, n_bootstrap, seed
        )
        result["comparison"] = {
            "period1_label": period1_years,
            "period1_n": len(period1_vals),
            "period1_mean": round(statistics.mean(period1_vals), 4),
            "period2_label": period2_years,
            "period2_n": len(period2_vals),
            "period2_mean": round(statistics.mean(period2_vals), 4),
            "diff": round(diff, 4),
            "ci_lower": round(ci_lo, 4),
            "ci_upper": round(ci_hi, 4),
            "p_value": round(p_val, 6),
            "significant": p_val < 0.05,
        }

    return result


# ---------------------------------------------------------------------------
# Export raw speed samples
# ---------------------------------------------------------------------------


def export_speeds(
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    direction: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    aggregate_by: str = "voyage",
    min_speed: float = 5.0,
    max_speed: float = 400.0,
    wind_force_min: int | None = None,
    wind_force_max: int | None = None,
    max_results: int = 5000,
    offset: int = 0,
) -> dict[str, Any]:
    """Export raw speed samples for downstream analysis.

    Unlike aggregate_track_speeds which groups and summarises, this returns
    individual speed records with full metadata so models can perform
    arbitrary grouping (e.g. ENSO phase classification by year).

    Args:
        lat_min/lat_max/lon_min/lon_max: Bounding box for position filtering
        nationality: Filter tracks by nationality code
        year_start/year_end: Filter tracks by year range
        direction: Filter observations by "eastbound" or "westbound"
        month_start/month_end: Filter by month (1-12), supports wrap-around
        aggregate_by: "observation" (each daily speed) or "voyage" (one mean
            per voyage with metadata — recommended for statistical tests)
        min_speed/max_speed: Speed bounds in km/day
        wind_force_min/wind_force_max: Beaufort force bounds (0-12)
        max_results: Maximum number of records per page (default 5000)
        offset: Skip this many records before returning (for pagination)

    Returns:
        Dict with samples list and total count. Each sample includes
        voyage_id, year, month, direction, speed_km_day, nationality,
        ship_name, and (for observation-level) date, day, wind_force,
        wind_direction, lat, lon. The date field is ISO format (YYYY-MM-DD)
        for lunar phase computation and other temporal analyses.
        Includes has_more and next_offset for pagination.
    """
    _load_tracks()
    voyage_level = aggregate_by == "voyage"

    # Collect all matching records first, then paginate
    all_records: list[dict[str, Any]] = []
    voyage_accum: dict[int, dict[str, Any]] = {}

    for track in _TRACKS:
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue

        speeds = _compute_daily_speeds(
            track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed
        )
        if not speeds:
            continue

        vid = track["voyage_id"]
        nat = track.get("nationality")
        ship = track.get("ship_name")

        for obs in speeds:
            if direction and obs.get("direction") != direction:
                continue

            d = _parse_date(obs["date"])
            if d is None:
                continue

            if month_start is not None or month_end is not None:
                if not _month_in_range(d.month, month_start, month_end):
                    continue

            if wind_force_min is not None or wind_force_max is not None:
                wf = obs.get("wind_force")
                if wf is None:
                    continue
                if wind_force_min is not None and wf < wind_force_min:
                    continue
                if wind_force_max is not None and wf > wind_force_max:
                    continue

            if voyage_level:
                if vid not in voyage_accum:
                    voyage_accum[vid] = {
                        "voyage_id": vid,
                        "nationality": nat,
                        "ship_name": ship,
                        "direction": obs.get("direction"),
                        "year": d.year,
                        "speeds": [],
                        "months": [],
                    }
                voyage_accum[vid]["speeds"].append(obs["km_day"])
                voyage_accum[vid]["months"].append(d.month)
            else:
                all_records.append(
                    {
                        "voyage_id": vid,
                        "date": obs["date"],
                        "year": d.year,
                        "month": d.month,
                        "day": d.day,
                        "direction": obs.get("direction"),
                        "speed_km_day": obs["km_day"],
                        "nationality": nat,
                        "ship_name": ship,
                        "lat": obs.get("lat"),
                        "lon": obs.get("lon"),
                        "wind_force": obs.get("wind_force"),
                        "wind_direction": obs.get("wind_direction"),
                    }
                )

    if voyage_level:
        for va in voyage_accum.values():
            spds = va["speeds"]
            months = va["months"]
            mean_spd = statistics.mean(spds) if spds else 0.0
            month_counts: dict[int, int] = {}
            for m in months:
                month_counts[m] = month_counts.get(m, 0) + 1
            primary_month = (
                max(month_counts, key=lambda k: month_counts[k]) if month_counts else None
            )
            all_records.append(
                {
                    "voyage_id": va["voyage_id"],
                    "year": va["year"],
                    "month": primary_month,
                    "direction": va["direction"],
                    "speed_km_day": round(mean_spd, 1),
                    "nationality": va["nationality"],
                    "ship_name": va["ship_name"],
                    "n_observations": len(spds),
                }
            )

    total_matching = len(all_records)
    # Apply pagination: skip offset, take max_results
    page = all_records[offset : offset + max_results]
    has_more = (offset + max_results) < total_matching
    next_offset = (offset + max_results) if has_more else None

    return {
        "total_matching": total_matching,
        "returned": len(page),
        "offset": offset,
        "has_more": has_more,
        "next_offset": next_offset,
        "aggregate_by": aggregate_by,
        "samples": page,
        "latitude_band": [lat_min, lat_max] if lat_min is not None or lat_max is not None else None,
        "longitude_band": [lon_min, lon_max]
        if lon_min is not None or lon_max is not None
        else None,
        "direction_filter": direction,
        "nationality_filter": nationality,
        "year_start_filter": year_start,
        "year_end_filter": year_end,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
        "wind_force_min_filter": wind_force_min,
        "wind_force_max_filter": wind_force_max,
    }


# ---------------------------------------------------------------------------
# Wind Rose — Beaufort force distribution
# ---------------------------------------------------------------------------


def wind_rose(
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    direction: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    period1_years: str | None = None,
    period2_years: str | None = None,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
) -> dict[str, Any]:
    """Count observations by Beaufort wind force and direction, with optional period comparison.

    Returns dict with beaufort_counts, direction_counts, period splits,
    and wind data availability. Wind direction is available for ~97% of
    observations even when Beaufort force is missing.
    """
    _load_tracks()

    # Beaufort force counters: force -> [speeds]
    all_counts: dict[int, list[float]] = defaultdict(list)
    p1_counts: dict[int, list[float]] = defaultdict(list)
    p2_counts: dict[int, list[float]] = defaultdict(list)
    total_with_wind = 0
    total_without_wind = 0
    voyage_ids: set[int] = set()

    # Wind direction counters: sector -> [speeds]
    all_dir_counts: dict[str, list[float]] = defaultdict(list)
    p1_dir_counts: dict[str, list[float]] = defaultdict(list)
    p2_dir_counts: dict[str, list[float]] = defaultdict(list)
    total_with_direction = 0
    total_without_direction = 0

    # Logged vs haversine distance calibration
    logged_dists: list[float] = []
    haversine_dists: list[float] = []

    # Parse periods
    p1_set: frozenset[int] | None = None
    p2_set: frozenset[int] | None = None
    if period1_years and period2_years:
        p1_set = _parse_period(period1_years)
        p2_set = _parse_period(period2_years)

    for track in _TRACKS:
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue

        speeds = _compute_daily_speeds(
            track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed
        )
        if not speeds:
            continue

        for obs in speeds:
            if direction and obs.get("direction") != direction:
                continue
            if month_start is not None or month_end is not None:
                d = _parse_date(obs["date"])
                if d is None or not _month_in_range(d.month, month_start, month_end):
                    continue

            # Collect logged vs haversine distances for calibration
            # CLIWOC Distance field is in nautical miles; convert to km
            logged = obs.get("logged_dist")
            if logged is not None and logged > 0:
                logged_dists.append(logged * 1.852)  # nm -> km
                haversine_dists.append(obs["km_day"])

            # Determine observation year for period splitting
            obs_year: int | None = None
            has_periods = p1_set is not None and p2_set is not None
            if has_periods:
                d = _parse_date(obs["date"])
                if d:
                    obs_year = d.year

            # Wind direction (available for ~97% of observations)
            wd = obs.get("wind_direction")
            sector = _wind_dir_to_sector(wd) if wd is not None else None
            if sector is not None:
                total_with_direction += 1
                all_dir_counts[sector].append(obs["km_day"])
                if obs_year is not None and p1_set is not None and p2_set is not None:
                    if obs_year in p1_set:
                        p1_dir_counts[sector].append(obs["km_day"])
                    elif obs_year in p2_set:
                        p2_dir_counts[sector].append(obs["km_day"])
            else:
                total_without_direction += 1

            # Beaufort force (available for ~17% of observations)
            wf = obs.get("wind_force")
            if wf is None:
                total_without_wind += 1
                continue

            total_with_wind += 1
            voyage_ids.add(track["voyage_id"])
            all_counts[wf].append(obs["km_day"])

            if obs_year is not None and p1_set is not None and p2_set is not None:
                if obs_year in p1_set:
                    p1_counts[wf].append(obs["km_day"])
                elif obs_year in p2_set:
                    p2_counts[wf].append(obs["km_day"])

    has_wind = total_with_wind > 0
    has_direction = total_with_direction > 0

    def _make_beaufort_counts(counts: dict[int, list[float]], total: int) -> list[dict[str, Any]]:
        result = []
        for force in range(13):  # 0-12
            speeds_list = counts.get(force, [])
            count = len(speeds_list)
            pct = (100 * count / total) if total > 0 else 0.0
            mean_spd = statistics.mean(speeds_list) if speeds_list else None
            result.append(
                {
                    "force": force,
                    "count": count,
                    "percent": round(pct, 1),
                    "mean_speed_km_day": round(mean_spd, 1) if mean_spd is not None else None,
                }
            )
        return result

    def _make_direction_counts(counts: dict[str, list[float]], total: int) -> list[dict[str, Any]]:
        result = []
        for sector in _COMPASS_SECTORS:
            speeds_list = counts.get(sector, [])
            count = len(speeds_list)
            pct = (100 * count / total) if total > 0 else 0.0
            mean_spd = statistics.mean(speeds_list) if speeds_list else None
            result.append(
                {
                    "sector": sector,
                    "count": count,
                    "percent": round(pct, 1),
                    "mean_speed_km_day": round(mean_spd, 1) if mean_spd is not None else None,
                }
            )
        return result

    # Distance calibration stats
    calibration = None
    if logged_dists:
        n_cal = len(logged_dists)
        mean_logged = statistics.mean(logged_dists)
        mean_haversine = statistics.mean(haversine_dists)
        ratio = mean_logged / mean_haversine if mean_haversine > 0 else None
        calibration = {
            "n_pairs": n_cal,
            "mean_logged_km_day": round(mean_logged, 1),
            "mean_haversine_km_day": round(mean_haversine, 1),
            "logged_over_haversine": round(ratio, 3) if ratio else None,
        }

    result: dict[str, Any] = {
        "total_with_wind": total_with_wind,
        "total_without_wind": total_without_wind,
        "total_with_direction": total_with_direction,
        "total_without_direction": total_without_direction,
        "total_voyages": len(voyage_ids),
        "has_wind_data": has_wind,
        "has_direction_data": has_direction,
        "beaufort_counts": _make_beaufort_counts(all_counts, total_with_wind),
        "direction_counts": _make_direction_counts(all_dir_counts, total_with_direction),
        "distance_calibration": calibration,
        "latitude_band": [lat_min, lat_max] if lat_min is not None or lat_max is not None else None,
        "longitude_band": [lon_min, lon_max]
        if lon_min is not None or lon_max is not None
        else None,
        "direction_filter": direction,
        "nationality_filter": nationality,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
    }

    if period1_years and period2_years:
        p1_total = sum(len(v) for v in p1_counts.values())
        p2_total = sum(len(v) for v in p2_counts.values())
        result["period1_label"] = period1_years
        result["period1_counts"] = _make_beaufort_counts(p1_counts, p1_total)
        result["period2_label"] = period2_years
        result["period2_counts"] = _make_beaufort_counts(p2_counts, p2_total)
        # Direction period splits
        p1_dir_total = sum(len(v) for v in p1_dir_counts.values())
        p2_dir_total = sum(len(v) for v in p2_dir_counts.values())
        result["period1_direction_counts"] = _make_direction_counts(p1_dir_counts, p1_dir_total)
        result["period2_direction_counts"] = _make_direction_counts(p2_dir_counts, p2_dir_total)

    return result


# ---------------------------------------------------------------------------
# Wind direction by year — for ENSO phase detection
# ---------------------------------------------------------------------------


def wind_direction_by_year(
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    nationality: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    direction: str | None = None,
    month_start: int | None = None,
    month_end: int | None = None,
    min_speed: float = 5.0,
    max_speed: float = 400.0,
) -> dict[str, Any]:
    """Compute year-by-year wind direction sector distributions.

    Groups CLIWOC observations by year and returns 8-compass-sector
    distributions for each year. Wind direction data has ~97.5% coverage
    across the full 1662-1854 period, making this a powerful tool for
    detecting long-term atmospheric circulation shifts (e.g. ENSO phases,
    Walker circulation changes).

    Args:
        lat_min/lat_max/lon_min/lon_max: Bounding box filter
        nationality: Filter by nationality code
        year_start/year_end: Year range filter
        direction: Filter by sailing direction ("eastbound"/"westbound")
        month_start/month_end: Month filter (supports wrap-around)
        min_speed/max_speed: Speed bounds in km/day

    Returns:
        Dict with per-year sector distributions, mean speeds per sector,
        and summary statistics.
    """
    _load_tracks()

    # year -> sector -> [speeds]
    year_data: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    total_obs = 0
    total_with_dir = 0

    for track in _TRACKS:
        if nationality and track.get("nationality") != nationality.upper():
            continue
        if year_start and (track.get("year_start") or 9999) < year_start:
            continue
        if year_end and (track.get("year_end") or 0) > year_end:
            continue

        speeds = _compute_daily_speeds(
            track, lat_min, lat_max, lon_min, lon_max, min_speed, max_speed
        )
        if not speeds:
            continue

        for obs in speeds:
            if direction and obs.get("direction") != direction:
                continue
            d = _parse_date(obs["date"])
            if d is None:
                continue
            if month_start is not None or month_end is not None:
                if not _month_in_range(d.month, month_start, month_end):
                    continue

            total_obs += 1
            wd = obs.get("wind_direction")
            sector = _wind_dir_to_sector(wd) if wd is not None else None
            if sector is not None:
                total_with_dir += 1
                year_data[d.year][sector].append(obs["km_day"])

    # Build per-year distributions
    years_list: list[dict[str, Any]] = []
    for yr in sorted(year_data.keys()):
        sectors = year_data[yr]
        total_yr = sum(len(v) for v in sectors.values())
        sector_counts = []
        for s in _COMPASS_SECTORS:
            speeds_list = sectors.get(s, [])
            count = len(speeds_list)
            pct = (100 * count / total_yr) if total_yr > 0 else 0.0
            mean_spd = statistics.mean(speeds_list) if speeds_list else None
            sector_counts.append(
                {
                    "sector": s,
                    "count": count,
                    "percent": round(pct, 1),
                    "mean_speed_km_day": round(mean_spd, 1) if mean_spd is not None else None,
                }
            )
        years_list.append(
            {
                "year": yr,
                "total_observations": total_yr,
                "sectors": sector_counts,
            }
        )

    return {
        "total_observations": total_obs,
        "total_with_direction": total_with_dir,
        "total_years": len(years_list),
        "years": years_list,
        "latitude_band": [lat_min, lat_max] if lat_min is not None or lat_max is not None else None,
        "longitude_band": [lon_min, lon_max]
        if lon_min is not None or lon_max is not None
        else None,
        "direction_filter": direction,
        "nationality_filter": nationality,
        "month_start_filter": month_start,
        "month_end_filter": month_end,
    }


# Load on import
_load_tracks()
