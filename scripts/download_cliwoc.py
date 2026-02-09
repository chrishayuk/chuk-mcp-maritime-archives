#!/usr/bin/env python3
"""
Download CLIWOC (Climatological Database for World's Oceans) ship track data.

Downloads the CLIWOC Slim dataset from Figshare and extracts ship
positions and voyage tracks for all nationalities.  The CLIWOC dataset
contains ~261K daily logbook observations from 1662-1855 across eight
European maritime nations: NL (Dutch), UK, ES (Spanish), FR (French),
SE (Swedish), US, DE (German), DK (Danish).

Source:
    Arribas-Bel, D. "CLIWOC Slim and Routes" (2020)
    https://figshare.com/articles/dataset/CLIWOC_Slim_and_Routes/11941224

    Original CLIWOC 2.1:
    https://www.historicalclimatology.com/cliwoc.html

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

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Figshare direct download URLs
CLIWOC_SLIM_URL = "https://ndownloader.figshare.com/files/21940248"
CLIWOC_ROUTES_URL = "https://ndownloader.figshare.com/files/21940242"

# File sizes for progress reporting (approximate)
CLIWOC_SLIM_SIZE_MB = 37
CLIWOC_ROUTES_SIZE_MB = 6


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

    urllib.request.urlretrieve(url, str(dest), reporthook=_progress)
    print()  # newline after progress
    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info("  Saved: %s (%.1f MB)", dest.name, size_mb)


def extract_positions(db_path: Path) -> list[dict]:
    """
    Extract all ship positions from CLIWOC Slim GeoPackage.

    Returns list of position dicts sorted by (ID, date).
    """
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

        # Format date safely
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
    """
    Extract all route metadata from CLIWOC Routes GeoPackage.

    Returns route summary dicts (without geometry — just metadata).
    """
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


def group_positions_into_tracks(
    positions: list[dict], route_metadata: dict[int, dict]
) -> list[dict]:
    """
    Group individual position records into voyage tracks.

    Each track has metadata (start/end date, duration, nationality) and
    a list of dated positions.
    """
    # Group by voyage_id
    voyages: dict[int, list[dict]] = {}
    for pos in positions:
        vid = pos["voyage_id"]
        if vid not in voyages:
            voyages[vid] = []
        voyages[vid].append(pos)

    tracks = []
    for voyage_id, points in sorted(voyages.items()):
        # Get dates for this track
        dates = [p["date"] for p in points if p["date"]]
        years = [p["year"] for p in points if p["year"]]

        # Determine nationality from first point
        nationality = points[0]["nationality"] if points else None

        # Get route metadata if available
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


def main() -> None:
    logger.info("=" * 60)
    logger.info("CLIWOC Ship Track Download — chuk-mcp-maritime-archives")
    logger.info("=" * 60)
    logger.info("")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Download CLIWOC Slim GeoPackage
    logger.info("Step 1: Downloading CLIWOC Slim (~%d MB)...", CLIWOC_SLIM_SIZE_MB)
    with tempfile.TemporaryDirectory() as tmpdir:
        slim_path = Path(tmpdir) / "cliwoc_slim.geopackage"
        download_file(CLIWOC_SLIM_URL, slim_path, "CLIWOC Slim GeoPackage")

        # Step 2: Download CLIWOC Routes GeoPackage
        logger.info("")
        logger.info("Step 2: Downloading CLIWOC Routes (~%d MB)...", CLIWOC_ROUTES_SIZE_MB)
        routes_path = Path(tmpdir) / "cliwoc_routes.geopackage"
        download_file(CLIWOC_ROUTES_URL, routes_path, "CLIWOC Routes GeoPackage")

        # Step 3: Extract positions
        logger.info("")
        logger.info("Step 3: Extracting ship positions...")
        positions = extract_positions(slim_path)
        logger.info("  Found %d position records", len(positions))

        # Step 4: Extract route metadata
        logger.info("")
        logger.info("Step 4: Extracting route metadata...")
        routes = extract_routes(routes_path)
        logger.info("  Found %d voyage routes", len(routes))

    # Step 5: Group into tracks
    logger.info("")
    logger.info("Step 5: Grouping positions into voyage tracks...")
    route_meta = {r["voyage_id"]: r for r in routes}
    tracks = group_positions_into_tracks(positions, route_meta)
    logger.info("  Created %d voyage tracks", len(tracks))

    # Compute stats
    total_positions = sum(t["position_count"] for t in tracks)
    years = [t["year_start"] for t in tracks if t["year_start"]]
    min_year = min(years) if years else "?"
    max_year = max(years) if years else "?"

    # Nationality breakdown
    nat_counts: dict[str, int] = {}
    for t in tracks:
        n = t["nationality"] or "unknown"
        nat_counts[n] = nat_counts.get(n, 0) + 1

    # Step 6: Save
    logger.info("")
    logger.info("Step 6: Saving to data/cliwoc_tracks.json...")
    output = {
        "source": "CLIWOC Slim and Routes (Figshare)",
        "source_url": "https://figshare.com/articles/dataset/CLIWOC_Slim_and_Routes/11941224",
        "description": (
            "Ship position records from the CLIWOC database, "
            "derived from historical ship logbooks (1662-1855). "
            "Covers Dutch, British, Spanish, French, Swedish, "
            "American, German, and Danish vessels."
        ),
        "nationalities": dict(sorted(nat_counts.items())),
        "date_range": f"{min_year}-{max_year}",
        "total_voyages": len(tracks),
        "total_positions": total_positions,
        "tracks": tracks,
    }

    output_path = DATA_DIR / "cliwoc_tracks.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("  Saved: %s (%.1f MB)", output_path, size_mb)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info("  Voyages:       %d", len(tracks))
    logger.info("  Positions:     %d", total_positions)
    logger.info("  Years:         %s to %s", min_year, max_year)
    logger.info("  Nationalities: %s", ", ".join(sorted(nat_counts.keys())))
    for nat, count in sorted(nat_counts.items(), key=lambda x: -x[1]):
        logger.info("    %s: %d voyages", nat, count)
    logger.info("  Output:        %s", output_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
