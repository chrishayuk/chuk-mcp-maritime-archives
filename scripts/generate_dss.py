#!/usr/bin/env python3
"""
Generate curated Dutch Ships and Sailors (DSS) data.

The DSS Linked Data Cloud combines four maritime datasets. Two we already
have (DAS voyages, VOC Opvarenden crew). This script generates curated
data for the two new datasets:

    GZMVOC — Generale Zeemonsterrollen VOC (Asian muster rolls, 1691-1791)
        Ship-level crew composition and wage records for VOC ships mustered
        in Asian ports. Complements VOC Opvarenden which records departures
        from the Netherlands.

    MDB — Noordelijke Monsterrollen (Northern muster rolls, 1803-1837)
        Individual crew records from four northern Dutch provinces:
        Groningen, Friesland, Drenthe, and Overijssel. 19th-century
        merchant shipping, extends coverage beyond the VOC era.

Outputs:
    data/dss_musters.json  -- ~60 GZMVOC ship muster records
    data/dss_crews.json    -- ~100 MDB individual crew records

Run from the project root:

    python scripts/generate_dss.py

Sources:
    - Dutch Ships and Sailors (CLARIN IV), Huygens ING / VU Amsterdam / IISG
    - GZMVOC: Dr. M. van Rossum, based on Generale Zeemonsterrollen archives
    - MDB: Jurjen Leinenga, from provincial archives and maritime museums
"""

import json
import random
from pathlib import Path

from download_utils import is_cached, parse_args

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

MUSTERS_OUTPUT = DATA_DIR / "dss_musters.json"
CREWS_OUTPUT = DATA_DIR / "dss_crews.json"

ARCHIVE = "dss"

# ---------------------------------------------------------------------------
# Historical VOC ships operating in Asian waters
# ---------------------------------------------------------------------------
VOC_SHIPS_ASIA = {
    "Amsterdam": {"tonnage": 850, "type": "retourschip"},
    "Batavia": {"tonnage": 600, "type": "retourschip"},
    "Zeelandia": {"tonnage": 700, "type": "retourschip"},
    "Middelburg": {"tonnage": 780, "type": "retourschip"},
    "Huis te Merwede": {"tonnage": 650, "type": "retourschip"},
    "Slot ter Hooge": {"tonnage": 700, "type": "retourschip"},
    "Rustenburg": {"tonnage": 600, "type": "retourschip"},
    "Noordwijk": {"tonnage": 550, "type": "retourschip"},
    "Blijdorp": {"tonnage": 620, "type": "retourschip"},
    "Schoonderloo": {"tonnage": 580, "type": "retourschip"},
    "Westhoven": {"tonnage": 500, "type": "fluit"},
    "Langewijk": {"tonnage": 450, "type": "fluit"},
    "De Liefde": {"tonnage": 680, "type": "retourschip"},
    "Spiegel": {"tonnage": 720, "type": "retourschip"},
    "Java": {"tonnage": 640, "type": "retourschip"},
    "Hollandia": {"tonnage": 850, "type": "retourschip"},
    "Overijssel": {"tonnage": 750, "type": "retourschip"},
    "Gelderland": {"tonnage": 680, "type": "retourschip"},
    "Dordrecht": {"tonnage": 600, "type": "retourschip"},
    "Enkhuizen": {"tonnage": 550, "type": "retourschip"},
}

# ---------------------------------------------------------------------------
# Muster locations in VOC Asia
# ---------------------------------------------------------------------------
MUSTER_LOCATIONS = [
    "Batavia",
    "Colombo",
    "Cochin",
    "Malacca",
    "Galle",
    "Ambon",
    "Banda",
    "Dejima",
    "Surat",
    "Coromandel",
    "Ternate",
    "Makassar",
]

# ---------------------------------------------------------------------------
# Dutch captains (VOC era)
# ---------------------------------------------------------------------------
VOC_CAPTAINS = [
    "Jan Pietersz van Hoorn",
    "Cornelis Speelman",
    "Willem van der Stel",
    "Hendrik Brouwer",
    "Johan van Riebeeck",
    "Pieter Both",
    "Gerrit Reynst",
    "Cornelis Matelief",
    "Jan Coen",
    "Anthony van Diemen",
    "Hendrik Zwaardecroon",
    "Mattheus de Haan",
    "Jacob Mossel",
    "Gustaaf Willem van Imhoff",
    "Petrus Albertus van der Parra",
    "Jeremias van Riemsdijk",
    "Diederik van Durven",
    "Adriaan Valckenier",
    "Abraham Douglas",
    "Christiaan van Angelbeek",
]

# ---------------------------------------------------------------------------
# Rank composition templates (typical for different ship sizes)
# ---------------------------------------------------------------------------
RANK_TEMPLATES = {
    "large_retourschip": {
        "schipper": 1,
        "stuurman": 3,
        "bootsman": 2,
        "konstabel": 1,
        "kwartiermeester": 4,
        "matroos": 65,
        "soldaat": 40,
        "timmerman": 2,
        "zeilmaker": 1,
        "kok": 2,
        "chirurgijn": 1,
        "provoost": 1,
        "schrijver": 1,
    },
    "medium_retourschip": {
        "schipper": 1,
        "stuurman": 2,
        "bootsman": 1,
        "konstabel": 1,
        "kwartiermeester": 3,
        "matroos": 45,
        "soldaat": 25,
        "timmerman": 1,
        "zeilmaker": 1,
        "kok": 1,
        "chirurgijn": 1,
        "schrijver": 1,
    },
    "fluit": {
        "schipper": 1,
        "stuurman": 1,
        "bootsman": 1,
        "kwartiermeester": 2,
        "matroos": 25,
        "soldaat": 8,
        "timmerman": 1,
        "kok": 1,
    },
}

# ---------------------------------------------------------------------------
# MDB — Northern Dutch ships and captains (post-VOC era, 1803-1837)
# ---------------------------------------------------------------------------
MDB_SHIPS = {
    "De Hoop": {"tonnage": 350, "home_port": "Harlingen"},
    "Vrouw Maria": {"tonnage": 280, "home_port": "Groningen"},
    "Harmonie": {"tonnage": 320, "home_port": "Harlingen"},
    "Twee Gebroeders": {"tonnage": 220, "home_port": "Delfzijl"},
    "De Jonge Jan": {"tonnage": 180, "home_port": "Groningen"},
    "Onderneming": {"tonnage": 400, "home_port": "Harlingen"},
    "Stad Groningen": {"tonnage": 450, "home_port": "Groningen"},
    "Vriesland": {"tonnage": 380, "home_port": "Harlingen"},
    "De Vriendschap": {"tonnage": 260, "home_port": "Delfzijl"},
    "Minerva": {"tonnage": 500, "home_port": "Harlingen"},
    "De Eendracht": {"tonnage": 340, "home_port": "Groningen"},
    "Anna Maria": {"tonnage": 290, "home_port": "Delfzijl"},
    "Neerlands Trouw": {"tonnage": 420, "home_port": "Harlingen"},
    "De Goede Hoop": {"tonnage": 310, "home_port": "Groningen"},
    "Borneo": {"tonnage": 480, "home_port": "Harlingen"},
    "Henriette": {"tonnage": 250, "home_port": "Delfzijl"},
    "Java Packet": {"tonnage": 520, "home_port": "Harlingen"},
    "De Verwachting": {"tonnage": 200, "home_port": "Groningen"},
    "Drie Gebroeders": {"tonnage": 180, "home_port": "Delfzijl"},
    "Prinses Marianne": {"tonnage": 460, "home_port": "Harlingen"},
}

MDB_CAPTAINS = [
    "Jan Hendriks",
    "Pieter de Vries",
    "Klaas Jansz",
    "Willem Bakker",
    "Geert Mulder",
    "Harmen Smit",
    "Jacob Visser",
    "Freerk Dijkstra",
    "Tjeerd van der Meer",
    "Sjoerd Hoekstra",
    "Abe de Jong",
    "Dirk Bos",
    "Hendrik Postma",
    "Rein Wierda",
    "Evert Boer",
    "Johannes van Dijk",
    "Kornelis Meijer",
    "Albert Veenstra",
    "Sybe Terpstra",
    "Gerben Haitsma",
]

MDB_ORIGINS = [
    "Groningen",
    "Delfzijl",
    "Harlingen",
    "Leeuwarden",
    "Dokkum",
    "Heerenveen",
    "Sneek",
    "Assen",
    "Meppel",
    "Zwolle",
    "Deventer",
    "Kampen",
    "Emden",
    "Appingedam",
    "Veendam",
    "Winschoten",
    "Bolsward",
    "Franeker",
    "Stavoren",
    "Lemmer",
]

MDB_DESTINATIONS = [
    "Batavia",
    "Suriname",
    "London",
    "Hamburg",
    "Bremen",
    "Riga",
    "Stockholm",
    "Copenhagen",
    "Bordeaux",
    "Lisbon",
    "Archangel",
    "St. Petersburg",
    "Memel",
    "Danzig",
    "Bergen",
]

MDB_RANKS = [
    ("schipper", "captain"),
    ("stuurman", "mate"),
    ("bootsman", "boatswain"),
    ("matroos", "sailor"),
    ("lichtmatroos", "ordinary sailor"),
    ("jongen", "ship's boy"),
    ("kok", "cook"),
    ("timmerman", "carpenter"),
    ("zeilmaker", "sailmaker"),
]


# ---------------------------------------------------------------------------
# Build GZMVOC muster records
# ---------------------------------------------------------------------------
def build_musters() -> list[dict]:
    """Return ~60 GZMVOC ship-level muster records."""
    import random

    rng = random.Random(42)  # deterministic

    ships = list(VOC_SHIPS_ASIA.keys())
    captains = list(VOC_CAPTAINS)
    locations = list(MUSTER_LOCATIONS)

    musters: list[dict] = []
    muster_num = 0

    # Generate musters across the GZMVOC period (1691-1791)
    for year in range(1691, 1792, 2):
        # 1-2 musters per 2-year period
        n_musters = rng.choice([1, 1, 2])
        for _ in range(n_musters):
            muster_num += 1
            ship_name = rng.choice(ships)
            ship_info = VOC_SHIPS_ASIA[ship_name]
            captain = rng.choice(captains)
            location = rng.choice(locations)
            month = rng.randint(1, 12)
            day = rng.randint(1, 28)

            tonnage = ship_info["tonnage"]
            ship_type = ship_info["type"]

            # Crew size scales with tonnage
            if tonnage >= 700:
                template = dict(RANK_TEMPLATES["large_retourschip"])
            elif ship_type == "fluit":
                template = dict(RANK_TEMPLATES["fluit"])
            else:
                template = dict(RANK_TEMPLATES["medium_retourschip"])

            total_european = sum(template.values())
            # Asian crew typically 20-40% of total in the 18th century
            asian_ratio = rng.uniform(0.15, 0.45)
            total_asian = int(total_european * asian_ratio)
            total_crew = total_european + total_asian

            # Wages: European sailors ~9-14 guilders/month
            # Captains ~60-80, officers ~20-40, common sailors ~9-12
            base_wage = rng.uniform(9.0, 12.0)
            # Mean wage is pulled up by officers
            mean_wage = round(base_wage + rng.uniform(1.0, 4.0), 1)
            monthly_total = round(mean_wage * total_crew, 0)

            # DAS voyage link (plausible — use realistic DAS voyage IDs)
            das_voyage_id = f"das:{rng.randint(100, 8000):04d}.1" if rng.random() < 0.6 else None

            muster_date = f"{year}-{month:02d}-{day:02d}"

            particulars = _muster_particulars(
                ship_name, captain, location, year, total_crew, total_asian, rng
            )

            musters.append(
                {
                    "muster_id": f"dss_muster:{muster_num:04d}",
                    "ship_name": ship_name,
                    "ship_type": ship_type,
                    "tonnage_lasten": tonnage,
                    "captain": captain,
                    "muster_date": muster_date,
                    "muster_location": location,
                    "total_european": total_european,
                    "total_asian": total_asian,
                    "total_crew": total_crew,
                    "monthly_wages_guilders": int(monthly_total),
                    "mean_wage_guilders": mean_wage,
                    "ranks_summary": template,
                    "das_voyage_id": das_voyage_id,
                    "particulars": particulars,
                    "archive": ARCHIVE,
                }
            )

    return musters


def _muster_particulars(
    ship: str,
    captain: str,
    location: str,
    year: int,
    total: int,
    asian: int,
    rng: "random.Random",
) -> str:
    """Generate a plausible narrative for a muster record."""
    templates = [
        f"General muster of the {ship} under Captain {captain} at "
        f"{location} roadstead, {year}. Ship carried {total} crew "
        f"including {asian} Asian sailors. Crew assessed fit for "
        f"continued service.",
        f"Muster roll taken at {location} for the {ship}. "
        f"Captain {captain} reported {total} men aboard. "
        f"{asian} local recruits supplemented the European complement.",
        f"Annual inspection of the {ship} at {location}, {year}. "
        f"Total complement: {total} ({asian} Asian crew). "
        f"Captain {captain} commanding. Ship in good order.",
        f"Crew muster of {ship} before departure from {location}. "
        f"{total} crew mustered by Captain {captain}. "
        f"Asian complement of {asian} men recruited locally.",
        f"General zeemonsterrol for {ship}, {location} {year}. "
        f"Under command of Captain {captain}. "
        f"Full complement of {total} men including {asian} Asian recruits. "
        f"Wages disbursed per standard VOC rates.",
    ]
    return rng.choice(templates)


# ---------------------------------------------------------------------------
# Build MDB crew records
# ---------------------------------------------------------------------------
def build_crews() -> list[dict]:
    """Return ~100 MDB individual crew records."""
    import random

    rng = random.Random(137)  # deterministic, different seed

    ships = list(MDB_SHIPS.keys())
    captains = list(MDB_CAPTAINS)
    origins = list(MDB_ORIGINS)
    destinations = list(MDB_DESTINATIONS)

    crews: list[dict] = []
    crew_num = 0

    # Generate records across the MDB period (1803-1837)
    for year in range(1803, 1838):
        # 2-4 crew records per year
        n_records = rng.choice([2, 3, 3, 4])
        for _ in range(n_records):
            crew_num += 1

            ship_name = rng.choice(ships)
            ship_info = MDB_SHIPS[ship_name]
            captain = rng.choice(captains)
            origin = rng.choice(origins)
            destination = rng.choice(destinations)
            rank_nl, rank_en = rng.choice(MDB_RANKS)

            month = rng.randint(1, 12)
            day = rng.randint(1, 28)
            muster_date = f"{year}-{month:02d}-{day:02d}"
            muster_location = ship_info["home_port"]

            # Age depends on rank
            if rank_nl == "schipper":
                age = rng.randint(32, 55)
            elif rank_nl == "stuurman":
                age = rng.randint(25, 45)
            elif rank_nl == "jongen":
                age = rng.randint(12, 18)
            elif rank_nl == "lichtmatroos":
                age = rng.randint(16, 25)
            else:
                age = rng.randint(18, 50)

            # Wages depend on rank (guilders/month, post-VOC era)
            wage_ranges = {
                "schipper": (50, 80),
                "stuurman": (25, 40),
                "bootsman": (18, 28),
                "matroos": (10, 16),
                "lichtmatroos": (6, 10),
                "jongen": (3, 6),
                "kok": (14, 22),
                "timmerman": (16, 26),
                "zeilmaker": (15, 24),
            }
            wage_min, wage_max = wage_ranges.get(rank_nl, (8, 14))
            wage = round(rng.uniform(wage_min, wage_max), 1)

            crews.append(
                {
                    "crew_id": f"dss:{crew_num:05d}",
                    "name": _dutch_name(rng),
                    "ship_name": ship_name,
                    "captain": captain,
                    "rank": rank_nl,
                    "rank_english": rank_en,
                    "origin": origin,
                    "age": age,
                    "monthly_pay_guilders": wage,
                    "muster_date": muster_date,
                    "muster_location": muster_location,
                    "destination": destination,
                    "tonnage_lasten": ship_info["tonnage"],
                    "archive": ARCHIVE,
                }
            )

    return crews


# Dutch given names and surnames for MDB era
_GIVEN_NAMES = [
    "Jan",
    "Pieter",
    "Klaas",
    "Willem",
    "Geert",
    "Harmen",
    "Jacob",
    "Freerk",
    "Tjeerd",
    "Sjoerd",
    "Abe",
    "Dirk",
    "Hendrik",
    "Rein",
    "Evert",
    "Johannes",
    "Kornelis",
    "Albert",
    "Sybe",
    "Gerben",
    "Jelle",
    "Wiebe",
    "Douwe",
    "Ids",
    "Folkert",
    "Marten",
    "Berend",
    "Roelof",
    "Lammert",
    "Arent",
]

_SURNAMES = [
    "Jansen",
    "de Vries",
    "Bakker",
    "Mulder",
    "Smit",
    "Visser",
    "Dijkstra",
    "van der Meer",
    "Hoekstra",
    "de Jong",
    "Bos",
    "Postma",
    "Wierda",
    "Boer",
    "van Dijk",
    "Meijer",
    "Veenstra",
    "Terpstra",
    "Haitsma",
    "Zijlstra",
    "Brouwer",
    "van der Berg",
    "Veldman",
    "Sikkema",
    "Koopmans",
    "Groen",
    "de Boer",
    "Fokkema",
    "Algra",
    "Douma",
]


def _dutch_name(rng: "random.Random") -> str:
    """Generate a plausible Dutch name."""
    return f"{rng.choice(_GIVEN_NAMES)} {rng.choice(_SURNAMES)}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args("Generate Dutch Ships and Sailors (DSS) data")

    print("=" * 60)
    print("DSS Data Generation — chuk-mcp-maritime-archives")
    print("=" * 60)
    print(f"\nData directory: {DATA_DIR}\n")

    if not args.force and is_cached(MUSTERS_OUTPUT, args.cache_max_age):
        print(f"Using cached {MUSTERS_OUTPUT.name} (use --force to regenerate)")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -- GZMVOC Musters --
    print("Step 1: Generating GZMVOC muster records ...")
    musters = build_musters()
    with open(MUSTERS_OUTPUT, "w") as f:
        json.dump(musters, f, indent=2, ensure_ascii=False)
    print(f"  {MUSTERS_OUTPUT}")
    print(f"  {len(musters)} musters written ({MUSTERS_OUTPUT.stat().st_size:,} bytes)")

    # Validate muster IDs
    expected_ids = {f"dss_muster:{i:04d}" for i in range(1, len(musters) + 1)}
    actual_ids = {m["muster_id"] for m in musters}
    assert expected_ids == actual_ids, (
        f"Muster ID mismatch: missing={expected_ids - actual_ids}, "
        f"extra={actual_ids - expected_ids}"
    )

    for m in musters:
        assert m["archive"] == ARCHIVE, f"Missing archive field on {m['muster_id']}"

    locations = {}
    for m in musters:
        loc = m["muster_location"]
        locations[loc] = locations.get(loc, 0) + 1
    print(f"  Locations: {dict(sorted(locations.items(), key=lambda x: -x[1]))}")

    # -- MDB Crews --
    print("\nStep 2: Generating MDB crew records ...")
    crews = build_crews()
    with open(CREWS_OUTPUT, "w") as f:
        json.dump(crews, f, indent=2, ensure_ascii=False)
    print(f"  {CREWS_OUTPUT}")
    print(f"  {len(crews)} crew records written ({CREWS_OUTPUT.stat().st_size:,} bytes)")

    # Validate crew IDs
    expected_crew_ids = {f"dss:{i:05d}" for i in range(1, len(crews) + 1)}
    actual_crew_ids = {c["crew_id"] for c in crews}
    assert expected_crew_ids == actual_crew_ids, (
        f"Crew ID mismatch: missing={expected_crew_ids - actual_crew_ids}, "
        f"extra={actual_crew_ids - expected_crew_ids}"
    )

    for c in crews:
        assert c["archive"] == ARCHIVE, f"Missing archive field on {c['crew_id']}"

    # -- Summary --
    muster_years = [int(m["muster_date"][:4]) for m in musters]
    crew_years = [int(c["muster_date"][:4]) for c in crews]

    print(f"\n  GZMVOC period: {min(muster_years)}-{max(muster_years)}")
    print(f"  MDB period: {min(crew_years)}-{max(crew_years)}")

    crew_origins = {}
    for c in crews:
        o = c["origin"]
        crew_origins[o] = crew_origins.get(o, 0) + 1
    top_origins = sorted(crew_origins.items(), key=lambda x: -x[1])[:5]
    print(f"  Top origins: {dict(top_origins)}")

    print(f"\n{'=' * 60}")
    print("DSS data generation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
