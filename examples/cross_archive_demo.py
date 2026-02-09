#!/usr/bin/env python3
"""
Cross-Archive Linking Demo -- chuk-mcp-maritime-archives

Demonstrates the maritime_get_voyage_full tool, which returns a unified
view of a voyage with all linked records: wreck, vessel, hull profile,
and CLIWOC ship track — in a single call.

Compare this to batavia_case_study_demo.py, which calls 10+ tools
individually to assemble the same information.

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


async def main() -> None:
    runner = ToolRunner()

    print("=" * 70)
    print("  CROSS-ARCHIVE LINKING DEMO")
    print("  One tool call to rule them all")
    print("=" * 70)

    # ---- Step 1: Search for the Batavia voyage --------------------------
    print("\n  Step 1: Finding the Batavia voyage...")
    voyages = await runner.run("maritime_search_voyages", ship_name="Batavia")

    if "error" in voyages:
        print(f"\n  API unavailable: {voyages['error']}")
        return

    if voyages["voyage_count"] == 0:
        print("\n  No Batavia voyages found.")
        return

    voyage_id = voyages["voyages"][0]["voyage_id"]
    print(f"  Found: {voyage_id}")

    # ---- Step 2: Get unified view with ALL linked records ---------------
    print("\n  Step 2: Calling maritime_get_voyage_full (single call)...")
    result = await runner.run("maritime_get_voyage_full", voyage_id=voyage_id)

    if "error" in result:
        print(f"\n  Error: {result['error']}")
        return

    print(f"\n  {result['message']}")

    # ---- Voyage details -------------------------------------------------
    v = result["voyage"]
    print("\n" + "-" * 70)
    print("  VOYAGE")
    print("-" * 70)
    print(f"  ID:        {v.get('voyage_id', '?')}")
    print(f"  Ship:      {v.get('ship_name', '?')}")
    print(f"  Captain:   {v.get('captain', 'Unknown')}")
    print(f"  Type:      {v.get('ship_type', '?')}")
    print(f"  Route:     {v.get('departure_port', '?')} -> {v.get('destination_port', '?')}")
    print(f"  Departed:  {v.get('departure_date', '?')}")
    print(f"  Fate:      {v.get('fate', '?')}")

    if v.get("particulars"):
        print("\n  Particulars:")
        _wrap_print(v["particulars"])

    # ---- Wreck record (if linked) ---------------------------------------
    if result.get("wreck"):
        w = result["wreck"]
        print("\n" + "-" * 70)
        print("  LINKED WRECK RECORD")
        print("-" * 70)
        print(f"  Wreck ID:  {w.get('wreck_id', '?')}")
        print(f"  Lost:      {w.get('loss_date', '?')}")
        print(f"  Cause:     {w.get('loss_cause', '?')}")
        print(f"  Region:    {w.get('region', '?')}")
        print(f"  Location:  {w.get('loss_location', '?')}")
        print(f"  Status:    {w.get('status', '?')}")
        if w.get("position"):
            pos = w["position"]
            print(f"  Position:  {pos.get('lat')}, {pos.get('lon')}")
        if w.get("depth_estimate_m"):
            print(f"  Depth:     ~{w['depth_estimate_m']}m")
        if w.get("cargo_value_guilders"):
            print(f"  Cargo:     {w['cargo_value_guilders']:,.0f} guilders")

    # ---- Vessel record (if linked) --------------------------------------
    if result.get("vessel"):
        vs = result["vessel"]
        print("\n" + "-" * 70)
        print("  LINKED VESSEL RECORD")
        print("-" * 70)
        print(f"  Vessel ID: {vs.get('vessel_id', '?')}")
        print(f"  Name:      {vs.get('name', '?')}")
        print(f"  Type:      {vs.get('type', '?')}")
        print(f"  Tonnage:   {vs.get('tonnage', '?')} lasten")
        print(f"  Built:     {vs.get('built_year', '?')}")
        print(f"  Chamber:   {vs.get('chamber', '?')}")
        n_voyages = len(vs.get("voyage_ids", []))
        print(f"  Voyages:   {n_voyages}")

    # ---- Hull profile (if linked) ---------------------------------------
    if result.get("hull_profile"):
        hp = result["hull_profile"]
        print("\n" + "-" * 70)
        print("  LINKED HULL PROFILE")
        print("-" * 70)
        print(f"  Ship type: {hp.get('ship_type', '?')}")
        if hp.get("description"):
            _wrap_print(hp["description"])
        dims = hp.get("dimensions_typical", {})
        if dims:
            length = dims.get("length_m", {}).get("typical", "?")
            beam = dims.get("beam_m", {}).get("typical", "?")
            draught = dims.get("draught_m", {}).get("typical", "?")
            print(f"  Dimensions: {length}m x {beam}m, draught {draught}m")

    # ---- CLIWOC track (if linked) ---------------------------------------
    if result.get("cliwoc_track"):
        ct = result["cliwoc_track"]
        print("\n" + "-" * 70)
        print("  LINKED CLIWOC TRACK")
        print("-" * 70)
        print(f"  CLIWOC ID: {ct.get('voyage_id', '?')}")
        print(f"  Nation:    {ct.get('nationality', '?')}")
        print(f"  Ship:      {ct.get('ship_name', '?')}")
        print(f"  Company:   {ct.get('company', '?')}")
        print(f"  Period:    {ct.get('start_date', '?')} to {ct.get('end_date', '?')}")
        print(f"  Positions: {ct.get('position_count', '?')}")

    # ---- Summary --------------------------------------------------------
    links = result.get("links_found", [])
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"\n  Links found: {', '.join(links) if links else 'none'}")
    print("\n  This unified view was assembled from a SINGLE tool call:")
    print(f'    maritime_get_voyage_full(voyage_id="{voyage_id}")')
    print("\n  It automatically followed links across:")
    print("    - DAS voyage database")
    print("    - MAARER wreck records (via voyage_id)")
    print("    - DAS vessel registry (via voyage_ids)")
    print("    - Hull profile data (via ship_type)")
    print("    - CLIWOC 2.1 ship tracks (via DAS number or ship name)")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
