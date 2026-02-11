#!/usr/bin/env python3
"""
Download VOC Opvarenden (crew) data from the enriched Zenodo dataset.

Downloads the "Dutch East India Company's Eighteenth-Century Workforce"
enriched dataset from Zenodo, which contains 774,200 muster records
(1633-1794) across 8 CSV files.  Joins contracts, names, ranks, voyages,
and places into a single crew.json file for the MCP server.

Source:
    Zenodo record 10599528
    https://zenodo.org/records/10599528
    DOI: 10.5281/zenodo.10599528

    Original: Nationaal Archief index nt00444
    https://www.nationaalarchief.nl/onderzoeken/index/nt00444

Produces:
    data/crew.json  -- ~774,200 crew records (compact JSON, ~80 MB)

Usage:
    python scripts/download_crew.py
    python scripts/download_crew.py --force
"""

import csv
import io
import json
import logging
import sys
import urllib.request
import zipfile
from pathlib import Path

from download_utils import (
    CACHE_DIR,
    DATA_DIR,
    USER_AGENT,
    ensure_cache_dir,
    is_cached,
    parse_args,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

# Zenodo enriched dataset (preferred — 8 CSV files, ~300 MB ZIP)
ZENODO_RECORD = "10599528"
ZENODO_API = f"https://zenodo.org/api/records/{ZENODO_RECORD}"

# Nationaal Archief bulk download (fallback — 626 MB ZIP)
NA_DOWNLOAD_URL = "https://www.nationaalarchief.nl/onderzoeken/index/nt00444/download/csv"

# Output
OUTPUT = DATA_DIR / "crew.json"
CACHE_ZIP = CACHE_DIR / "voc_opvarenden_zenodo.zip"

# CSV file names inside the Zenodo ZIP
CSV_CONTRACTS = "voc_persons_contracts.csv"
CSV_NAMES = "voc_names.csv"
CSV_RANKS = "voc_ranks.csv"
CSV_VOYAGES = "voc_voyages.csv"
CSV_PLACES = "voc_places.csv"

# Service end reason mappings
SERVICE_END_MAP = {
    # could_muster_again values and context-based mapping
    "yes": "returned",
    "no": "died_voyage",
    "desertion": "deserted",
    "discharged": "discharged",
    "died": "died_voyage",
    "died in asia": "died_asia",
}


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------


def _download_zenodo_zip(dest: Path) -> Path:
    """Download the Zenodo dataset ZIP file."""
    logger.info("Step 1: Fetching Zenodo record metadata...")
    req = urllib.request.Request(ZENODO_API, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        record = json.loads(resp.read().decode("utf-8"))

    # Find the ZIP file in the record's files
    files = record.get("files", [])
    zip_url = None
    for f in files:
        name = f.get("key", "") or f.get("filename", "")
        if name.endswith(".zip"):
            zip_url = f.get("links", {}).get("self") or f.get("links", {}).get("download")
            break

    if not zip_url:
        # Try direct file listing from newer Zenodo API format
        file_entries = record.get("files", {}).get("entries", {})
        for name, entry in file_entries.items():
            if name.endswith(".zip"):
                zip_url = entry.get("links", {}).get("self") or entry.get("links", {}).get(
                    "content"
                )
                break

    if not zip_url:
        raise RuntimeError(
            f"No ZIP file found in Zenodo record {ZENODO_RECORD}. "
            f"Available files: {[f.get('key', f.get('filename', '?')) for f in files]}"
        )

    logger.info("  Found: %s", zip_url)
    logger.info("")
    logger.info("Step 2: Downloading ZIP (~300 MB)...")

    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(zip_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=600) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 65536
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    mb = downloaded / (1024 * 1024)
                    sys.stdout.write(f"\r  {mb:.1f} / {total / (1024 * 1024):.1f} MB ({pct:.0f}%)")
                else:
                    sys.stdout.write(f"\r  {downloaded / (1024 * 1024):.1f} MB")
                sys.stdout.flush()
    print()
    logger.info("  Saved %s (%.1f MB)", dest.name, dest.stat().st_size / (1024 * 1024))
    return dest


def _read_csv_from_zip(zf: zipfile.ZipFile, filename: str) -> list[dict]:
    """Read a CSV file from inside the ZIP, handling nested directories."""
    # Find the file — it might be in a subdirectory
    matching = [n for n in zf.namelist() if n.endswith(filename)]
    if not matching:
        raise FileNotFoundError(f"{filename} not found in ZIP. Contents: {zf.namelist()[:20]}...")
    path_in_zip = matching[0]
    logger.info("  Reading %s ...", path_in_zip)

    with zf.open(path_in_zip) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8")
        reader = csv.DictReader(text)
        return list(reader)


# ---------------------------------------------------------------------------
# Data processing
# ---------------------------------------------------------------------------


def _build_name_lookup(names_rows: list[dict]) -> dict[str, str]:
    """Build vocop_id → full_name mapping from names CSV."""
    lookup: dict[str, str] = {}
    for row in names_rows:
        vocop_id = row.get("vocop_id", "").strip()
        if not vocop_id:
            continue
        # Prefer normalized full name, fall back to building from parts
        full = row.get("full_name_normalized", "").strip()
        if not full:
            parts = [
                row.get("first_name_normalized", ""),
                row.get("patronymic_normalized", ""),
                row.get("family_name_prefix_normalized", ""),
                row.get("family_name_normalized", ""),
            ]
            full = " ".join(p.strip() for p in parts if p.strip())
        if full:
            lookup[vocop_id] = full
    return lookup


def _build_rank_lookup(ranks_rows: list[dict]) -> dict[str, dict]:
    """Build rank_id → rank info mapping."""
    lookup: dict[str, dict] = {}
    for row in ranks_rows:
        rank_id = row.get("rank_id", "").strip()
        if rank_id:
            lookup[rank_id] = {
                "rank": row.get("rank", "").strip(),
                "rank_nl": row.get("rank_nl", "").strip(),
                "category": row.get("category", "").strip(),
            }
    return lookup


def _build_voyage_lookup(voyages_rows: list[dict]) -> dict[str, dict]:
    """Build das_voyage_id → voyage info mapping."""
    lookup: dict[str, dict] = {}
    for row in voyages_rows:
        das_id = row.get("das_voyage_id", "").strip()
        if das_id:
            lookup[das_id] = {
                "ship_name": row.get("ship_name", "").strip(),
                "chamber": row.get("chamber", "").strip(),
                "departure_date": row.get("departure_date", "").strip(),
            }
    return lookup


def _build_place_lookup(places_rows: list[dict]) -> dict[str, str]:
    """Build place_id → place_name mapping."""
    lookup: dict[str, str] = {}
    for row in places_rows:
        place_id = row.get("place_id", "").strip()
        name = row.get("place_normalized", "").strip() or row.get("place_original", "").strip()
        if place_id and name:
            lookup[place_id] = name
    return lookup


def _map_service_end(row: dict) -> str:
    """Map contract data to a service_end_reason value."""
    # Check location_end_contract for hints
    location = (row.get("location_end_contract") or "").lower().strip()
    could_muster = (row.get("could_muster_again") or "").lower().strip()

    if could_muster in SERVICE_END_MAP:
        return SERVICE_END_MAP[could_muster]

    # Infer from location
    if any(w in location for w in ("patria", "holland", "nederland", "amsterdam", "texel")):
        return "returned"
    if any(w in location for w in ("batavia", "bengalen", "ceylon", "malacca", "banda")):
        return "died_asia"
    if "deserted" in location or "gedeserteerd" in location:
        return "deserted"
    if any(w in location for w in ("died", "overleden", "gestorven")):
        return "died_voyage"

    # Default: returned if could muster again, otherwise unknown
    if could_muster == "1" or could_muster == "true":
        return "returned"
    return "discharged"


def _format_das_voyage_id(raw_id: str) -> str | None:
    """Convert a DAS voyage ID to the das:NNNN.N format used by DASClient."""
    raw = raw_id.strip()
    if not raw:
        return None
    # The DAS IDs might be numeric or already formatted
    # Try to match pattern like "1234.1" → "das:1234.1"
    if "." in raw:
        return f"das:{raw}"
    # Bare number → assume outward voyage (.1)
    try:
        num = int(raw)
        return f"das:{num:04d}.1"
    except ValueError:
        return f"das:{raw}"


def build_crew_records(
    contracts: list[dict],
    names: dict[str, str],
    ranks: dict[str, dict],
    voyages: dict[str, dict],
    places: dict[str, str],
) -> list[dict]:
    """Build the final crew.json records from joined data."""
    records = []
    for i, row in enumerate(contracts, 1):
        vocop_id = row.get("vocop_id", "").strip()

        # Name
        name = names.get(vocop_id, "")

        # Rank
        rank_id = row.get("rank_id", "").strip()
        rank_corrected = row.get("rank_corrected", "").strip()
        rank_info = ranks.get(rank_id, {})
        rank = rank_corrected or rank_info.get("rank", "")

        # Voyage and ship
        outward_id = row.get("outward_voyage_id", "").strip()
        voyage_info = voyages.get(outward_id, {})
        ship_name = voyage_info.get("ship_name", "")
        voyage_id = _format_das_voyage_id(outward_id)

        # Origin
        place_id = row.get("place_id", "").strip()
        origin_raw = row.get("place_of_origin", "").strip()
        origin = places.get(place_id, origin_raw)

        # Dates
        embark_date = row.get("date_begin_contract", "").strip() or None

        # Service end
        service_end = _map_service_end(row)

        record = {
            "crew_id": f"voc_crew:{i:06d}",
            "name": name,
            "rank": rank,
            "ship_name": ship_name,
            "voyage_id": voyage_id,
            "origin": origin,
            "embarkation_date": embark_date,
            "service_end_reason": service_end,
        }
        records.append(record)

        if i % 100000 == 0:
            logger.info("  Processed %d / %d records ...", i, len(contracts))

    return records


# ---------------------------------------------------------------------------
# Fallback: Nationaal Archief download
# ---------------------------------------------------------------------------


def _try_nationaalarchief(cache_path: Path) -> list[dict] | None:
    """Try downloading from the Nationaal Archief as fallback."""
    logger.info("")
    logger.info("Fallback: Trying Nationaal Archief bulk download...")
    logger.info("  %s", NA_DOWNLOAD_URL)

    try:
        req = urllib.request.Request(NA_DOWNLOAD_URL, headers={"User-Agent": USER_AGENT})
        na_zip_path = cache_path.parent / "voc_opvarenden_na.zip"
        with urllib.request.urlopen(req, timeout=600) as resp:
            na_zip_path.write_bytes(resp.read())

        logger.info(
            "  Downloaded %s (%.1f MB)",
            na_zip_path.name,
            na_zip_path.stat().st_size / (1024 * 1024),
        )

        # The NA ZIP contains a single large CSV
        with zipfile.ZipFile(na_zip_path) as zf:
            csv_files = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_files:
                logger.warning("  No CSV files found in NA ZIP")
                return None

            records = []
            for csv_name in csv_files:
                rows = _read_csv_from_zip(zf, csv_name.split("/")[-1])
                for i, row in enumerate(rows, len(records) + 1):
                    # NA CSV has different column names — map as best we can
                    name = (row.get("Voornaam", "") + " " + row.get("Achternaam", "")).strip()
                    record = {
                        "crew_id": f"voc_crew:{i:06d}",
                        "name": name or row.get("Naam", ""),
                        "rank": row.get("Rang", row.get("Functie", "")),
                        "ship_name": row.get("Schip", row.get("Scheepsnaam", "")),
                        "voyage_id": None,
                        "origin": row.get("Herkomst", row.get("Geboorteplaats", "")),
                        "embarkation_date": row.get("Datum_indiensttreding", None),
                        "service_end_reason": "discharged",
                    }
                    records.append(record)
            return records
    except Exception as e:
        logger.warning("  Nationaal Archief download failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Download VOC Opvarenden (crew) data")

    logger.info("=" * 60)
    logger.info("VOC Crew Download — chuk-mcp-maritime-archives")
    logger.info("=" * 60)
    logger.info("")

    if not args.force and is_cached(OUTPUT, args.cache_max_age):
        logger.info("Using cached %s (use --force to re-download)", OUTPUT.name)
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_cache_dir()

    # Try Zenodo enriched dataset first
    records = None
    try:
        # Download ZIP if not cached
        if not args.force and CACHE_ZIP.exists() and CACHE_ZIP.stat().st_size > 0:
            logger.info("Using cached ZIP: %s", CACHE_ZIP.name)
        else:
            _download_zenodo_zip(CACHE_ZIP)

        logger.info("")
        logger.info("Step 3: Parsing CSV files from ZIP...")

        with zipfile.ZipFile(CACHE_ZIP) as zf:
            # Load lookup tables first (smaller files)
            names_rows = _read_csv_from_zip(zf, CSV_NAMES)
            names = _build_name_lookup(names_rows)
            logger.info("    %d name records", len(names))
            del names_rows  # free memory

            ranks_rows = _read_csv_from_zip(zf, CSV_RANKS)
            ranks = _build_rank_lookup(ranks_rows)
            logger.info("    %d rank records", len(ranks))
            del ranks_rows

            voyages_rows = _read_csv_from_zip(zf, CSV_VOYAGES)
            voyages = _build_voyage_lookup(voyages_rows)
            logger.info("    %d voyage records", len(voyages))
            del voyages_rows

            places_rows = _read_csv_from_zip(zf, CSV_PLACES)
            places = _build_place_lookup(places_rows)
            logger.info("    %d place records", len(places))
            del places_rows

            # Load main contracts file
            contracts = _read_csv_from_zip(zf, CSV_CONTRACTS)
            logger.info("    %d contract records", len(contracts))

        logger.info("")
        logger.info("Step 4: Building crew records (joining tables)...")
        records = build_crew_records(contracts, names, ranks, voyages, places)
        del contracts, names, ranks, voyages, places

    except Exception as e:
        logger.warning("Zenodo download failed: %s", e)
        records = _try_nationaalarchief(CACHE_ZIP)

    if not records:
        logger.error("ERROR: Could not download crew data from any source.")
        logger.error("  Try running with --force or check network connectivity.")
        sys.exit(1)

    # Save
    logger.info("")
    logger.info("Step 5: Saving crew.json (%d records, compact JSON)...", len(records))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    logger.info("  %s (%.1f MB)", OUTPUT, size_mb)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info("  Total crew records: %d", len(records))

    # Count by service_end_reason
    fates: dict[str, int] = {}
    for r in records:
        f = r.get("service_end_reason", "unknown")
        fates[f] = fates.get(f, 0) + 1
    for fate, count in sorted(fates.items(), key=lambda x: -x[1]):
        logger.info("    %s: %d", fate, count)

    # Count with voyage_id
    linked = sum(1 for r in records if r.get("voyage_id"))
    logger.info("  Linked to DAS voyages: %d (%.1f%%)", linked, linked / len(records) * 100)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
