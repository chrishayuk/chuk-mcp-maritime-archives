#!/usr/bin/env python3
"""
Download NOAA AWOIS wreck data from ArcGIS REST API.

Downloads ~13,000 wreck records from the NOAA Office of Coast Survey
Automated Wreck and Obstruction Information System (AWOIS), maps
fields to our standard wreck format, and saves as JSON.

Source:
    NOAA Office of Coast Survey. ENC Online / AWOIS.
    https://gis.charttools.noaa.gov/arcgis/rest/services/MCS/ENCOnline/MapServer/5
    Public Domain (US Government work).

Produces:
    data/noaa_wrecks.json  -- ~13,000 wreck records

Usage:
    python scripts/download_noaa.py
    python scripts/download_noaa.py --force

Note:
    If the ArcGIS service is unavailable, run generate_noaa.py for a
    curated fallback subset of ~50 representative US wrecks.
"""

import json
import sys
import urllib.request

from download_utils import DATA_DIR, is_cached, parse_args, save_json

WRECKS_OUTPUT = DATA_DIR / "noaa_wrecks.json"
ARCHIVE = "noaa"

# NOAA ArcGIS REST endpoint for wrecks layer
ARCGIS_BASE = "https://gis.charttools.noaa.gov/arcgis/rest/services/MCS/ENCOnline/MapServer/5/query"
USER_AGENT = "chuk-mcp-maritime-archives/0.12.0"

# Batch size for paginated queries
BATCH_SIZE = 1000

# GP quality codes -> uncertainty in km
GP_UNCERTAINTY: dict[int, float] = {
    1: 0.03,  # High accuracy
    2: 5.0,  # Medium accuracy
    3: 50.0,  # Low accuracy
    4: 500.0,  # Poor accuracy
}


# ---------------------------------------------------------------------------
# Region classifier (US waters focus)
# ---------------------------------------------------------------------------


def classify_region(lat: float, lon: float) -> str | None:
    """Classify a US-waters position into a region."""
    # Great Lakes
    if 41.0 <= lat <= 49.0 and -92.0 <= lon <= -76.0:
        return "great_lakes"
    # Gulf of Mexico
    if 18.0 <= lat <= 31.0 and -98.0 <= lon <= -80.0:
        return "gulf_of_mexico"
    # Caribbean
    if 10.0 <= lat <= 27.0 and -85.0 <= lon <= -60.0:
        return "caribbean"
    # North Pacific (US West Coast, Hawaii, Alaska)
    if lat > 0 and lon < -100.0:
        return "north_pacific"
    # North Atlantic (US East Coast, catch-all)
    if lat > 0 and -100.0 <= lon <= -30.0:
        return "north_atlantic"
    return None


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------


def map_loss_cause(history: str | None) -> str:
    """Map NOAA HISTORY field to our LOSS_CAUSES enum."""
    if not history:
        return "unknown"
    h = history.lower()
    if any(w in h for w in ("storm", "gale", "hurricane", "weather", "seas", "wind")):
        return "storm"
    if any(w in h for w in ("reef", "rock", "shoal", "coral")):
        return "reef"
    if any(w in h for w in ("fire", "explosion", "exploded", "burnt")):
        return "fire"
    if any(w in h for w in ("torpedo", "mine", "u-boat", "submarine", "war", "enemy", "battle")):
        return "battle"
    if any(w in h for w in ("ground", "ashore", "strand", "beached")):
        return "grounding"
    if any(w in h for w in ("collision", "collided", "struck", "rammed")):
        return "collision"
    if any(w in h for w in ("scuttled", "sunk deliberately", "abandoned")):
        return "scuttled"
    return "unknown"


def map_gp_quality(gp: int | None) -> tuple[int, float]:
    """Map GP quality code to (code, uncertainty_km)."""
    if gp and gp in GP_UNCERTAINTY:
        return gp, GP_UNCERTAINTY[gp]
    return 4, 500.0  # Default to poor if unknown


def parse_feature(attrs: dict, index: int) -> dict | None:
    """Convert ArcGIS feature attributes to our wreck record format."""
    lat = attrs.get("LATDEC")
    lon = attrs.get("LONDEC")

    if lat is None or lon is None:
        return None

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return None

    ship_name = attrs.get("VESSLTERMS") or "Unknown"
    year_sunk = attrs.get("YEARSUNK")
    loss_date = None
    if year_sunk:
        try:
            loss_date = f"{int(year_sunk)}-01-01"
        except (ValueError, TypeError):
            pass

    history = attrs.get("HISTORY") or ""
    depth_val = attrs.get("DEPTH")
    depth_m = None
    if depth_val is not None:
        try:
            # NOAA depths are typically in feet; convert
            depth_ft = float(depth_val)
            depth_m = round(depth_ft * 0.3048, 1)
        except (ValueError, TypeError):
            pass

    gp_raw = attrs.get("GP_QUALITY")
    gp_code = None
    if gp_raw is not None:
        try:
            gp_code = int(gp_raw)
        except (ValueError, TypeError):
            pass
    gp_quality, uncertainty_km = map_gp_quality(gp_code)

    wreck_id = f"{ARCHIVE}_wreck:{index:05d}"

    return {
        "wreck_id": wreck_id,
        "ship_name": ship_name,
        "loss_date": loss_date,
        "loss_cause": map_loss_cause(history),
        "loss_location": attrs.get("CHART"),
        "region": classify_region(lat, lon),
        "status": "found",  # AWOIS entries are charted wrecks
        "position": {"lat": lat, "lon": lon, "uncertainty_km": uncertainty_km},
        "depth_estimate_m": depth_m,
        "flag": "US",  # AWOIS covers US waters; nationality not always recorded
        "vessel_type": attrs.get("FEATURE_TYPE"),
        "gp_quality": gp_quality,
        "archive": ARCHIVE,
    }


# ---------------------------------------------------------------------------
# ArcGIS REST download
# ---------------------------------------------------------------------------


def fetch_page(offset: int, count: int) -> dict:
    """Fetch a page of features from NOAA ArcGIS REST API."""
    params = f"where=1%3D1&outFields=*&resultOffset={offset}&resultRecordCount={count}&f=json"
    url = f"{ARCGIS_BASE}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_all_features() -> list[dict]:
    """Download all features from NOAA ArcGIS with pagination."""
    all_attrs: list[dict] = []
    offset = 0

    print("  Downloading from NOAA ArcGIS REST API (paginated)...")
    while True:
        sys.stdout.write(f"\r  Fetching records {offset}–{offset + BATCH_SIZE}...")
        sys.stdout.flush()

        data = fetch_page(offset, BATCH_SIZE)
        features = data.get("features", [])

        if not features:
            break

        for f in features:
            attrs = f.get("attributes", {})
            if attrs:
                all_attrs.append(attrs)

        print(f" got {len(features)} (total: {len(all_attrs)})")

        if len(features) < BATCH_SIZE:
            break  # Last page

        offset += BATCH_SIZE

    print(f"  Downloaded {len(all_attrs)} features total")
    return all_attrs


def main() -> None:
    args = parse_args("Download NOAA AWOIS wreck data")

    if not args.force and is_cached(WRECKS_OUTPUT, args.cache_max_age):
        print(f"  {WRECKS_OUTPUT.name} is up to date (use --force to re-download)")
        return

    print("NOAA AWOIS Wrecks — ArcGIS REST Download")
    print("=" * 50)

    try:
        all_attrs = download_all_features()
    except Exception as e:
        print(f"\n  ERROR: NOAA ArcGIS download failed: {e}")
        print("  Falling back to curated subset (run generate_noaa.py)")
        sys.exit(1)

    # Convert to our format
    wrecks = []
    skipped = 0
    for i, attrs in enumerate(all_attrs, start=1):
        record = parse_feature(attrs, i)
        if record:
            wrecks.append(record)
        else:
            skipped += 1

    print(f"  Converted {len(wrecks)} wrecks ({skipped} skipped)")

    # Validate
    for w in wrecks:
        assert w["archive"] == ARCHIVE

    save_json(wrecks, WRECKS_OUTPUT.name, compact=True)
    print(f"\n  Done! {len(wrecks)} NOAA wrecks saved to {WRECKS_OUTPUT.name}")


if __name__ == "__main__":
    main()
