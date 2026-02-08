#!/usr/bin/env python3
"""
Batavia Case Study -- chuk-mcp-maritime-archives

A complete investigation of the VOC ship Batavia, which was wrecked
on the Houtman Abrolhos reef off Western Australia in June 1629.
This demo shows how an LLM would chain multiple tools together to
build a comprehensive picture of a maritime incident.

Demonstrates the full tool chain:
    maritime_search_voyages   -> Find the Batavia voyage
    maritime_get_voyage       -> Get full voyage details
    maritime_search_wrecks    -> Find the wreck record
    maritime_get_wreck        -> Get wreck position and status
    maritime_search_crew      -> Find crew members aboard
    maritime_get_crew_member  -> Get individual crew details
    maritime_search_cargo     -> Find cargo carried
    maritime_get_hull_profile -> Ship type characteristics
    maritime_assess_position  -> Position quality for the wreck
    maritime_export_geojson   -> Map the wreck location

Usage:
    python examples/batavia_case_study_demo.py
"""

import asyncio
import json

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 70)
    print("  THE BATAVIA -- A Complete Maritime Investigation")
    print("  VOC Ship Wrecked 4 June 1629, Houtman Abrolhos, Western Australia")
    print("=" * 70)

    # ----- Phase 1: Find the voyage ---------------------------------
    print("\n" + "-" * 70)
    print("  PHASE 1: Voyage Search")
    print("-" * 70)

    voyages = await runner.run("maritime_search_voyages", ship_name="Batavia")
    print(f"\n  Found {voyages['voyage_count']} matching voyage(s)")

    voyage_id = None
    for v in voyages["voyages"]:
        print(f"\n  Voyage: {v['voyage_id']}")
        print(f"    Ship: {v['ship_name']}")
        print(f"    Captain: {v.get('captain', 'Unknown')}")
        print(f"    From: {v.get('departure_port', '?')}")
        print(f"    To: {v.get('destination_port', '?')}")
        print(f"    Departed: {v.get('departure_date', '?')}")
        print(f"    Fate: {v.get('fate', '?')}")
        voyage_id = v["voyage_id"]

    # Full voyage details
    if voyage_id:
        print(f"\n  Fetching full voyage record for {voyage_id}...")
        detail = await runner.run("maritime_get_voyage", voyage_id=voyage_id)
        voyage = detail["voyage"]

        if voyage.get("summary"):
            print(f"\n  Summary:")
            # Word-wrap the summary
            words = voyage["summary"].split()
            line = "    "
            for word in words:
                if len(line) + len(word) + 1 > 68:
                    print(line)
                    line = "    " + word
                else:
                    line += " " + word if line.strip() else "    " + word
            if line.strip():
                print(line)

        if voyage.get("incident"):
            inc = voyage["incident"]
            print(f"\n  Incident Details:")
            print(f"    Date: {inc.get('date', '?')}")
            print(f"    Cause: {inc.get('cause', '?')}")
            print(f"    Lives lost: {inc.get('lives_lost', '?')}")
            print(f"    Survivors: {inc.get('survivors', '?')}")
            if inc.get("position"):
                pos = inc["position"]
                print(f"    Position: {pos.get('lat')}S, {pos.get('lon')}E")

    # ----- Phase 2: Wreck record ------------------------------------
    print("\n" + "-" * 70)
    print("  PHASE 2: Wreck Investigation")
    print("-" * 70)

    wrecks = await runner.run("maritime_search_wrecks", ship_name="Batavia")
    print(f"\n  Found {wrecks['wreck_count']} wreck record(s)")

    wreck_id = None
    for w in wrecks["wrecks"]:
        print(f"\n  Wreck: {w['wreck_id']}")
        print(f"    Ship: {w['ship_name']}")
        print(f"    Lost: {w.get('loss_date', '?')}")
        print(f"    Cause: {w.get('loss_cause', '?')}")
        print(f"    Region: {w.get('region', '?')}")
        print(f"    Status: {w.get('status', '?')}")
        wreck_id = w["wreck_id"]

    if wreck_id:
        wreck_detail = await runner.run("maritime_get_wreck", wreck_id=wreck_id)
        wd = wreck_detail["wreck"]
        if wd.get("depth_estimate_m"):
            print(f"    Depth: ~{wd['depth_estimate_m']}m")
        if wd.get("cargo_value_guilders"):
            print(f"    Cargo value: {wd['cargo_value_guilders']:,.0f} guilders")
        if wd.get("archaeological_notes"):
            print(f"    Notes: {wd['archaeological_notes'][:100]}...")

    # ----- Phase 3: Crew on board -----------------------------------
    print("\n" + "-" * 70)
    print("  PHASE 3: Crew Complement")
    print("-" * 70)

    crew = await runner.run("maritime_search_crew", ship_name="Batavia")

    if "error" not in crew:
        print(f"\n  Found {crew['crew_count']} crew record(s)")
        for c in crew["crew"]:
            rank = c.get("rank_english") or c.get("rank", "?")
            print(f"    {c['crew_id']}: {c['name']} ({rank})")

            # Get full crew member details
            member = await runner.run("maritime_get_crew_member", crew_id=c["crew_id"])
            if "crew_member" in member:
                m = member["crew_member"]
                if m.get("origin"):
                    print(f"      Origin: {m['origin']}")
                if m.get("monthly_pay_guilders"):
                    print(f"      Pay: {m['monthly_pay_guilders']} guilders/month")
    else:
        print(f"\n  No crew records found for Batavia in the sample data.")
        print(f"  (The Batavia crew would be found in the full VOC Opvarenden database.)")

    # ----- Phase 4: Cargo -------------------------------------------
    print("\n" + "-" * 70)
    print("  PHASE 4: Cargo Manifest")
    print("-" * 70)

    if voyage_id:
        cargo = await runner.run("maritime_search_cargo", voyage_id=voyage_id)

        if "error" not in cargo:
            print(f"\n  Found {cargo['cargo_count']} cargo entries")
            total_value = 0
            for c in cargo["cargo"]:
                qty = f"{c['quantity']} {c.get('unit', '')}" if c.get("quantity") else "unknown qty"
                val = f" ({c['value_guilders']:,.0f} guilders)" if c.get("value_guilders") else ""
                print(f"    {c['commodity']}: {qty}{val}")
                total_value += c.get("value_guilders") or 0
            if total_value:
                print(f"\n  Total manifest value: {total_value:,.0f} guilders")
        else:
            print(f"\n  No cargo records linked to this voyage in the sample data.")

    # ----- Phase 5: Ship characteristics ----------------------------
    print("\n" + "-" * 70)
    print("  PHASE 5: Vessel Characteristics")
    print("-" * 70)

    # Get the ship type from the voyage data
    ship_type = voyage.get("ship_type", "retourschip") if voyage_id else "retourschip"
    profile = await runner.run("maritime_get_hull_profile", ship_type=ship_type)
    p = profile["profile"]

    print(f"\n  Ship type: {p.get('ship_type', '?')}")
    if p.get("description"):
        print(f"  Description: {p['description'][:100]}...")

    dims = p.get("dimensions_typical", {})
    if dims:
        length = dims.get("length_m", {}).get("typical", "?")
        beam = dims.get("beam_m", {}).get("typical", "?")
        draught = dims.get("draught_m", {}).get("typical", "?")
        print(f"  Typical dimensions: {length}m x {beam}m, draught {draught}m")

    tonnage = p.get("tonnage_range_lasten", {})
    if tonnage:
        print(f"  Tonnage range: {tonnage.get('min', '?')}-{tonnage.get('max', '?')} lasten")

    # ----- Phase 6: Position assessment -----------------------------
    print("\n" + "-" * 70)
    print("  PHASE 6: Position Assessment")
    print("-" * 70)

    if wreck_id:
        assessment = await runner.run(
            "maritime_assess_position",
            wreck_id=wreck_id,
            source_description="GPS surveyed archaeological site, multiple dives",
        )
        a = assessment["assessment"]
        quality = a.get("assessment", {})
        print(f"\n  Quality score: {quality.get('quality_score', '?')}/1.0")
        print(f"  Quality label: {quality.get('quality_label', '?')}")
        print(f"  Uncertainty: {quality.get('uncertainty_type', '?')} (+/-{quality.get('uncertainty_radius_km', '?')}km)")

        recs = a.get("recommendations", {})
        if recs.get("for_drift_modelling"):
            print(f"\n  Drift modelling advice:")
            print(f"    {recs['for_drift_modelling'][:100]}...")
        if recs.get("for_search"):
            print(f"  Search advice:")
            print(f"    {recs['for_search'][:100]}...")

    # ----- Phase 7: GeoJSON export ----------------------------------
    print("\n" + "-" * 70)
    print("  PHASE 7: GeoJSON Export")
    print("-" * 70)

    if wreck_id:
        geojson = await runner.run(
            "maritime_export_geojson",
            wreck_ids=[wreck_id],
        )
        print(f"\n  Exported {geojson['feature_count']} feature(s)")
        print(f"\n  GeoJSON:")
        print(json.dumps(geojson["geojson"], indent=4))

    # ----- Summary --------------------------------------------------
    print("\n" + "=" * 70)
    print("  INVESTIGATION SUMMARY")
    print("=" * 70)
    print(f"""
  Ship:       Batavia (retourschip, ~600 lasten)
  Voyage:     {voyage_id or 'Unknown'}
  Commander:  {voyage.get('captain', 'Unknown') if voyage_id else 'Unknown'}
  Route:      Netherlands -> Batavia (Jakarta)
  Lost:       4 June 1629, Houtman Abrolhos reef, Western Australia
  Cause:      Struck Morning Reef at night
  Status:     Found -- extensively excavated since 1963
  Position:   28.49S, 113.79E (GPS-surveyed)

  This investigation used 10 different MCP tools chained together
  to build a comprehensive picture of a single maritime incident.
""")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
