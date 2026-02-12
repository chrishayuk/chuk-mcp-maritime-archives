#!/usr/bin/env python3
"""
Download UK Hydrographic Office Global Wrecks from EMODnet.

Downloads ~94,000 wreck records from the EMODnet Human Activities WFS
service, maps fields to our standard wreck format, and saves as JSON.

Source:
    UK Hydrographic Office via EMODnet Human Activities portal.
    https://ows.emodnet-humanactivities.eu/wfs
    Open Government Licence v3.0.

Produces:
    data/ukho_wrecks.json  -- ~94,000 wreck records

Usage:
    python scripts/download_ukho.py
    python scripts/download_ukho.py --force

Note:
    The full download may take several minutes due to dataset size.
    If the WFS service is unavailable, run generate_ukho.py for a
    curated fallback subset of ~50 representative wrecks.
"""

import json
import sys
import urllib.request

from download_utils import DATA_DIR, is_cached, parse_args, save_json

WRECKS_OUTPUT = DATA_DIR / "ukho_wrecks.json"
ARCHIVE = "ukho"

# EMODnet WFS endpoint for shipwrecks layer
EMODNET_WFS_BASE = "https://ows.emodnet-humanactivities.eu/wfs"
USER_AGENT = "chuk-mcp-maritime-archives/0.11.0"

# Batch size for paginated WFS requests
WFS_BATCH_SIZE = 10000


# ---------------------------------------------------------------------------
# Region classifier
# ---------------------------------------------------------------------------


def classify_region(lat: float, lon: float) -> str | None:
    """Classify a position into a region using bounding boxes."""
    # English Channel
    if 49.0 <= lat <= 51.5 and -6.0 <= lon <= 2.5:
        return "english_channel"
    # North Sea
    if 51.0 <= lat <= 62.0 and -5.0 <= lon <= 10.0:
        return "north_sea"
    # Baltic
    if 53.5 <= lat <= 66.0 and 10.0 <= lon <= 30.0:
        return "baltic"
    # Mediterranean
    if 30.0 <= lat <= 46.0 and -6.0 <= lon <= 37.0:
        return "mediterranean"
    # Atlantic Europe (Biscay to Canaries)
    if 27.0 <= lat <= 49.0 and -20.0 <= lon <= -5.0:
        return "atlantic_europe"
    # West Africa
    if 0.0 <= lat <= 27.0 and -25.0 <= lon <= 0.0:
        return "west_africa"
    # Caribbean
    if 10.0 <= lat <= 30.0 and -100.0 <= lon <= -55.0:
        return "caribbean"
    # Cape of Good Hope
    if -36.0 <= lat <= -28.0 and 15.0 <= lon <= 32.0:
        return "cape"
    # Mozambique Channel
    if -28.0 <= lat <= -10.0 and 30.0 <= lon <= 50.0:
        return "mozambique_channel"
    # Arabian Sea
    if 0.0 <= lat <= 30.0 and 40.0 <= lon <= 75.0:
        return "arabian_sea"
    # Indian Ocean (open)
    if -40.0 <= lat <= 0.0 and 40.0 <= lon <= 100.0:
        return "indian_ocean"
    # Malabar coast
    if 8.0 <= lat <= 20.0 and 72.0 <= lon <= 78.0:
        return "malabar"
    # South China Sea
    if 0.0 <= lat <= 25.0 and 100.0 <= lon <= 125.0:
        return "south_china_sea"
    # Japan
    if 25.0 <= lat <= 46.0 and 125.0 <= lon <= 150.0:
        return "japan"
    # Australia / NZ
    if -50.0 <= lat <= -10.0 and 110.0 <= lon <= 180.0:
        return "australia_nz"
    # North Pacific
    if 0.0 <= lat <= 60.0 and 150.0 <= lon <= 180.0:
        return "north_pacific"
    if 0.0 <= lat <= 60.0 and -180.0 <= lon <= -100.0:
        return "north_pacific"
    # South Atlantic
    if -60.0 <= lat <= 0.0 and -70.0 <= lon <= 20.0:
        return "south_atlantic"
    # North Atlantic (catch-all for remaining Atlantic)
    if 0.0 <= lat <= 70.0 and -80.0 <= lon <= -5.0:
        return "north_atlantic"
    return None


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------


def map_loss_cause(circumstances: str | None) -> str:
    """Map UKHO circumstances of loss to our LOSS_CAUSES enum."""
    if not circumstances:
        return "unknown"
    circ = circumstances.lower()
    if any(w in circ for w in ("storm", "gale", "weather", "hurricane", "typhoon", "cyclone")):
        return "storm"
    if any(w in circ for w in ("reef", "rock", "shoal", "coral")):
        return "reef"
    if any(w in circ for w in ("fire", "explosion", "exploded", "burnt")):
        return "fire"
    if any(
        w in circ
        for w in ("action", "war", "torpedo", "mine", "bomb", "enemy", "u-boat", "submarine")
    ):
        return "battle"
    if any(w in circ for w in ("ground", "ashore", "strand", "beached")):
        return "grounding"
    if any(w in circ for w in ("collision", "collided", "struck", "rammed")):
        return "collision"
    if any(w in circ for w in ("scuttled", "sunk deliberately", "abandoned and sunk")):
        return "scuttled"
    return "unknown"


def map_wreck_status(condition: str | None) -> str:
    """Map UKHO condition to our WRECK_STATUSES enum."""
    if not condition:
        return "approximate"
    cond = condition.lower()
    if any(w in cond for w in ("live", "visible", "intact", "located", "surveyed")):
        return "found"
    if any(w in cond for w in ("dead", "dispersed", "removed", "not found")):
        return "unfound"
    return "approximate"


def parse_feature(feature: dict, index: int) -> dict | None:
    """Convert a GeoJSON feature to our wreck record format."""
    props = feature.get("properties", {})
    geometry = feature.get("geometry")

    if not geometry or geometry.get("type") != "Point":
        return None

    coords = geometry.get("coordinates", [])
    if len(coords) < 2:
        return None

    lon, lat = coords[0], coords[1]

    # Extract fields — field names vary by WFS layer configuration
    ship_name = (
        props.get("vesselname")
        or props.get("vessel_name")
        or props.get("name")
        or props.get("shipname")
        or "Unknown"
    )

    loss_date = props.get("date_sunk") or props.get("sink_date") or props.get("sinkyear")
    if loss_date and len(str(loss_date)) == 4:
        loss_date = f"{loss_date}-01-01"  # Year only -> Jan 1

    circumstances = (
        props.get("circumstances") or props.get("sink_context") or props.get("loss_cause")
    )

    condition = props.get("condition") or props.get("status")
    depth_val = props.get("depth") or props.get("least_depth") or props.get("depth_m")
    flag = props.get("flag") or props.get("nationality")
    vessel_type = props.get("vessel_type") or props.get("type") or props.get("ship_type")
    location = props.get("location") or props.get("location_description")

    # Build record
    wreck_id = f"{ARCHIVE}_wreck:{index:05d}"

    depth_m = None
    if depth_val is not None:
        try:
            depth_m = float(depth_val)
        except (ValueError, TypeError):
            pass

    return {
        "wreck_id": wreck_id,
        "ship_name": ship_name,
        "loss_date": loss_date,
        "loss_cause": map_loss_cause(circumstances),
        "loss_location": location,
        "region": classify_region(lat, lon),
        "status": map_wreck_status(condition),
        "position": {"lat": lat, "lon": lon, "uncertainty_km": 1.0},
        "depth_estimate_m": depth_m,
        "flag": flag,
        "vessel_type": vessel_type,
        "archive": ARCHIVE,
    }


# ---------------------------------------------------------------------------
# WFS download
# ---------------------------------------------------------------------------


def fetch_wfs_page(start_index: int, max_features: int) -> dict:
    """Fetch a page of features from EMODnet WFS."""
    url = (
        f"{EMODNET_WFS_BASE}"
        f"?service=WFS&version=2.0.0&request=GetFeature"
        f"&typeNames=emodnet:shipwrecks"
        f"&outputFormat=application/json"
        f"&startIndex={start_index}"
        f"&count={max_features}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_all_features() -> list[dict]:
    """Download all features from EMODnet WFS with pagination."""
    all_features: list[dict] = []
    start_index = 0

    print("  Downloading from EMODnet WFS (paginated)...")
    while True:
        sys.stdout.write(f"\r  Fetching records {start_index}–{start_index + WFS_BATCH_SIZE}...")
        sys.stdout.flush()

        data = fetch_wfs_page(start_index, WFS_BATCH_SIZE)
        features = data.get("features", [])

        if not features:
            break

        all_features.extend(features)
        print(f" got {len(features)} (total: {len(all_features)})")

        if len(features) < WFS_BATCH_SIZE:
            break  # Last page

        start_index += WFS_BATCH_SIZE

    print(f"  Downloaded {len(all_features)} features total")
    return all_features


def main() -> None:
    args = parse_args("Download UKHO Global Wrecks from EMODnet")

    if not args.force and is_cached(WRECKS_OUTPUT, args.cache_max_age):
        print(f"  {WRECKS_OUTPUT.name} is up to date (use --force to re-download)")
        return

    print("UKHO Global Wrecks — EMODnet Download")
    print("=" * 50)

    try:
        features = download_all_features()
    except Exception as e:
        print(f"\n  ERROR: EMODnet WFS download failed: {e}")
        print("  Falling back to curated subset (run generate_ukho.py)")
        sys.exit(1)

    # Convert to our format
    wrecks = []
    skipped = 0
    for i, feature in enumerate(features, start=1):
        record = parse_feature(feature, i)
        if record:
            wrecks.append(record)
        else:
            skipped += 1

    print(f"  Converted {len(wrecks)} wrecks ({skipped} skipped)")

    # Validate
    for w in wrecks:
        assert w["archive"] == ARCHIVE

    save_json(wrecks, WRECKS_OUTPUT.name, compact=True)
    print(f"\n  Done! {len(wrecks)} UKHO wrecks saved to {WRECKS_OUTPUT.name}")


if __name__ == "__main__":
    main()
