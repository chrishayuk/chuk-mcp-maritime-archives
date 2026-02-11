#!/usr/bin/env python3
"""
Download English East India Company (EIC) voyage and wreck data.

Attempts to fetch structured EIC voyage records from available online
databases, then falls back to the curated generate_eic.py dataset.

Sources (tried in order):
    1. ThreeDecks EIC Ships database (eicships.threedecks.org)
    2. Fallback: curated generation from generate_eic.py

Produces:
    data/eic_voyages.json  -- EIC voyage records
    data/eic_wrecks.json   -- EIC wreck records

Usage:
    python scripts/download_eic.py
    python scripts/download_eic.py --force
"""

import json
import logging
import sys
import urllib.request
from html.parser import HTMLParser
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

THREEDECKS_BASE = "https://eicships.threedecks.org"

VOYAGES_OUTPUT = DATA_DIR / "eic_voyages.json"
WRECKS_OUTPUT = DATA_DIR / "eic_wrecks.json"


# ---------------------------------------------------------------------------
# ThreeDecks HTML scraper
# ---------------------------------------------------------------------------


class ShipListParser(HTMLParser):
    """Extract ship names and IDs from ThreeDecks ship list pages."""

    def __init__(self):
        super().__init__()
        self.ships: list[dict] = []
        self._in_link = False
        self._current_href = ""
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if "/ship" in href or "/vessel" in href:
                self._in_link = True
                self._current_href = href
                self._current_text = ""

    def handle_data(self, data):
        if self._in_link:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self._in_link = False
            name = self._current_text.strip()
            if name and self._current_href:
                self.ships.append(
                    {
                        "name": name,
                        "url": self._current_href,
                    }
                )


def _fetch_page(url: str, timeout: int = 30) -> str | None:
    """Fetch a web page, return None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.debug("  Fetch failed for %s: %s", url, e)
        return None


def _try_threedecks() -> tuple[list[dict], list[dict]] | None:
    """Try to scrape EIC voyage data from ThreeDecks."""
    logger.info("Strategy 1: ThreeDecks EIC Ships database...")
    logger.info("  %s", THREEDECKS_BASE)

    # Test if the site is accessible
    html = _fetch_page(THREEDECKS_BASE, timeout=15)
    if not html or len(html) < 500:
        logger.info("  Site not accessible or returned minimal content")
        return None

    logger.info("  Site accessible (%d bytes)", len(html))
    logger.info("  Note: Full scraping of ThreeDecks requires further development.")
    logger.info("  For now, using curated data as primary source.")

    # ThreeDecks scraping is complex (multi-page, JavaScript-rendered)
    # and potentially against ToS. We acknowledge the source but
    # use curated data that was compiled from published references
    # including Hardy's Register and Farrington's Catalogue.
    return None


# ---------------------------------------------------------------------------
# Curated fallback
# ---------------------------------------------------------------------------


def _use_curated_fallback() -> tuple[list[dict], list[dict]]:
    """Fall back to the curated generate_eic.py script."""
    logger.info("")
    logger.info("Strategy 2: Curated EIC generation (from published sources)...")

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from generate_eic import build_voyages, build_wrecks

        voyages = build_voyages()
        wrecks = build_wrecks()
        logger.info(
            "  Generated %d voyages, %d wrecks from Hardy/Farrington data",
            len(voyages),
            len(wrecks),
        )
        return voyages, wrecks
    except ImportError as e:
        logger.error("  generate_eic.py not found: %s", e)
        return [], []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Download English East India Company (EIC) data")

    logger.info("=" * 60)
    logger.info("EIC Data Download — chuk-mcp-maritime-archives")
    logger.info("=" * 60)
    logger.info("")

    if not args.force and is_cached(VOYAGES_OUTPUT, args.cache_max_age):
        logger.info("Using cached %s (use --force to re-download)", VOYAGES_OUTPUT.name)
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_cache_dir()

    # Try each strategy
    result = _try_threedecks()

    if result:
        voyages, wrecks = result
    else:
        voyages, wrecks = _use_curated_fallback()

    if not voyages:
        logger.error("ERROR: Could not obtain EIC data from any source.")
        sys.exit(1)

    # Save voyages
    logger.info("")
    logger.info("Saving %d voyages to %s ...", len(voyages), VOYAGES_OUTPUT.name)
    with open(VOYAGES_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(voyages, f, indent=2, ensure_ascii=False)
    logger.info("  %s (%d bytes)", VOYAGES_OUTPUT.name, VOYAGES_OUTPUT.stat().st_size)

    # Save wrecks
    logger.info("Saving %d wrecks to %s ...", len(wrecks), WRECKS_OUTPUT.name)
    with open(WRECKS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(wrecks, f, indent=2, ensure_ascii=False)
    logger.info("  %s (%d bytes)", WRECKS_OUTPUT.name, WRECKS_OUTPUT.stat().st_size)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary:")
    logger.info("  EIC voyages: %d", len(voyages))
    logger.info("  EIC wrecks: %d", len(wrecks))

    fates: dict[str, int] = {}
    for v in voyages:
        f = v.get("fate", "unknown")
        fates[f] = fates.get(f, 0) + 1
    logger.info("  Fates: %s", fates)

    dates = [v["departure_date"] for v in voyages if v.get("departure_date")]
    if dates:
        logger.info("  Date range: %s to %s", min(dates), max(dates))

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
