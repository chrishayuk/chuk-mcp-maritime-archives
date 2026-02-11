#!/usr/bin/env python3
"""
Download VOC cargo manifest data from the BGB (Boekhouder-Generaal Batavia).

Attempts to fetch cargo records from the Huygens Institute BGB database,
which contains ~18,000 voyages with 250,000+ product references covering
3,000+ distinct commodities traded by the VOC (1700-1795).

Sources (tried in order):
    1. Huygens BGB CSV export (bgb.resources.huygens.knaw.nl)
    2. GitHub "Wind in our Sails" project CSV data
    3. Fallback: expanded curated generation from generate_cargo.py

Produces:
    data/cargo.json  -- VOC cargo manifest records

Usage:
    python scripts/download_cargo.py
    python scripts/download_cargo.py --force
"""

import csv
import io
import json
import logging
import re
import sys
import urllib.request
from pathlib import Path

from download_utils import (
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

# Huygens BGB — try CSV export like DAS has
BGB_BASE = "https://bgb.resources.huygens.knaw.nl"
BGB_VOYAGES_CSV = f"{BGB_BASE}/voyages_results.csv"
BGB_CARGO_CSV = f"{BGB_BASE}/cargo_results.csv"

# Alternative Huygens URL patterns
BGB_ALT_BASE = "https://resources.huygens.knaw.nl/bgb"
BGB_ALT_CSV = f"{BGB_ALT_BASE}/cargo.csv"

# GitHub Wind in our Sails project
GITHUB_RAW = "https://raw.githubusercontent.com/stijnschout3n/thewindinoursails/main"

OUTPUT = DATA_DIR / "cargo.json"

# ---------------------------------------------------------------------------
# Commodity name mapping (Dutch → English)
# ---------------------------------------------------------------------------

DUTCH_TO_ENGLISH = {
    "peper": "pepper",
    "nootmuskaat": "nutmeg",
    "foelie": "mace",
    "kruidnagelen": "cloves",
    "kaneel": "cinnamon",
    "thee": "tea",
    "koffie": "coffee",
    "suiker": "sugar",
    "zijde": "silk",
    "katoen": "cotton",
    "porselein": "porcelain",
    "tin": "tin",
    "koper": "copper",
    "lood": "lead",
    "zilver": "silver",
    "goud": "gold",
    "rijst": "rice",
    "salpeter": "saltpeter",
    "indigo": "indigo",
    "opium": "opium",
    "kamfer": "camphor",
    "sandelhout": "sandalwood",
    "lak": "lacquer",
    "wijn": "wine",
    "textiel": "textiles",
    "arak": "arrack",
    "diamanten": "diamonds",
    "ivoor": "ivory",
}


# ---------------------------------------------------------------------------
# Download strategies
# ---------------------------------------------------------------------------


def _fetch_url(url: str, timeout: int = 120) -> str | None:
    """Fetch URL content, return None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        logger.info("    Failed: %s", e)
        return None


def _try_huygens_csv() -> list[dict] | None:
    """Try to download cargo data from Huygens BGB CSV export."""
    logger.info("Strategy 1: Huygens BGB CSV export...")

    for url in [BGB_CARGO_CSV, BGB_VOYAGES_CSV, BGB_ALT_CSV]:
        logger.info("  Trying %s", url)
        content = _fetch_url(url)
        if content and len(content) > 500:
            logger.info("  Got %d bytes", len(content))
            try:
                return _parse_huygens_csv(content)
            except Exception as e:
                logger.info("  Parse failed: %s", e)

    logger.info("  No Huygens CSV available")
    return None


def _parse_huygens_csv(content: str) -> list[dict]:
    """Parse Huygens BGB CSV into cargo records."""
    # BGB CSV uses semicolons like DAS
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    records = []
    for i, row in enumerate(reader, 1):
        # Map BGB columns to our schema
        commodity_nl = (row.get("Product", "") or row.get("product", "")).strip()
        commodity = DUTCH_TO_ENGLISH.get(commodity_nl.lower(), commodity_nl)

        record = {
            "cargo_id": f"voc_cargo:{i:06d}",
            "voyage_id": _map_voyage_id(row),
            "commodity": commodity,
            "commodity_dutch": commodity_nl,
            "quantity": (row.get("Quantity", "") or row.get("quantity", "")).strip(),
            "quantity_kg": _parse_quantity_kg(row),
            "origin": (row.get("Departure", "") or row.get("departure", "")).strip(),
            "destination": (row.get("Arrival", "") or row.get("arrival", "")).strip(),
            "date": _parse_date(row),
            "value_guilders": _parse_value(row),
            "notes": (row.get("Remarks", "") or row.get("specification", "")).strip(),
        }
        records.append(record)
    return records


def _try_github_csv() -> list[dict] | None:
    """Try to get CSV data from the Wind in our Sails GitHub project."""
    logger.info("")
    logger.info("Strategy 2: GitHub Wind in our Sails project...")

    # Try common CSV locations in the repo
    paths = [
        "data/bgb_cargo.csv",
        "data/input/bgb_cargo.csv",
        "data/bgb_voyages.csv",
        "csv/bgb_cargo.csv",
    ]
    for path in paths:
        url = f"{GITHUB_RAW}/{path}"
        logger.info("  Trying %s", path)
        content = _fetch_url(url, timeout=60)
        if content and len(content) > 500 and "," in content[:200]:
            logger.info("  Got %d bytes", len(content))
            try:
                reader = csv.DictReader(io.StringIO(content))
                records = []
                for i, row in enumerate(reader, 1):
                    record = _map_github_row(i, row)
                    if record:
                        records.append(record)
                if records:
                    return records
            except Exception as e:
                logger.info("  Parse failed: %s", e)

    logger.info("  No GitHub data available")
    return None


def _map_github_row(idx: int, row: dict) -> dict | None:
    """Map a GitHub CSV row to our cargo schema."""
    # Try various column name patterns
    commodity = ""
    for key in ("product", "Product", "commodity", "Commodity", "item", "Item"):
        if key in row and row[key].strip():
            commodity = row[key].strip()
            break
    if not commodity:
        return None

    return {
        "cargo_id": f"voc_cargo:{idx:06d}",
        "voyage_id": _map_voyage_id(row),
        "commodity": commodity,
        "commodity_dutch": "",
        "quantity": row.get("quantity", row.get("Quantity", "")),
        "quantity_kg": _parse_quantity_kg(row),
        "origin": row.get("origin", row.get("Origin", row.get("departure", ""))),
        "destination": row.get("destination", row.get("Destination", row.get("arrival", ""))),
        "date": _parse_date(row),
        "value_guilders": _parse_value(row),
        "notes": row.get("notes", row.get("remarks", row.get("specification", ""))),
    }


def _use_curated_fallback() -> list[dict]:
    """Fall back to the curated generate_cargo.py script."""
    logger.info("")
    logger.info("Strategy 3: Curated cargo generation (fallback)...")
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from generate_cargo import build_cargo

        records = build_cargo()
        logger.info("  Generated %d curated cargo records", len(records))
        return records
    except ImportError:
        logger.error("  generate_cargo.py not found!")
        return []


# ---------------------------------------------------------------------------
# Field parsers
# ---------------------------------------------------------------------------


def _map_voyage_id(row: dict) -> str | None:
    """Extract and format a DAS voyage ID from a CSV row."""
    for key in ("voyage_id", "VoyageId", "das_id", "DasId", "voyage_number"):
        val = (row.get(key) or "").strip()
        if val:
            if val.startswith("das:"):
                return val
            try:
                num = int(val)
                return f"das:{num:04d}.1"
            except ValueError:
                if "." in val:
                    return f"das:{val}"
    return None


def _parse_date(row: dict) -> str | None:
    """Extract a date from various column names."""
    for key in ("date", "Date", "departure_date", "DepartureDate"):
        val = (row.get(key) or "").strip()
        if val and re.match(r"\d{4}", val):
            return val
    return None


def _parse_value(row: dict) -> int:
    """Extract monetary value in guilders."""
    for key in ("value_guilders", "value", "Value", "total_value", "TotalValue"):
        val = (row.get(key) or "").strip()
        if val:
            try:
                return int(float(val.replace(",", "")))
            except ValueError:
                pass
    return 0


def _parse_quantity_kg(row: dict) -> int:
    """Extract quantity in kg."""
    for key in ("quantity_kg", "weight_kg", "WeightKg"):
        val = (row.get(key) or "").strip()
        if val:
            try:
                return int(float(val.replace(",", "")))
            except ValueError:
                pass
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Download BGB cargo manifest data")

    logger.info("=" * 60)
    logger.info("BGB Cargo Download — chuk-mcp-maritime-archives")
    logger.info("=" * 60)
    logger.info("")

    if not args.force and is_cached(OUTPUT, args.cache_max_age):
        logger.info("Using cached %s (use --force to re-download)", OUTPUT.name)
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_cache_dir()

    # Try each strategy in order
    records = _try_huygens_csv()

    if not records:
        records = _try_github_csv()

    if not records:
        records = _use_curated_fallback()

    if not records:
        logger.error("ERROR: Could not obtain cargo data from any source.")
        sys.exit(1)

    # Save
    logger.info("")
    logger.info("Step: Saving cargo.json (%d records)...", len(records))
    compact = len(records) > 5000  # Use compact JSON for large datasets
    with open(OUTPUT, "w", encoding="utf-8") as f:
        if compact:
            json.dump(records, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(records, f, ensure_ascii=False, indent=2)
    size_kb = OUTPUT.stat().st_size / 1024
    logger.info("  %s (%.0f KB)", OUTPUT, size_kb)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info("  Total cargo records: %d", len(records))

    commodities: dict[str, int] = {}
    for r in records:
        c = r.get("commodity", "unknown")
        commodities[c] = commodities.get(c, 0) + 1
    top = sorted(commodities.items(), key=lambda x: -x[1])[:10]
    logger.info("  Top commodities: %s", ", ".join(f"{c} ({n})" for c, n in top))

    linked = sum(1 for r in records if r.get("voyage_id"))
    logger.info("  Linked to DAS voyages: %d", linked)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
