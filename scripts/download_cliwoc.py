#!/usr/bin/env python3
"""
Download CLIWOC (Climatological Database for World's Oceans) ship track data.

Downloads the CLIWOC 2.1 Full dataset from HistoricalClimatology.com and
extracts ship positions, voyage metadata, and vessel information for all
nationalities.  The CLIWOC dataset contains ~282K daily logbook observations
from 1662-1855 across European maritime nations.

Source:
    CLIWOC 2.1 -- https://www.historicalclimatology.com/cliwoc.html
    GeoPackage: 182 columns, 282K records

    Fallback (CLIWOC Slim):
    Arribas-Bel, D. "CLIWOC Slim and Routes" (2020)
    https://figshare.com/articles/dataset/CLIWOC_Slim_and_Routes/11941224

Produces:
    data/cliwoc_tracks.json  -- Ship position records grouped by voyage

Usage:
    python scripts/download_cliwoc.py
"""

import json
import logging
import sqlite3
import tempfile
import urllib.request
from pathlib import Path

from download_utils import is_cached, parse_args

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# CLIWOC 2.1 Full GeoPackage (~181 MB)
CLIWOC_FULL_URL = "https://historicalclimatology.com/uploads/4/5/1/4/4514421/cliwoc21.gpkg"
CLIWOC_FULL_SIZE_MB = 181

# Figshare fallback URLs (CLIWOC Slim)
CLIWOC_SLIM_URL = "https://ndownloader.figshare.com/files/21940248"
CLIWOC_ROUTES_URL = "https://ndownloader.figshare.com/files/21940242"


def download_file(url: str, dest: Path, description: str) -> None:
    """Download a file with progress reporting."""
    logger.info("  Downloading %s...", description)
    logger.info("  URL: %s", url)

    def _progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            print(f"\r  {mb:.1f}/{total_mb:.1f} MB ({pct}%)", end="", flush=True)

    urllib.request.urlretrieve(url, str(dest), reporthook=_progress)  # noqa: S310
    print()  # newline after progress
    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info("  Saved: %s (%.1f MB)", dest.name, size_mb)


def _format_das_number(das_raw: float | None) -> str | None:
    """Convert CLIWOC DASnumber float (e.g. 3984.6) to DAS string (e.g. '3984.6')."""
    if das_raw is None or das_raw <= 0:
        return None
    s = f"{das_raw:.1f}"
    # Remove trailing zeros but keep at least one decimal
    if "." in s:
        s = s.rstrip("0")
        if s.endswith("."):
            s += "0"
    return s


# ---------------------------------------------------------------------------
# CLIWOC 2.1 Full extraction
# ---------------------------------------------------------------------------


def extract_full_positions(db_path: Path) -> list[dict]:
    """
    Extract ship positions with metadata from CLIWOC 2.1 Full GeoPackage.

    Returns list of position dicts sorted by (ID, date).
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        """
        SELECT ID, YR, MO, DY, latitude, longitude, C1,
               ShipName, Company, DASnumber, ShipType,
               VoyageFrom, VoyageTo, WindScale, D,
               ShipSpeed, Distance, SST, AT, SLP,
               CMG, Anchored
        FROM CLIWOC21
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY ID, YR, MO, DY
        """
    )

    positions = []
    for row in cursor:
        yr = row["YR"]
        mo = row["MO"]
        dy = row["DY"]

        if yr and mo and dy:
            try:
                date_str = f"{int(yr):04d}-{int(mo):02d}-{int(dy):02d}"
            except (ValueError, TypeError):
                date_str = None
        else:
            date_str = None

        # Wind data: WindScale = Beaufort force (0-12), D = wind direction (1-362)
        wf_raw = row["WindScale"]
        wd_raw = row["D"]
        wf = None
        wd = None
        if wf_raw is not None:
            try:
                wf_int = int(wf_raw)
                if 0 <= wf_int <= 12:
                    wf = wf_int
            except (ValueError, TypeError):
                pass
        if wd_raw is not None:
            try:
                wd_int = int(wd_raw)
                if 1 <= wd_int <= 362:
                    wd = wd_int
            except (ValueError, TypeError):
                pass

        # Environmental observations (None if not recorded)
        def _safe_float(val: object) -> float | None:
            if val is None:
                return None
            try:
                f = float(val)
                return round(f, 1) if f == f else None  # NaN check
            except (ValueError, TypeError):
                return None

        def _safe_int(val: object) -> int | None:
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        ship_speed = _safe_float(row["ShipSpeed"])  # logged speed (knots)
        distance = _safe_float(row["Distance"])  # logged daily distance
        sst = _safe_int(row["SST"])  # sea surface temp (tenths °C ICOADS)
        at = _safe_int(row["AT"])  # air temp (tenths °C ICOADS)
        slp = _safe_int(row["SLP"])  # sea level pressure (tenths hPa ICOADS)
        cmg_raw = row["CMG"]  # course made good (compass text)
        cmg = str(cmg_raw).strip() if cmg_raw else None
        anchored = _safe_int(row["Anchored"])  # 1 = anchored

        positions.append(
            {
                "voyage_id": int(row["ID"]),
                "date": date_str,
                "lat": round(float(row["latitude"]), 4),
                "lon": round(float(row["longitude"]), 4),
                "nationality": row["C1"],
                "year": int(yr) if yr else None,
                # Voyage-level metadata (same for all positions in a voyage)
                "ship_name": row["ShipName"],
                "company": row["Company"],
                "das_number": _format_das_number(row["DASnumber"]),
                "ship_type": row["ShipType"],
                "voyage_from": row["VoyageFrom"],
                "voyage_to": row["VoyageTo"],
                # Wind data
                "wf": wf,
                "wd": wd,
                # Environmental observations
                "ss": ship_speed,
                "dist": distance,
                "sst": sst,
                "at": at,
                "slp": slp,
                "cmg": cmg,
                "anch": anchored,
            }
        )

    conn.close()
    return positions


def group_full_positions_into_tracks(positions: list[dict]) -> list[dict]:
    """
    Group individual position records from CLIWOC 2.1 into voyage tracks.

    Extracts per-voyage metadata (ship_name, company, das_number) from the
    first record in each group.
    """
    voyages: dict[int, list[dict]] = {}
    for pos in positions:
        vid = pos["voyage_id"]
        if vid not in voyages:
            voyages[vid] = []
        voyages[vid].append(pos)

    tracks = []
    for voyage_id, points in sorted(voyages.items()):
        dates = [p["date"] for p in points if p["date"]]
        years = [p["year"] for p in points if p["year"]]
        nationality = points[0]["nationality"] if points else None

        # Extract voyage-level metadata from first record
        first = points[0]
        ship_name = first.get("ship_name")
        company = first.get("company")
        das_number = first.get("das_number")
        ship_type = first.get("ship_type")
        voyage_from = first.get("voyage_from")
        voyage_to = first.get("voyage_to")

        track: dict = {
            "voyage_id": voyage_id,
            "nationality": nationality,
            "ship_name": ship_name,
            "company": company,
            "das_number": das_number,
            "ship_type": ship_type,
            "voyage_from": voyage_from,
            "voyage_to": voyage_to,
            "start_date": min(dates) if dates else None,
            "end_date": max(dates) if dates else None,
            "duration_days": None,
            "year_start": min(years) if years else None,
            "year_end": max(years) if years else None,
            "position_count": len(points),
            "positions": [
                {
                    k: v
                    for k, v in [
                        ("date", p["date"]),
                        ("lat", p["lat"]),
                        ("lon", p["lon"]),
                        ("wf", p.get("wf")),
                        ("wd", p.get("wd")),
                        ("ss", p.get("ss")),
                        ("dist", p.get("dist")),
                        ("sst", p.get("sst")),
                        ("at", p.get("at")),
                        ("slp", p.get("slp")),
                        ("cmg", p.get("cmg")),
                        ("anch", p.get("anch")),
                    ]
                    if v is not None
                }
                for p in points
            ],
        }
        # Compute duration from dates
        if track["start_date"] and track["end_date"] and len(dates) >= 2:
            from datetime import date as dt_date

            try:
                start = dt_date.fromisoformat(track["start_date"])
                end = dt_date.fromisoformat(track["end_date"])
                track["duration_days"] = (end - start).days
            except ValueError:
                pass

        # Remove None values from metadata to keep JSON clean
        track = {k: v for k, v in track.items() if v is not None}
        # Always keep these keys
        for key in ("voyage_id", "position_count", "positions"):
            if key not in track:
                track[key] = points if key == "positions" else 0

        tracks.append(track)

    return tracks


# ---------------------------------------------------------------------------
# CLIWOC Slim fallback extraction
# ---------------------------------------------------------------------------


def extract_slim_positions(db_path: Path) -> list[dict]:
    """Extract positions from CLIWOC Slim GeoPackage (fallback)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        """
        SELECT ID, YR, MO, DY, latitude, longitude, C1
        FROM cliwoc_slim
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY ID, YR, MO, DY
        """
    )

    positions = []
    for row in cursor:
        yr = row["YR"]
        mo = row["MO"]
        dy = row["DY"]

        if yr and mo and dy:
            try:
                date_str = f"{int(yr):04d}-{int(mo):02d}-{int(dy):02d}"
            except (ValueError, TypeError):
                date_str = None
        else:
            date_str = None

        positions.append(
            {
                "voyage_id": int(row["ID"]),
                "date": date_str,
                "lat": round(float(row["latitude"]), 4),
                "lon": round(float(row["longitude"]), 4),
                "nationality": row["C1"],
                "year": int(yr) if yr else None,
            }
        )

    conn.close()
    return positions


def extract_routes(db_path: Path) -> list[dict]:
    """Extract route metadata from CLIWOC Routes GeoPackage."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cursor = conn.execute(
        """
        SELECT ID, start, end, records, C1, length_days
        FROM cliwoc_routes
        ORDER BY start
        """
    )

    routes = []
    for row in cursor:
        routes.append(
            {
                "voyage_id": int(row["ID"]),
                "nationality": row["C1"],
                "start_date": row["start"],
                "end_date": row["end"],
                "record_count": int(row["records"]) if row["records"] else 0,
                "duration_days": int(row["length_days"]) if row["length_days"] else None,
            }
        )

    conn.close()
    return routes


def group_slim_positions_into_tracks(
    positions: list[dict], route_metadata: dict[int, dict]
) -> list[dict]:
    """Group Slim position records into voyage tracks (no vessel metadata)."""
    voyages: dict[int, list[dict]] = {}
    for pos in positions:
        vid = pos["voyage_id"]
        if vid not in voyages:
            voyages[vid] = []
        voyages[vid].append(pos)

    tracks = []
    for voyage_id, points in sorted(voyages.items()):
        dates = [p["date"] for p in points if p["date"]]
        years = [p["year"] for p in points if p["year"]]
        nationality = points[0]["nationality"] if points else None
        meta = route_metadata.get(voyage_id, {})

        track = {
            "voyage_id": voyage_id,
            "nationality": nationality,
            "start_date": meta.get("start_date") or (min(dates) if dates else None),
            "end_date": meta.get("end_date") or (max(dates) if dates else None),
            "duration_days": meta.get("duration_days"),
            "year_start": min(years) if years else None,
            "year_end": max(years) if years else None,
            "position_count": len(points),
            "positions": [{"date": p["date"], "lat": p["lat"], "lon": p["lon"]} for p in points],
        }
        tracks.append(track)

    return tracks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Download CLIWOC ship track data")

    logger.info("=" * 60)
    logger.info("CLIWOC Ship Track Download — chuk-mcp-maritime-archives")
    logger.info("=" * 60)
    logger.info("")

    output_path = DATA_DIR / "cliwoc_tracks.json"
    if not args.force and is_cached(output_path, args.cache_max_age):
        logger.info("Using cached %s (use --force to re-download)", output_path.name)
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tracks: list[dict] = []
    source_name = ""
    source_url = ""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Try CLIWOC 2.1 Full first
        logger.info("Step 1: Downloading CLIWOC 2.1 Full (~%d MB)...", CLIWOC_FULL_SIZE_MB)
        try:
            full_path = Path(tmpdir) / "cliwoc21.gpkg"
            download_file(CLIWOC_FULL_URL, full_path, "CLIWOC 2.1 Full GeoPackage")

            logger.info("")
            logger.info("Step 2: Extracting positions with vessel metadata...")
            positions = extract_full_positions(full_path)
            logger.info("  Found %d position records", len(positions))

            logger.info("")
            logger.info("Step 3: Grouping into voyage tracks...")
            tracks = group_full_positions_into_tracks(positions)
            source_name = "CLIWOC 2.1 Full (HistoricalClimatology.com)"
            source_url = "https://www.historicalclimatology.com/cliwoc.html"

            ships_with_name = sum(1 for t in tracks if t.get("ship_name"))
            ships_with_das = sum(1 for t in tracks if t.get("das_number"))
            all_pos = [p for t in tracks for p in t.get("positions", [])]
            pos_with_wind = sum(1 for p in all_pos if p.get("wf") is not None)
            pos_with_sst = sum(1 for p in all_pos if p.get("sst") is not None)
            pos_with_at = sum(1 for p in all_pos if p.get("at") is not None)
            pos_with_slp = sum(1 for p in all_pos if p.get("slp") is not None)
            pos_with_ss = sum(1 for p in all_pos if p.get("ss") is not None)
            pos_anchored = sum(1 for p in all_pos if p.get("anch") == 1)
            logger.info("  Created %d voyage tracks", len(tracks))
            logger.info("    With ship name: %d", ships_with_name)
            logger.info("    With DAS number: %d (linked to DAS voyages)", ships_with_das)
            logger.info("  Observations with data:")
            logger.info("    Beaufort wind force: %d", pos_with_wind)
            logger.info("    Ship speed (logged): %d", pos_with_ss)
            logger.info("    Sea surface temp:    %d", pos_with_sst)
            logger.info("    Air temperature:     %d", pos_with_at)
            logger.info("    Sea level pressure:  %d", pos_with_slp)
            logger.info("    Anchored:            %d", pos_anchored)

        except Exception as e:
            logger.warning("")
            logger.warning("CLIWOC 2.1 Full download failed: %s", e)
            logger.warning("Falling back to CLIWOC Slim...")
            logger.info("")

            # Fallback: CLIWOC Slim + Routes
            logger.info("Step 1b: Downloading CLIWOC Slim (~37 MB)...")
            slim_path = Path(tmpdir) / "cliwoc_slim.geopackage"
            download_file(CLIWOC_SLIM_URL, slim_path, "CLIWOC Slim GeoPackage")

            logger.info("")
            logger.info("Step 2b: Downloading CLIWOC Routes (~6 MB)...")
            routes_path = Path(tmpdir) / "cliwoc_routes.geopackage"
            download_file(CLIWOC_ROUTES_URL, routes_path, "CLIWOC Routes GeoPackage")

            logger.info("")
            logger.info("Step 3b: Extracting positions...")
            positions = extract_slim_positions(slim_path)
            logger.info("  Found %d position records", len(positions))

            logger.info("")
            logger.info("Step 4b: Extracting route metadata...")
            routes = extract_routes(routes_path)
            route_meta = {r["voyage_id"]: r for r in routes}

            logger.info("")
            logger.info("Step 5b: Grouping into voyage tracks...")
            tracks = group_slim_positions_into_tracks(positions, route_meta)
            source_name = "CLIWOC Slim and Routes (Figshare)"
            source_url = "https://figshare.com/articles/dataset/CLIWOC_Slim_and_Routes/11941224"
            logger.info("  Created %d voyage tracks", len(tracks))

    # Compute stats
    total_positions = sum(t["position_count"] for t in tracks)
    years = [t.get("year_start") for t in tracks if t.get("year_start")]
    min_year = min(years) if years else "?"
    max_year = max(years) if years else "?"

    nat_counts: dict[str, int] = {}
    for t in tracks:
        n = t.get("nationality") or "unknown"
        nat_counts[n] = nat_counts.get(n, 0) + 1

    company_counts: dict[str, int] = {}
    for t in tracks:
        c = t.get("company")
        if c:
            company_counts[c] = company_counts.get(c, 0) + 1

    # Save
    logger.info("")
    logger.info("Step 4: Saving to data/cliwoc_tracks.json...")
    output = {
        "source": source_name,
        "source_url": source_url,
        "description": (
            "Ship position records from the CLIWOC database, "
            "derived from historical ship logbooks. "
            "Covers Dutch, British, Spanish, French, and other European vessels."
        ),
        "nationalities": dict(sorted(nat_counts.items())),
        "companies": dict(sorted(company_counts.items())) if company_counts else None,
        "date_range": f"{min_year}-{max_year}",
        "total_voyages": len(tracks),
        "total_positions": total_positions,
        "tracks": tracks,
    }
    # Remove None from top-level
    output = {k: v for k, v in output.items() if v is not None}

    output_path = DATA_DIR / "cliwoc_tracks.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("  Saved: %s (%.1f MB)", output_path, size_mb)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info("  Source:        %s", source_name)
    logger.info("  Voyages:       %d", len(tracks))
    logger.info("  Positions:     %d", total_positions)
    logger.info("  Years:         %s to %s", min_year, max_year)
    logger.info("  Nationalities: %s", ", ".join(sorted(nat_counts.keys())))
    for nat, count in sorted(nat_counts.items(), key=lambda x: -x[1]):
        logger.info("    %s: %d voyages", nat, count)
    if company_counts:
        logger.info("  Companies:")
        for co, count in sorted(company_counts.items(), key=lambda x: -x[1])[:10]:
            logger.info("    %s: %d voyages", co, count)
    logger.info("  Output:        %s", output_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
