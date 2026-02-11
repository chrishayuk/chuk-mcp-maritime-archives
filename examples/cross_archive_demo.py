#!/usr/bin/env python3
"""
Cross-Archive Linking Demo -- chuk-mcp-maritime-archives

Demonstrates the maritime_get_voyage_full tool across multiple archives:
DAS (Dutch), EIC (English), Carreira (Portuguese), Galleon (Spanish),
and SOIC (Swedish). Returns a unified view of a voyage with all linked
records: wreck, vessel, hull profile, and CLIWOC ship track -- in a
single call.

The new archives (EIC, Carreira, Galleon, SOIC) work offline with
local curated data. DAS requires network access.

Usage:
    python examples/cross_archive_demo.py
"""

import asyncio

from tool_runner import ToolRunner


def _wrap_print(text: str, width: int = 66, indent: str = "    ") -> None:
    """Word-wrap and print a long string."""
    words = text.split()
    line = indent
    for word in words:
        if len(line) + len(word) + 1 > width:
            print(line)
            line = indent + word
        else:
            line += " " + word if line.strip() else indent + word
    if line.strip():
        print(line)


def _print_voyage_full(result: dict) -> None:
    """Print a unified voyage_full result."""
    v = result["voyage"]
    print(f"  Archive:   {v.get('archive', '?')}")
    print(f"  ID:        {v.get('voyage_id', '?')}")
    print(f"  Ship:      {v.get('ship_name', '?')}")
    print(f"  Captain:   {v.get('captain', 'Unknown')}")
    print(f"  Route:     {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}")
    print(f"  Departed:  {v.get('departure_date', '?')}")
    print(f"  Fate:      {v.get('fate', '?')}")

    if v.get("particulars"):
        print("  Details:")
        _wrap_print(v["particulars"])

    if result.get("wreck"):
        w = result["wreck"]
        print(f"\n  LINKED WRECK:")
        print(f"    Wreck ID:  {w.get('wreck_id', '?')}")
        print(f"    Lost:      {w.get('loss_date', '?')}  Cause: {w.get('loss_cause', '?')}")
        print(f"    Location:  {w.get('loss_location', '?')}")
        print(f"    Status:    {w.get('status', '?')}")
        if w.get("position"):
            pos = w["position"]
            print(f"    Position:  {pos.get('lat')}, {pos.get('lon')} (+/-{pos.get('uncertainty_km', '?')}km)")
        if w.get("depth_estimate_m"):
            print(f"    Depth:     ~{w['depth_estimate_m']}m")

    if result.get("vessel"):
        vs = result["vessel"]
        print(f"\n  LINKED VESSEL:")
        print(f"    Name: {vs.get('name', '?')}  Type: {vs.get('type', '?')}  Built: {vs.get('built_year', '?')}")

    if result.get("hull_profile"):
        hp = result["hull_profile"]
        print(f"\n  LINKED HULL PROFILE: {hp.get('ship_type', '?')}")

    if result.get("cliwoc_track"):
        ct = result["cliwoc_track"]
        print(f"\n  LINKED CLIWOC TRACK:")
        print(f"    Nation: {ct.get('nationality', '?')}  Ship: {ct.get('ship_name', '?')}")
        print(f"    Period: {ct.get('start_date', '?')} to {ct.get('end_date', '?')}")
        print(f"    Positions: {ct.get('position_count', '?')}")

    links = result.get("links_found", [])
    print(f"\n  Links found: {', '.join(links) if links else 'none'}")


async def main() -> None:
    runner = ToolRunner()

    print("=" * 70)
    print("  CROSS-ARCHIVE LINKING DEMO")
    print("  Unified voyage views across 8 maritime archives")
    print("=" * 70)

    # ---- 1: EIC - Earl of Abergavenny (offline) -------------------------
    print("\n" + "-" * 70)
    print("  1. EIC: Earl of Abergavenny (eic:0062)")
    print("     Captain Wordsworth's tragic final voyage, 1805")
    print("-" * 70)

    result = await runner.run("maritime_get_voyage_full", voyage_id="eic:0062")
    if "error" not in result:
        _print_voyage_full(result)
    else:
        print(f"  Error: {result['error']}")

    # ---- 2: Carreira - Vasco da Gama's first voyage (offline) -----------
    print("\n" + "-" * 70)
    print("  2. CARREIRA: Vasco da Gama's first voyage (carreira:0001)")
    print("     The voyage that opened the sea route to India, 1497")
    print("-" * 70)

    result = await runner.run("maritime_get_voyage_full", voyage_id="carreira:0001")
    if "error" not in result:
        _print_voyage_full(result)
    else:
        print(f"  Error: {result['error']}")

    # ---- 3: Galleon - San Diego (offline) --------------------------------
    print("\n" + "-" * 70)
    print("  3. GALLEON: San Diego (galleon:0009)")
    print("     Sunk by the Dutch off Fortune Island, 1600")
    print("-" * 70)

    result = await runner.run("maritime_get_voyage_full", voyage_id="galleon:0009")
    if "error" not in result:
        _print_voyage_full(result)
    else:
        print(f"  Error: {result['error']}")

    # ---- 4: SOIC - Gotheborg (offline) -----------------------------------
    print("\n" + "-" * 70)
    print("  4. SOIC: Gotheborg (soic:0002)")
    print("     Sweden's most famous shipwreck, sank within sight of home, 1745")
    print("-" * 70)

    # Find the Gotheborg wreck voyage
    search = await runner.run("maritime_search_voyages", archive="soic", ship_name="Gotheborg")
    gotheborg_id = None
    if "error" not in search and search["voyage_count"] > 0:
        # Pick the wrecked voyage
        for v in search["voyages"]:
            if v.get("fate") == "wrecked":
                gotheborg_id = v["voyage_id"]
                break
        if not gotheborg_id:
            gotheborg_id = search["voyages"][0]["voyage_id"]

    if gotheborg_id:
        result = await runner.run("maritime_get_voyage_full", voyage_id=gotheborg_id)
        if "error" not in result:
            _print_voyage_full(result)
        else:
            print(f"  Error: {result['error']}")
    else:
        print("  Gotheborg not found in SOIC archive")

    # ---- 5: DAS - Batavia (network-dependent) ----------------------------
    print("\n" + "-" * 70)
    print("  5. DAS: Batavia (network-dependent)")
    print("     The most famous VOC shipwreck, 1629")
    print("-" * 70)

    voyages = await runner.run("maritime_search_voyages", ship_name="Batavia")
    if "error" in voyages:
        print(f"  DAS API unavailable: {voyages['error']}")
        print("  (DAS requires network access -- skipping)")
    elif voyages["voyage_count"] == 0:
        print("  No Batavia voyages found.")
    else:
        voyage_id = voyages["voyages"][0]["voyage_id"]
        result = await runner.run("maritime_get_voyage_full", voyage_id=voyage_id)
        if "error" not in result:
            _print_voyage_full(result)
        else:
            print(f"  Error: {result['error']}")

    # ---- Summary ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print()
    print("  maritime_get_voyage_full assembles unified views from:")
    print("    - 5 voyage archives (DAS, EIC, Carreira, Galleon, SOIC)")
    print("    - 5 wreck archives  (MAARER, EIC, Carreira, Galleon, SOIC)")
    print("    - DAS vessel registry + hull profiles")
    print("    - CLIWOC 2.1 ship tracks (linked by nationality)")
    print()
    print("  Each call automatically follows cross-archive links:")
    print("    voyage -> wreck (by voyage_id)")
    print("    voyage -> vessel (by reverse index)")
    print("    vessel -> hull profile (by ship_type)")
    print("    voyage -> CLIWOC track (by ship name + nationality)")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
