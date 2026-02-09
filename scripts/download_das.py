#!/usr/bin/env python3
"""
Download and normalize DAS (Dutch Asiatic Shipping) data.

Fetches the complete voyage database from the Huygens Institute DAS
website via CSV export endpoints. Parses, normalizes, and saves as
structured JSON files ready for the MCP server.

Produces:
    data/voyages.json  -- All 8,000+ VOC voyage records
    data/vessels.json   -- Unique vessel records extracted from voyages
    data/wrecks.json    -- Loss/wreck records extracted from voyage Particulars

Source:
    https://resources.huygens.knaw.nl/das

Usage:
    python scripts/download_das.py
"""

import csv
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://resources.huygens.knaw.nl/das"
DETAILS_CSV = f"{BASE_URL}/voyages_with_details.csv"
OPVARENDEN_CSV = f"{BASE_URL}/voyages_with_opvarenden.csv"

# Full date range for all VOC voyages
PARAMS = "clear=1&field_voydepartureY0=1595&field_voydepartureY1=1795"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Keywords in Particulars that indicate a loss event
LOSS_KEYWORDS = {
    "wrecked": "wrecked",
    "lost": "lost",
    "sunk": "sunk",
    "blown up": "fire",
    "burned": "fire",
    "burnt": "fire",
    "set on fire": "fire",
    "stranded": "grounding",
    "foundered": "foundered",
    "captured": "captured",
    "taken by": "captured",
    "seized": "captured",
    "ran aground": "grounding",
    "ran on": "grounding",
}


def fetch_csv(url: str) -> str:
    """Fetch CSV content from a URL."""
    full_url = f"{url}?{PARAMS}"
    print(f"  Fetching {full_url}")
    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": "chuk-mcp-maritime-archives/0.1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
        return resp.read().decode("utf-8")


def convert_date(date_str: str) -> str:
    """Convert DD-MM-YYYY to YYYY-MM-DD. Returns original if unparseable."""
    if not date_str or date_str in ("no call", ""):
        return ""
    # Handle partial dates like "-03-1599" or "1620"
    m = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", date_str)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    # Partial: -MM-YYYY
    m = re.match(r"^-(\d{2})-(\d{4})$", date_str)
    if m:
        return f"{m.group(2)}-{m.group(1)}"
    # Ambiguous day: DD/DD-MM-YYYY (e.g. "01/02-10-1754" meaning 1 or 2 Oct)
    m = re.match(r"^(\d{2})/\d{2}-(\d{2})-(\d{4})$", date_str)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    # Just a year
    m = re.match(r"^(\d{4})$", date_str)
    if m:
        return date_str
    return date_str


def parse_tonnage(tonnage_str: str) -> int | None:
    """Parse tonnage string, handling '400/600' format."""
    if not tonnage_str:
        return None
    # Take first number from formats like "400/600"
    m = re.match(r"(\d+)", tonnage_str)
    if m:
        return int(m.group(1))
    return None


def parse_built_year(built_str: str) -> int | None:
    """Parse built year, handling 'bought 1666' etc."""
    if not built_str:
        return None
    m = re.search(r"(\d{4})", built_str)
    if m:
        return int(m.group(1))
    return None


def extract_fate(particulars: str) -> str | None:
    """Extract fate/loss cause from Particulars text."""
    if not particulars:
        return None
    lower = particulars.lower()
    for keyword, cause in LOSS_KEYWORDS.items():
        if keyword in lower:
            return cause
    return None


def extract_wreck_status(particulars: str) -> str:
    """Determine if wreck has been found from Particulars text."""
    if not particulars:
        return "unfound"
    lower = particulars.lower()
    if "discovered" in lower or "wreck has been found" in lower:
        return "found"
    return "unfound"


def parse_voyages_csv(csv_text: str) -> list[dict]:
    """Parse the semicolon-delimited voyage details CSV."""
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    voyages = []
    for row in reader:
        particulars = row.get("Particulars", "")
        fate = extract_fate(particulars)
        voyage = {
            "voyage_id": f"das:{row['Number']}",
            "voyage_number": row["Number"],
            "ship_name": row.get("Name of ship", ""),
            "captain": row.get("Master", "") or None,
            "tonnage": parse_tonnage(row.get("Tonnage", "")),
            "ship_type": (row.get("Type of ship", "") or "").strip().lower() or None,
            "built_year": parse_built_year(row.get("Built", "")),
            "yard": row.get("Yard", "") or None,
            "chamber": row.get("Chamber", "") or None,
            "departure_date": convert_date(row.get("Date of departure", "")),
            "departure_port": row.get("Place of departure", "") or None,
            "cape_arrival": convert_date(row.get("Arrival at Cape", "")),
            "cape_departure": convert_date(row.get("Departure from Cape", "")),
            "arrival_date": convert_date(row.get("Date of arrival at destination", "")),
            "destination_port": row.get("Place of arrival", "") or None,
            "cargo_chamber": row.get("Chamber for which cargo is destined", "") or None,
            "particulars": particulars or None,
            "fate": fate,
            "source_url": f"{BASE_URL}/detailVoyage/{row['Number']}",
        }
        # Clean up None-equivalent empty strings
        voyage = {k: v for k, v in voyage.items() if v is not None and v != ""}
        # Always keep these keys even if empty
        for key in ("voyage_id", "voyage_number", "ship_name"):
            if key not in voyage:
                voyage[key] = ""
        voyages.append(voyage)
    return voyages


def parse_opvarenden_csv(csv_text: str) -> dict[str, dict]:
    """Parse crew-on-board CSV. Returns {voyage_number: {category: {I..VI}}}."""
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=",")
    crew_data: dict[str, dict] = {}
    for row in reader:
        number = row.get("Number", "").strip('"')
        category = (row.get("onbcategory", "") or "").strip().lower()
        if not number or not category:
            continue
        if number not in crew_data:
            crew_data[number] = {}
        crew_data[number][category] = {
            "on_board_departure": _int_or_none(row.get("I", "")),
            "died_to_cape": _int_or_none(row.get("II", "")),
            "left_at_cape": _int_or_none(row.get("III", "")),
            "joined_at_cape": _int_or_none(row.get("IV", "")),
            "died_total": _int_or_none(row.get("V", "")),
            "on_board_arrival": _int_or_none(row.get("VI", "")),
        }
        # Remove None values
        crew_data[number][category] = {
            k: v for k, v in crew_data[number][category].items() if v is not None
        }
    return crew_data


def _int_or_none(s: str) -> int | None:
    s = s.strip().strip('"')
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def merge_crew_data(voyages: list[dict], crew_data: dict[str, dict]) -> None:
    """Merge opvarenden crew stats into voyage records in-place."""
    for voyage in voyages:
        number = voyage["voyage_number"]
        if number in crew_data:
            voyage["crew_on_board"] = crew_data[number]


def extract_vessels(voyages: list[dict]) -> list[dict]:
    """Extract unique vessel records from voyage data."""
    vessel_map: dict[str, dict] = {}
    for v in voyages:
        name = v.get("ship_name", "")
        if not name:
            continue
        tonnage = v.get("tonnage")
        built = v.get("built_year")
        # Key by name + tonnage + built to distinguish same-named ships
        key = f"{name}|{tonnage or ''}|{built or ''}"
        if key not in vessel_map:
            vessel_map[key] = {
                "name": name,
                "type": v.get("ship_type"),
                "tonnage": tonnage,
                "built_year": built,
                "yard": v.get("yard"),
                "chamber": v.get("chamber"),
                "voyage_ids": [],
            }
        vessel_map[key]["voyage_ids"].append(v["voyage_id"])

    vessels = []
    for idx, (_, vessel) in enumerate(sorted(vessel_map.items()), 1):
        vessel["vessel_id"] = f"das_vessel:{idx:04d}"
        # Clean None values
        vessel = {k: v for k, v in vessel.items() if v is not None}
        if "vessel_id" not in vessel:
            vessel["vessel_id"] = f"das_vessel:{idx:04d}"
        vessels.append(vessel)
    return vessels


def extract_wrecks(voyages: list[dict]) -> list[dict]:
    """Extract wreck/loss records from voyages with loss events."""
    wrecks = []
    for v in voyages:
        fate = v.get("fate")
        if not fate:
            continue
        particulars = v.get("particulars", "")
        wreck = {
            "wreck_id": f"maarer:{v['voyage_number']}",
            "voyage_id": v["voyage_id"],
            "ship_name": v.get("ship_name", ""),
            "ship_type": v.get("ship_type"),
            "tonnage": v.get("tonnage"),
            "captain": v.get("captain"),
            "chamber": v.get("chamber"),
            "loss_cause": fate,
            "loss_date": v.get("departure_date"),
            "departure_port": v.get("departure_port"),
            "destination_port": v.get("destination_port"),
            "status": extract_wreck_status(particulars),
            "particulars": particulars,
        }
        # Try to extract crew stats for lives-lost estimate
        crew = v.get("crew_on_board", {})
        total = crew.get("total", {})
        if total.get("on_board_departure"):
            wreck["crew_total"] = total["on_board_departure"]
        if total.get("died_total"):
            wreck["lives_lost"] = total["died_total"]

        wreck = {k: v for k, v in wreck.items() if v is not None}
        wrecks.append(wreck)
    return wrecks


def save_json(data: list[dict], filename: str) -> Path:
    """Save data as JSON file in the data directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def main() -> None:
    print("=" * 60)
    print("DAS Data Download — chuk-mcp-maritime-archives")
    print("=" * 60)
    print(f"\nSource: {BASE_URL}")
    print(f"Output: {DATA_DIR}\n")

    # Step 1: Download voyage details CSV
    print("Step 1: Downloading voyage details CSV...")
    try:
        details_csv = fetch_csv(DETAILS_CSV)
    except Exception as e:
        print(f"  FAILED: {e}")
        sys.exit(1)

    voyages = parse_voyages_csv(details_csv)
    print(f"  Parsed {len(voyages)} voyage records")

    # Step 2: Download opvarenden (crew) CSV
    print("\nStep 2: Downloading crew-on-board CSV...")
    try:
        opvarenden_csv = fetch_csv(OPVARENDEN_CSV)
        crew_data = parse_opvarenden_csv(opvarenden_csv)
        merge_crew_data(voyages, crew_data)
        print(f"  Merged crew data for {len(crew_data)} voyages")
    except Exception as e:
        print(f"  WARNING: Could not fetch crew data: {e}")
        print("  Continuing without crew-on-board statistics...")

    # Step 3: Extract vessel records
    print("\nStep 3: Extracting vessel records...")
    vessels = extract_vessels(voyages)
    print(f"  Extracted {len(vessels)} unique vessels")

    # Step 4: Extract wreck records
    print("\nStep 4: Extracting wreck/loss records...")
    wrecks = extract_wrecks(voyages)
    print(f"  Extracted {len(wrecks)} loss events")
    found = sum(1 for w in wrecks if w.get("status") == "found")
    print(f"    Found: {found}  Unfound: {len(wrecks) - found}")

    # Step 5: Save JSON files
    print("\nStep 5: Saving JSON files...")
    p1 = save_json(voyages, "voyages.json")
    print(f"  {p1} ({p1.stat().st_size:,} bytes)")
    p2 = save_json(vessels, "vessels.json")
    print(f"  {p2} ({p2.stat().st_size:,} bytes)")
    p3 = save_json(wrecks, "wrecks.json")
    print(f"  {p3} ({p3.stat().st_size:,} bytes)")

    # Summary
    print(f"\n{'=' * 60}")
    print("Download complete!")
    print(f"  Voyages: {len(voyages)}")
    print(f"  Vessels: {len(vessels)}")
    print(f"  Wrecks:  {len(wrecks)} ({found} found, {len(wrecks) - found} unfound)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
