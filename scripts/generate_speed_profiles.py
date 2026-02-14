#!/usr/bin/env python3
"""
Generate speed profiles from CLIWOC ship track data.

Reads data/cliwoc_tracks.json and data/routes.json, computes daily sailing
distances using the haversine formula, assigns each observation to the
nearest route segment, and writes aggregate statistics to
data/speed_profiles.json.

Run from the project root:

    python scripts/generate_speed_profiles.py
"""

import json
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

from download_utils import is_cached, parse_args

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRACKS_PATH = DATA_DIR / "cliwoc_tracks.json"
ROUTES_PATH = DATA_DIR / "routes.json"
OUTPUT_PATH = DATA_DIR / "speed_profiles.json"

# ---------------------------------------------------------------------------
# Haversine (copied from cliwoc_tracks.py)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Route matching — map (voyage_from, voyage_to) to a route_id
# ---------------------------------------------------------------------------

# Netherlands port names found in CLIWOC data
_NL_PORTS = {
    "TEXEL",
    "ROTTERDAM",
    "AMSTERDAM",
    "NIEUWEDIEP",
    "HELLEVOETSLUIS",
    "NEDERLAND",
    "HOLLAND",
    "VLISSINGEN",
    "MIDDELBURG",
    "BROUWERSHAVEN",
    "RAMMEKENS",
    "SCHIEDAM",
    "DORDRECHT",
    "DEN HELDER",
    "WILLEMSOORD",
    "ZIERIKZEE",
    "NIEUWE DIEP",
    "NIEUWENDIEP",
    "ANTWERPEN",
    "TERNEUZEN",
    "ROTERDAM",
    "'T NIEUWE DIEP",
}

# UK departure ports that indicate an East-India-bound voyage
_UK_EAST_PORTS = {
    "DOWNS",
    "SPITHEAD",
    "PORTSMOUTH",
    "PLYMOUTH",
    "GRAVESEND",
    "LONDON",
    "TORBAY",
    "MOTHERBANK",
    "CORK",
    "FALMOUTH",
    "DOWNS UK",
    "PORTHMOUTH",
    "HARTLEPOOL",
    "LIZARD",
}

# Netherlands destination names (return voyages)
_NL_DEST = {
    "NEDERLAND",
    "AMSTERDAM",
    "ROTTERDAM",
    "TEXEL",
    "NIEUWEDIEP",
    "HELLEVOETSLUIS",
    "VLISSINGEN",
    "MIDDELBURG",
    "BROUWERSHAVEN",
    "RAMMEKENS",
    "HOLLAND",
    "DEN HELDER",
    "WILLEMSOORD",
    "SCHIEDAM",
    "DORDRECHT",
    "ANTWERPEN",
    "NIEUW DIEP",
    "EUROPA",
    "NIEUWE DIEP",
}

# UK destinations (return voyages)
_UK_HOME = {
    "DOWNS",
    "SPITHEAD",
    "UK",
    "PORTSMOUTH",
    "PLYMOUTH",
    "LONDON",
    "FALMOUTH",
    "TORBAY",
    "GRAVESEND",
}

# Portuguese ports
_PT_PORTS = {"LISBON", "LISBOA", "BELEM", "PORTO"}
_PT_DEST = {"LISBON", "LISBOA", "PORTUGAL"}

# Swedish ports
_SE_PORTS = {"GOTHENBURG", "GOTEBORG", "GOTHENBORG"}
_SE_DEST = {"GOTHENBURG", "GOTEBORG", "GOTHENBORG", "SWEDEN"}


def _contains_any(text: str, tokens: set) -> bool:
    """Return True if *text* (already upper-cased) contains any token."""
    for tok in tokens:
        if tok in text:
            return True
    return False


def classify_track(voyage_from: str, voyage_to: str) -> str | None:
    """Return a route_id for a track, or None if it cannot be matched."""
    vf = (voyage_from or "").upper().strip()
    vt = (voyage_to or "").upper().strip()

    # --- Outward: Netherlands → Batavia ---
    if _contains_any(vf, _NL_PORTS) and "BATAVIA" in vt:
        return "outward_outer"  # default to outer (most common post-1660)

    # --- EIC Outward: UK → India ---
    if _contains_any(vf, _UK_EAST_PORTS) and any(
        x in vt for x in ["MADRAS", "BOMBAY", "BENGAL", "CEYLON", "CALCUTTA", "SURAT"]
    ):
        return "eic_outward"

    # --- EIC China: UK → Canton/China ---
    if _contains_any(vf, _UK_EAST_PORTS) and any(x in vt for x in ["CHINA", "CANTON", "WHAMPOA"]):
        return "eic_china"

    # --- Outward: UK → Batavia/Java (UK ships on VOC-associated routes) ---
    if _contains_any(vf, _UK_EAST_PORTS) and any(x in vt for x in ["BATAVIA", "JAVA", "ST HELENA"]):
        return "outward_outer"

    # --- Outward: Cape → Batavia (partial, use Indian Ocean segments) ---
    if any(x in vf for x in ["TABLE BAY", "KAAP", "CAPE OF GOOD HOPE", "SIMONSBAAI", "KAAPSTAD"]):
        if "BATAVIA" in vt:
            return "outward_outer"

    # --- Return: Batavia/Java → Netherlands ---
    if ("BATAVIA" in vf or "JAVA" in vf) and _contains_any(vt, _NL_DEST):
        return "return"

    # --- Return: Batavia/Java → UK ---
    if ("BATAVIA" in vf or "JAVA" in vf) and _contains_any(vt, _UK_HOME):
        return "return"

    # --- Return: Java Head → St Helena / Downs (EIC return) ---
    if "JAVA" in vf and any(x in vt for x in ["ST HELENA", "DOWNS", "UK"]):
        return "return"

    # --- Return: Batavia → Cape (partial return) ---
    if "BATAVIA" in vf and any(x in vt for x in ["KAAP", "CAPE", "SIMONS", "TABLE BAY"]):
        return "return"

    # --- Coromandel: Batavia → Indian east coast ---
    if "BATAVIA" in vf and any(
        x in vt for x in ["MADRAS", "PULICAT", "NEGAPAT", "NAGEPATN", "BENGAL", "COROMANDEL"]
    ):
        return "coromandel"

    # --- Ceylon: Batavia → Ceylon ---
    if "BATAVIA" in vf and any(x in vt for x in ["GALLE", "COLOMBO", "CEYLON", "TRINCOMALEE"]):
        return "ceylon"

    # --- Malabar: Batavia → Indian west coast ---
    if "BATAVIA" in vf and any(x in vt for x in ["COCHIN", "CALICUT", "MALABAR"]):
        return "malabar"

    # --- Japan: Batavia → Deshima/Nagasaki ---
    if "BATAVIA" in vf and any(x in vt for x in ["DESHIMA", "NAGASAKI", "JAPAN", "DECIMA"]):
        return "japan"

    # --- Spice Islands: Batavia → Moluccas ---
    if "BATAVIA" in vf and any(x in vt for x in ["AMBON", "BANDA", "TERNATE", "MOLUC"]):
        return "spice_islands"

    # --- EIC Return: India/Canton → UK ---
    if any(x in vf for x in ["MADRAS", "BOMBAY", "CALCUTTA", "CANTON", "BENGAL"]):
        if _contains_any(vt, _UK_HOME):
            return "eic_return"

    # --- Madras → NL (can match VOC return route) ---
    if "MADRAS" in vf and _contains_any(vt, _NL_DEST):
        return "return"

    # --- Cape → NL/UK (partial return, Channel segments) ---
    if any(x in vf for x in ["TABLE BAY", "KAAP", "CAPE OF GOOD HOPE", "SIMONSBAAI"]):
        if _contains_any(vt, _NL_DEST) or _contains_any(vt, _UK_HOME):
            return "return"

    # --- Anjengo/Cochin → Cape (malabar partial) ---
    if any(x in vf for x in ["ANJENGO", "COCHIN"]) and any(x in vt for x in ["CAPE", "KAAP"]):
        return "malabar"

    # --- Carreira outward: Lisbon → Goa/India ---
    if _contains_any(vf, _PT_PORTS) and any(x in vt for x in ["GOA", "COCHIN", "INDIA"]):
        return "carreira_outward"

    # --- Carreira return: Goa/India → Lisbon ---
    if any(x in vf for x in ["GOA", "COCHIN", "INDIA"]):
        if _contains_any(vt, _PT_DEST):
            return "carreira_return"

    # --- SOIC outward: Gothenburg → Canton/China ---
    if _contains_any(vf, _SE_PORTS) and any(x in vt for x in ["CANTON", "CHINA"]):
        return "soic_outward"

    # --- SOIC return: Canton → Gothenburg ---
    if any(x in vf for x in ["CANTON", "CHINA"]):
        if _contains_any(vt, _SE_DEST):
            return "soic_return"

    # --- Galleon westbound: Acapulco → Manila ---
    if "ACAPULCO" in vf and "MANILA" in vt:
        return "galleon_westbound"

    # --- Galleon eastbound: Manila → Acapulco ---
    if "MANILA" in vf and "ACAPULCO" in vt:
        return "galleon_eastbound"

    return None


# ---------------------------------------------------------------------------
# Segment assignment — find which route segment a position belongs to
# ---------------------------------------------------------------------------


def _segment_midpoint(wp_a: dict, wp_b: dict) -> tuple[float, float]:
    """Return the geographic midpoint of two waypoints."""
    return ((wp_a["lat"] + wp_b["lat"]) / 2, (wp_a["lon"] + wp_b["lon"]) / 2)


def assign_segment(
    lat: float,
    lon: float,
    route_segments: list[tuple[str, str, float, float]],
) -> tuple[str, str] | None:
    """
    Assign a position to the nearest route segment.

    *route_segments* is a list of (wp_from_name, wp_to_name, mid_lat, mid_lon).

    Returns (segment_from, segment_to) or None if too far (>2000 km).
    """
    best_dist = float("inf")
    best_seg = None
    for seg_from, seg_to, mid_lat, mid_lon in route_segments:
        d = haversine_km(lat, lon, mid_lat, mid_lon)
        if d < best_dist:
            best_dist = d
            best_seg = (seg_from, seg_to)
    if best_dist > 2000:
        return None
    return best_seg


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def compute_stats(values: list[float]) -> dict:
    """Return statistical summary for a list of daily-km values."""
    n = len(values)
    if n == 0:
        return {}
    mean_val = statistics.mean(values)
    median_val = statistics.median(values)
    std_val = statistics.stdev(values) if n >= 2 else 0.0
    min_val = min(values)
    max_val = max(values)
    if n >= 2:
        quartiles = statistics.quantiles(values, n=4, method="inclusive")
        p25 = quartiles[0]
        p75 = quartiles[2]
    else:
        p25 = values[0]
        p75 = values[0]
    return {
        "sample_count": n,
        "mean_km_day": round(mean_val, 1),
        "median_km_day": round(median_val, 1),
        "std_dev_km_day": round(std_val, 1),
        "min_km_day": round(min_val, 1),
        "max_km_day": round(max_val, 1),
        "p25_km_day": round(p25, 1),
        "p75_km_day": round(p75, 1),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Generate speed profiles from CLIWOC data")

    if not args.force and is_cached(OUTPUT_PATH, args.cache_max_age):
        print(f"Using cached {OUTPUT_PATH.name} (use --force to regenerate)")
        return

    print("Loading CLIWOC tracks …")
    with open(TRACKS_PATH) as f:
        cliwoc = json.load(f)
    tracks = cliwoc["tracks"]
    print(f"  {len(tracks)} tracks loaded")

    print("Loading routes …")
    with open(ROUTES_PATH) as f:
        routes = json.load(f)
    print(f"  {len(routes)} routes loaded")

    # Pre-compute route segments (consecutive waypoint pairs)
    # route_id → list of (from_name, to_name, mid_lat, mid_lon)
    route_segments: dict[str, list[tuple[str, str, float, float]]] = {}
    for route in routes:
        rid = route["route_id"]
        wps = route["waypoints"]
        segs = []
        for i in range(len(wps) - 1):
            a, b = wps[i], wps[i + 1]
            mid_lat, mid_lon = _segment_midpoint(a, b)
            segs.append((a["name"], b["name"], mid_lat, mid_lon))
        route_segments[rid] = segs

    # Collect observations: (route_id, seg_from, seg_to) → {month → [daily_km]}
    observations: dict[tuple[str, str, str], dict[int | None, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    total_obs = 0
    tracks_matched = 0
    tracks_skipped = 0

    print("Processing tracks …")
    for idx, track in enumerate(tracks):
        if (idx + 1) % 200 == 0:
            print(f"  … {idx + 1}/{len(tracks)}")

        route_id = classify_track(track.get("voyage_from"), track.get("voyage_to"))
        if route_id is None:
            tracks_skipped += 1
            continue

        positions = track.get("positions", [])
        if len(positions) < 2:
            tracks_skipped += 1
            continue

        # Departure month from start_date
        start_date_str = track.get("start_date", "")
        try:
            dep_month = int(start_date_str.split("-")[1])
        except (IndexError, ValueError):
            dep_month = None

        segs = route_segments.get(route_id, [])
        if not segs:
            tracks_skipped += 1
            continue

        track_contributed = False

        for i in range(len(positions) - 1):
            p1 = positions[i]
            p2 = positions[i + 1]

            lat1, lon1 = p1["lat"], p1["lon"]
            lat2, lon2 = p2["lat"], p2["lon"]

            daily_km = haversine_km(lat1, lon1, lat2, lon2)

            # Filter: skip data gaps and port stops
            if daily_km > 400:
                continue  # likely multi-day gap
            if daily_km < 5:
                continue  # port stop or anchored

            # Midpoint of the day's travel
            mid_lat = (lat1 + lat2) / 2
            mid_lon = (lon1 + lon2) / 2

            seg = assign_segment(mid_lat, mid_lon, segs)
            if seg is None:
                continue

            seg_from, seg_to = seg
            key = (route_id, seg_from, seg_to)
            observations[key][None].append(daily_km)  # all-months
            if dep_month is not None:
                observations[key][dep_month].append(daily_km)

            total_obs += 1
            track_contributed = True

        if track_contributed:
            tracks_matched += 1

    print(f"  Tracks matched: {tracks_matched}")
    print(f"  Tracks skipped: {tracks_skipped}")
    print(f"  Total observations: {total_obs}")

    # Build profiles
    print("Building profiles …")
    profiles = []

    for (route_id, seg_from, seg_to), month_data in sorted(observations.items()):
        # All-months aggregate (departure_month = null)
        all_values = month_data.get(None, [])
        if all_values:
            stats = compute_stats(all_values)
            profiles.append(
                {
                    "route_id": route_id,
                    "segment_from": seg_from,
                    "segment_to": seg_to,
                    "departure_month": None,
                    **stats,
                }
            )

        # Per-month aggregates (only if >= 5 samples)
        for month in range(1, 13):
            month_values = month_data.get(month, [])
            if len(month_values) >= 5:
                stats = compute_stats(month_values)
                profiles.append(
                    {
                        "route_id": route_id,
                        "segment_from": seg_from,
                        "segment_to": seg_to,
                        "departure_month": month,
                        **stats,
                    }
                )

    # Write output
    output = {
        "generated": date.today().isoformat(),
        "source": "CLIWOC 2.1 Full tracks analysis",
        "total_observations": total_obs,
        "tracks_matched": tracks_matched,
        "profiles": profiles,
    }

    print(f"Writing {OUTPUT_PATH} …")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Done. {len(profiles)} profiles generated.")
    print(f"  Tracks matched: {tracks_matched}")
    print(f"  Total observations: {total_obs}")
    print(f"  Profiles: {len(profiles)}")


if __name__ == "__main__":
    main()
