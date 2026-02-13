#!/usr/bin/env python3
"""
Entity Resolution Demo -- chuk-mcp-maritime-archives v0.16.0

Demonstrates fuzzy cross-archive entity resolution:
1. Ship name normalization (articles, case, prefixes)
2. Fuzzy matching with confidence scores (Levenshtein + Soundex)
3. maritime_get_voyage_full with link_confidence and crew
4. maritime_audit_links — precision/recall metrics

All operations are offline using local curated data.

Usage:
    python examples/entity_resolution_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Allow running from the examples/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chuk_mcp_maritime_archives.core.entity_resolution import (
    ShipNameIndex,
    levenshtein_similarity,
    normalize_ship_name,
    score_ship_match,
    soundex,
)

from tool_runner import ToolRunner


def demo_normalization() -> None:
    """Show ship name normalization across conventions."""
    print("=" * 70)
    print("  1. SHIP NAME NORMALIZATION")
    print("     Handles articles, prefixes, casing, and punctuation")
    print("=" * 70)

    examples = [
        ("De Batavia", "Dutch 'De' article"),
        ("BATAVIA", "All-caps (CLIWOC/DAS style)"),
        ("'T Wapen van Hoorn", "Dutch 'T article"),
        ("HMS Victory", "British naval prefix"),
        ("San Pablo", "Spanish saint — NOT stripped"),
        ("Santa Ana", "Spanish saint — NOT stripped"),
        ("Sao Gabriel", "Portuguese saint — NOT stripped"),
        ("VOC Eendracht", "VOC prefix stripped"),
        ("El Buen Consejo", "Spanish article stripped"),
        ("La Reina", "Spanish article stripped"),
        ("USS Constitution", "US Navy prefix stripped"),
    ]

    for name, note in examples:
        norm = normalize_ship_name(name)
        print(f"  {name:<28s}  ->  {norm:<24s}  ({note})")

    print()


def demo_fuzzy_matching() -> None:
    """Show fuzzy matching with confidence scores."""
    print("=" * 70)
    print("  2. FUZZY MATCHING WITH CONFIDENCE SCORES")
    print("     Levenshtein distance + Soundex phonetic encoding")
    print("=" * 70)

    pairs = [
        ("BATAVIA", "BATAVIA", "Identical"),
        ("De Batavia", "BATAVIA", "Article variation"),
        ("HOLLANDIA", "HOLANDIA", "One-letter misspelling"),
        ("AMSTERDAM", "AMSTELDAM", "Historical variant"),
        ("ZEELANDIA", "SELANDIA", "Phonetic variant"),
        ("VICTORIA", "VICTOIRE", "Cross-language variant"),
    ]

    print(
        f"\n  {'Ship A':<20s}  {'Ship B':<20s}  {'Edit Sim':>8s}  {'Soundex A':>9s}  {'Soundex B':>9s}  Note"
    )
    print(f"  {'-' * 20}  {'-' * 20}  {'-' * 8}  {'-' * 9}  {'-' * 9}  {'-' * 20}")
    for a, b, note in pairs:
        a_norm = normalize_ship_name(a)
        b_norm = normalize_ship_name(b)
        sim = levenshtein_similarity(a_norm, b_norm)
        sx_a = soundex(a_norm)
        sx_b = soundex(b_norm)
        match = "Y" if sx_a == sx_b else "N"
        print(f"  {a:<20s}  {b:<20s}  {sim:>8.3f}  {sx_a:>9s}  {sx_b:>9s}  {note} (phon={match})")

    print()


def demo_composite_scoring() -> None:
    """Show composite match scoring with all factors."""
    print("=" * 70)
    print("  3. COMPOSITE MATCH SCORING")
    print("     Weighted: name=0.50, date=0.30, nationality=0.10, phonetic=0.10")
    print("=" * 70)

    test_cases = [
        {
            "query": ("Batavia", "1629-01-01", "NL"),
            "candidate": ("BATAVIA", "batavia-1", "1628-01-01", "1630-01-01", "NL"),
            "label": "Exact match, same era, same nationality",
        },
        {
            "query": ("De Batavia", "1629-01-01", "NL"),
            "candidate": ("BATAVIA", "batavia-2", "1628-01-01", "1630-01-01", "NL"),
            "label": "Article variation, same era",
        },
        {
            "query": ("Hollandia", "1740-01-01", "NL"),
            "candidate": ("HOLANDIA", "holandia-1", "1742-01-01", None, "NL"),
            "label": "Fuzzy name, 2yr gap",
        },
        {
            "query": ("Amsterdam", "1749-01-01", "NL"),
            "candidate": ("AMSTERDAM", "amsterdam-1", "1600-01-01", None, "GB"),
            "label": "Same name, wrong era + nationality",
        },
    ]

    for tc in test_cases:
        q_name, q_date, q_nat = tc["query"]
        c_name, c_id, c_start, c_end, c_nat = tc["candidate"]
        result = score_ship_match(
            query_name=q_name,
            query_date=q_date,
            query_nationality=q_nat,
            candidate_name=c_name,
            candidate_id=c_id,
            candidate_date_start=c_start,
            candidate_date_end=c_end,
            candidate_nationality=c_nat,
        )
        print(f"\n  Query: {q_name} ({q_date}, {q_nat})")
        print(f"  Match: {c_name} -> confidence={result.confidence:.4f} ({result.match_type})")
        print(f"         {result.details}")
        print(f"         {tc['label']}")

    print()


def demo_ship_name_index() -> None:
    """Show the pre-built fuzzy index in action."""
    print("=" * 70)
    print("  4. SHIP NAME INDEX — FAST FUZZY LOOKUP")
    print("     Three-level index: exact -> Soundex -> Levenshtein")
    print("=" * 70)

    records = [
        {
            "voyage_id": "das:1001",
            "ship_name": "BATAVIA",
            "start_date": "1628-10-27",
            "nationality": "NL",
        },
        {
            "voyage_id": "das:1002",
            "ship_name": "HOLLANDIA",
            "start_date": "1627-03-15",
            "nationality": "NL",
        },
        {
            "voyage_id": "das:1003",
            "ship_name": "AMSTERDAM",
            "start_date": "1748-11-01",
            "nationality": "NL",
        },
        {
            "voyage_id": "eic:0062",
            "ship_name": "Earl of Abergavenny",
            "start_date": "1805-02-01",
            "nationality": "GB",
        },
        {
            "voyage_id": "carreira:0001",
            "ship_name": "Sao Gabriel",
            "start_date": "1497-07-08",
            "nationality": "PT",
        },
        {
            "voyage_id": "galleon:0001",
            "ship_name": "San Pablo",
            "start_date": "1565-06-01",
            "nationality": "ES",
        },
        {
            "voyage_id": "soic:0002",
            "ship_name": "Gotheborg",
            "start_date": "1739-01-20",
            "nationality": "SE",
        },
    ]

    index = ShipNameIndex(records)
    print(f"\n  Index size: {index.size} records\n")

    queries = [
        ("De Batavia", "1629-01-01", "NL"),
        ("Holandia", "1627-06-01", "NL"),
        ("AMSTERDAM", "1749-01-01", "NL"),
        ("Earl of Abergaveny", "1805-01-01", "GB"),  # deliberate typo
        ("Goteborg", "1740-01-01", "SE"),  # missing 'h'
    ]

    for q_name, q_date, q_nat in queries:
        matches = index.find_matches(q_name, q_date, q_nat, min_confidence=0.40, max_results=3)
        print(f'  Query: "{q_name}" ({q_date}, {q_nat})')
        if matches:
            for m in matches:
                print(
                    f"    -> {m.candidate_id}  conf={m.confidence:.3f}  type={m.match_type}  [{m.details}]"
                )
        else:
            print("    -> No matches above threshold")
        print()


async def demo_voyage_full_with_confidence() -> None:
    """Show maritime_get_voyage_full with link_confidence."""
    print("=" * 70)
    print("  5. VOYAGE FULL WITH LINK CONFIDENCE")
    print("     Each cross-archive link now has a confidence score")
    print("=" * 70)

    runner = ToolRunner()

    test_voyages = [
        ("eic:0062", "EIC: Earl of Abergavenny (wrecked 1805)"),
        ("carreira:0003", "Carreira: Flor de la Mar (wrecked 1511)"),
        ("galleon:0009", "Galleon: San Diego (sunk 1600)"),
    ]

    for voyage_id, label in test_voyages:
        print(f"\n  {label}")
        print(f"  {'-' * 60}")
        result = await runner.run("maritime_get_voyage_full", voyage_id=voyage_id)
        if "error" in result:
            print(f"    Error: {result['error']}")
            continue

        v = result["voyage"]
        print(f"    Ship:     {v.get('ship_name', '?')}")
        print(f"    Route:    {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}")
        print(f"    Fate:     {v.get('fate', '?')}")

        links = result.get("links_found", [])
        conf = result.get("link_confidence", {})
        print(f"    Links:    {', '.join(links) if links else 'none'}")
        if conf:
            print("    Confidence:")
            for link_type, score in conf.items():
                pct = f"{score * 100:.0f}%"
                print(f"      {link_type:<20s} {pct:>5s}")

    print()


async def demo_audit_links() -> None:
    """Show the maritime_audit_links tool."""
    print("=" * 70)
    print("  6. LINK AUDIT — PRECISION/RECALL METRICS")
    print("     Evaluates cross-archive link quality against ground truth")
    print("=" * 70)

    runner = ToolRunner()
    result = await runner.run("maritime_audit_links")

    if "error" in result:
        print(f"\n  Error: {result['error']}")
    else:
        print(f"\n  Total links evaluated: {result.get('total_links_evaluated', 0)}")

        if result.get("wreck_links"):
            wl = result["wreck_links"]
            print("\n  Wreck links:")
            print(f"    Ground truth:  {wl.get('ground_truth_count', 0)}")
            print(f"    Matched:       {wl.get('matched_count', 0)}")
            print(f"    Precision:     {wl.get('precision', 0):.2f}")
            print(f"    Recall:        {wl.get('recall', 0):.2f}")

        if result.get("cliwoc_links"):
            cl = result["cliwoc_links"]
            print("\n  CLIWOC track links:")
            print(f"    Direct (DAS#): {cl.get('direct_links', 0)}")
            print(f"    Fuzzy matches: {cl.get('fuzzy_matches', 0)}")
            mean_conf = cl.get("mean_confidence", 0)
            print(f"    Mean conf:     {mean_conf:.3f}" if mean_conf else "    Mean conf:     N/A")

        if result.get("confidence_distribution"):
            print("\n  Confidence distribution:")
            for bucket, count in sorted(result["confidence_distribution"].items(), reverse=True):
                bar = "#" * count
                print(f"    {bucket}: {count:>3d}  {bar}")

    print()


async def main() -> None:
    # Pure-Python demos (no tools needed)
    demo_normalization()
    demo_fuzzy_matching()
    demo_composite_scoring()
    demo_ship_name_index()

    # Tool-based demos
    await demo_voyage_full_with_confidence()
    await demo_audit_links()

    print("=" * 70)
    print("  Entity resolution demo complete!")
    print("  v0.16.0 adds fuzzy matching, confidence scores, and link auditing.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
