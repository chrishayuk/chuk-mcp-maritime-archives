#!/usr/bin/env python3
"""
Cargo Trade Demo -- chuk-mcp-maritime-archives

Explore VOC cargo manifests and trade goods. The BGB archive
contains records of goods shipped between Asia and the Netherlands,
1700-1795, including spices, textiles, porcelain, silver, and more.

Demonstrates:
    maritime_search_cargo (by commodity, by value)
    maritime_get_cargo_manifest (full manifest from search results)

Usage:
    python examples/cargo_trade_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Cargo Trade Demo")
    print("=" * 60)

    # ----- Search all cargo -----------------------------------------
    print("\n1. Search all cargo records")
    print("-" * 40)

    all_cargo = await runner.run("maritime_search_cargo", max_results=20)

    if "error" in all_cargo:
        print(f"   API unavailable: {all_cargo['error']}")
        print("   (This demo requires network access to the BGB archive)")
        return

    print(f"   Total cargo records: {all_cargo['cargo_count']}")

    total_value = 0
    commodities: dict[str, float] = {}
    first_voyage_id = None

    for c in all_cargo["cargo"]:
        qty = f"{c['quantity']} {c.get('unit', '')}" if c.get("quantity") else "?"
        val = c.get("value_guilders") or 0
        val_str = f" ({val:,.0f} guilders)" if val else ""
        print(f"\n   {c['cargo_id']}: {c['commodity']}")
        print(f"     Quantity: {qty}{val_str}")
        print(f"     Voyage: {c.get('voyage_id', '?')}")
        print(f"     Ship: {c.get('ship_name', '?')}")
        total_value += val
        commodities[c["commodity"]] = commodities.get(c["commodity"], 0) + val
        if first_voyage_id is None and c.get("voyage_id"):
            first_voyage_id = c["voyage_id"]

    if total_value:
        print(f"\n   Total value across all manifests: {total_value:,.0f} guilders")

    # ----- Commodity breakdown --------------------------------------
    if commodities:
        print("\n2. Value by commodity")
        print("-" * 40)

        for commodity, value in sorted(commodities.items(), key=lambda x: -x[1]):
            pct = (value / total_value * 100) if total_value else 0
            bar = "#" * int(pct / 2)
            print(f"   {commodity:15s}  {value:>12,.0f} guilders  ({pct:5.1f}%)  {bar}")

    # ----- Search by specific voyage --------------------------------
    if first_voyage_id:
        print(f"\n3. Cargo manifest for voyage {first_voyage_id}")
        print("-" * 40)

        manifest = await runner.run("maritime_get_cargo_manifest", voyage_id=first_voyage_id)

        if "cargo_entries" in manifest:
            print(f"   Manifest entries: {len(manifest['cargo_entries'])}")
            voyage_total = 0
            for entry in manifest["cargo_entries"]:
                qty = f"{entry.get('quantity', '?')} {entry.get('unit', '')}"
                val = entry.get("value_guilders") or 0
                voyage_total += val
                print(f"     {entry.get('commodity', '?'):15s}  {qty:>20s}  {val:>10,.0f} guilders")
            print(f"   {'':15s}  {'':>20s}  {'':>10s} ----------")
            print(f"   {'Total':15s}  {'':>20s}  {voyage_total:>10,.0f} guilders")
        else:
            print(f"   {manifest.get('error', 'No manifest found')}")
    else:
        print("\n3. (Skipped -- no voyage ID in cargo results)")

    # ----- Search by commodity --------------------------------------
    print("\n4. Search for pepper cargo")
    print("-" * 40)

    pepper = await runner.run("maritime_search_cargo", commodity="pepper")
    if "error" not in pepper:
        print(f"   Found {pepper['cargo_count']} pepper entries")
        for c in pepper["cargo"]:
            qty = f"{c.get('quantity', '?')} {c.get('unit', '')}"
            print(f"     {c.get('ship_name', '?')}: {qty}")
    else:
        print(f"   {pepper['error']}")

    # ----- Text output mode -----------------------------------------
    print("\n5. Text output mode")
    print("-" * 40)
    text = await runner.run_text("maritime_search_cargo")
    print(text)

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
