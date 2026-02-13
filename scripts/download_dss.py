#!/usr/bin/env python3
"""
Download Dutch Ships and Sailors (DSS) Linked Data.

Downloads .ttl (Turtle) files from the DANS Data Station for the CLARIN-IV
DSS Linked Data Cloud project and parses them into JSON format.

Datasets:
    GZMVOC — Generale Zeemonsterrollen VOC (ship-level muster records
             from Asian waters, 1691-1791)
    MDB    — Noordelijke Monsterrollen (individual crew records from
             northern Dutch provinces, 1803-1837)

Source: doi:10.17026/dans-zeu-be9b

Falls back to generate_dss.py if download or parsing fails.

Usage:
    python scripts/download_dss.py [--force]
"""

import re
import sys

from download_utils import (
    DATA_DIR,
    download_file,
    ensure_cache_dir,
    is_cached,
    parse_args,
    save_json,
)

# ---------------------------------------------------------------------------
# Data source URLs (DANS Data Station / VU Amsterdam)
# ---------------------------------------------------------------------------

# These are the Turtle RDF files from the DSS Linked Data Cloud.
# The SPARQL endpoints at semanticweb.cs.vu.nl/dss/ are offline (500 errors)
# so we download the .ttl files directly.

GZMVOC_DATA_URL = (
    "https://easy.dans.knaw.nl/oai?verb=GetRecord"
    "&metadataPrefix=oai_datacite"
    "&identifier=oai:easy.dans.knaw.nl:easy-dataset:36988"
)
MDB_DATA_URL = (
    "https://easy.dans.knaw.nl/oai?verb=GetRecord"
    "&metadataPrefix=oai_datacite"
    "&identifier=oai:easy.dans.knaw.nl:easy-dataset:36988"
)

# ---------------------------------------------------------------------------
# Simple Turtle parser (no rdflib dependency)
# ---------------------------------------------------------------------------


def _parse_ttl_triples(text: str) -> list[tuple[str, str, str]]:
    """
    Extract subject-predicate-object triples from Turtle text.

    This is a minimal line-based parser sufficient for the DSS data files.
    It does NOT handle the full Turtle spec (blank nodes, nested, etc.)
    but is good enough for the flat record-per-subject DSS data.
    """
    triples = []
    current_subject = None

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue

        # Subject predicate object .
        match = re.match(r"^(<[^>]+>)\s+(<[^>]+>)\s+(.+)\s+\.\s*$", line)
        if match:
            current_subject = match.group(1)
            pred = match.group(2)
            obj = match.group(3).strip()
            triples.append((current_subject, pred, obj))
            continue

        # Continuation: ; predicate object .
        match = re.match(r"^;\s+(<[^>]+>)\s+(.+)\s+[;.]\s*$", line)
        if match and current_subject:
            pred = match.group(1)
            obj = match.group(2).strip()
            triples.append((current_subject, pred, obj))

    return triples


def _ttl_value(obj: str) -> str:
    """Extract plain value from a Turtle object (remove quotes, datatypes, URIs)."""
    # Quoted literal: "value"^^xsd:type or "value"
    if obj.startswith('"'):
        end = obj.find('"', 1)
        if end > 0:
            return obj[1:end]
    # URI: <http://...>
    if obj.startswith("<") and obj.endswith(">"):
        return obj[1:-1]
    return obj


# ---------------------------------------------------------------------------
# Conversion: triples -> JSON records
# ---------------------------------------------------------------------------


def _triples_to_musters(triples: list[tuple[str, str, str]]) -> list[dict]:
    """Convert GZMVOC triples to muster record dicts."""
    subjects: dict[str, dict[str, str]] = {}
    for subj, pred, obj in triples:
        if subj not in subjects:
            subjects[subj] = {}
        pred_local = pred.rsplit("/", 1)[-1].rstrip(">")
        subjects[subj][pred_local] = _ttl_value(obj)

    records = []
    idx = 0
    for _subj, props in subjects.items():
        if "shipName" not in props and "ship_name" not in props:
            continue
        idx += 1
        records.append(
            {
                "muster_id": f"dss_muster:{idx:04d}",
                "ship_name": props.get("shipName", props.get("ship_name", "")),
                "captain": props.get("captain"),
                "muster_date": props.get("date", props.get("muster_date")),
                "muster_location": props.get("location", props.get("muster_location")),
                "total_crew": int(props["crewCount"]) if "crewCount" in props else None,
                "archive": "dss",
            }
        )
    return records


def _triples_to_crews(triples: list[tuple[str, str, str]]) -> list[dict]:
    """Convert MDB triples to individual crew record dicts."""
    subjects: dict[str, dict[str, str]] = {}
    for subj, pred, obj in triples:
        if subj not in subjects:
            subjects[subj] = {}
        pred_local = pred.rsplit("/", 1)[-1].rstrip(">")
        subjects[subj][pred_local] = _ttl_value(obj)

    records = []
    idx = 0
    for _subj, props in subjects.items():
        if "name" not in props and "firstName" not in props:
            continue
        idx += 1
        name = props.get("name", "")
        if not name and "firstName" in props:
            name = f"{props.get('firstName', '')} {props.get('lastName', '')}".strip()
        records.append(
            {
                "crew_id": f"dss:{idx:05d}",
                "name": name,
                "ship_name": props.get("shipName", props.get("ship_name")),
                "rank": props.get("rank"),
                "origin": props.get("origin", props.get("birthPlace")),
                "age": int(props["age"]) if "age" in props else None,
                "muster_date": props.get("date", props.get("muster_date")),
                "archive": "dss",
            }
        )
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args("Download DSS Linked Data (.ttl) and convert to JSON")

    musters_path = DATA_DIR / "dss_musters.json"
    crews_path = DATA_DIR / "dss_crews.json"

    if not args.force and is_cached(musters_path) and is_cached(crews_path):
        print("DSS data is cached and up-to-date. Use --force to re-download.")
        return

    print("=" * 60)
    print("DSS Linked Data Download")
    print("=" * 60)
    print()
    print("NOTE: The SPARQL endpoints at semanticweb.cs.vu.nl/dss/ are")
    print("      currently offline (HTTP 500). Attempting .ttl download")
    print("      from DANS Data Station...")
    print()

    cache_dir = ensure_cache_dir()
    success = False

    try:
        # Attempt to download GZMVOC data
        gzmvoc_path = cache_dir / "gzmvoc_data.ttl"
        download_file(GZMVOC_DATA_URL, gzmvoc_path, "GZMVOC muster data")

        # Attempt to download MDB data
        mdb_path = cache_dir / "mdb_data.ttl"
        download_file(MDB_DATA_URL, mdb_path, "MDB crew data")

        # Parse Turtle files
        with open(gzmvoc_path, encoding="utf-8") as f:
            gzmvoc_text = f.read()
        with open(mdb_path, encoding="utf-8") as f:
            mdb_text = f.read()

        gzmvoc_triples = _parse_ttl_triples(gzmvoc_text)
        mdb_triples = _parse_ttl_triples(mdb_text)

        musters = _triples_to_musters(gzmvoc_triples)
        crews = _triples_to_crews(mdb_triples)

        if musters and crews:
            save_json(musters, "dss_musters.json")
            save_json(crews, "dss_crews.json")
            print(f"\nSuccess: {len(musters)} musters, {len(crews)} crew records")
            success = True
        else:
            print("\nParsing produced no records — falling back to generator.")

    except Exception as e:
        print(f"\nDownload/parse failed: {e}")
        print("Falling back to curated data generator...")

    if not success:
        # Fall back to generate_dss.py
        print("\nRunning generate_dss.py...")
        import subprocess

        result = subprocess.run(
            [sys.executable, "scripts/generate_dss.py", "--force"],
            check=True,
        )
        if result.returncode != 0:
            print("ERROR: generate_dss.py also failed!", file=sys.stderr)
            sys.exit(1)
        print("Fallback generation complete.")


if __name__ == "__main__":
    main()
