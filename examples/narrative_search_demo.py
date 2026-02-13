#!/usr/bin/env python3
"""
Narrative Search Demo -- chuk-mcp-maritime-archives

Demonstrates the full-text narrative search tool that searches across
all free-text fields (voyage particulars, wreck particulars, loss
location descriptions) in all 10 maritime archives.

Demonstrates:
    maritime_search_narratives (keyword, phrase, filters, pagination)

Usage:
    python examples/narrative_search_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 70)
    print("  NARRATIVE SEARCH DEMO")
    print("  Full-text search across all maritime archives")
    print("=" * 70)

    # ----- 1. Simple keyword search ------------------------------------------
    print("\n1. Simple keyword search: 'wrecked'")
    print("-" * 40)

    result = await runner.run("maritime_search_narratives", query="wrecked")
    if "error" not in result:
        print(f"   Total matches: {result['total_count']}")
        for r in result["results"][:5]:
            print(f"   [{r['record_type']}] {r['ship_name']:30s}  archive={r['archive']}")
            print(f"     ...{r['snippet'][:80]}...")
    else:
        print(f"   {result['error']}")

    # ----- 2. Phrase search --------------------------------------------------
    print("\n2. Phrase search: '\"Cape of Good Hope\"'")
    print("-" * 40)

    result = await runner.run("maritime_search_narratives", query='"Cape of Good Hope"')
    if "error" not in result:
        print(f"   Total matches: {result['total_count']}")
        for r in result["results"]:
            print(f"   [{r['record_type']}] {r['ship_name']:30s}  archive={r['archive']}")
            print(f"     Field: {r['field']}")
            print(f"     ...{r['snippet'][:100]}...")
    else:
        print(f"   {result['error']}")

    # ----- 3. Multi-word AND search ------------------------------------------
    print("\n3. Multi-word AND search: 'storm Cape'")
    print("-" * 40)

    result = await runner.run("maritime_search_narratives", query="storm Cape")
    if "error" not in result:
        print(f"   Total matches: {result['total_count']}")
        for r in result["results"]:
            print(f"   [{r['record_type']}] {r['ship_name']:30s}  archive={r['archive']}")
            print(f"     ...{r['snippet'][:100]}...")
    else:
        print(f"   {result['error']}")

    # ----- 4. Filter by record type (voyage only) ----------------------------
    print("\n4. Filter by record type: voyages mentioning 'harbour'")
    print("-" * 40)

    result = await runner.run("maritime_search_narratives", query="harbour", record_type="voyage")
    if "error" not in result:
        print(f"   Total matches: {result['total_count']} (voyages only)")
        for r in result["results"]:
            print(f"   [{r['record_type']}] {r['ship_name']:30s}  archive={r['archive']}")
    else:
        print(f"   {result['error']}")

    # ----- 5. Filter by record type (wreck only) -----------------------------
    print("\n5. Filter by record type: wrecks mentioning 'Philippines'")
    print("-" * 40)

    result = await runner.run(
        "maritime_search_narratives", query="Philippines", record_type="wreck"
    )
    if "error" not in result:
        print(f"   Total matches: {result['total_count']} (wrecks only)")
        for r in result["results"]:
            print(f"   [{r['record_type']}] {r['ship_name']:30s}  field={r['field']}")
    else:
        print(f"   {result['error']}")

    # ----- 6. Filter by archive ----------------------------------------------
    print("\n6. Filter by archive: EIC narratives mentioning 'Wrecked'")
    print("-" * 40)

    result = await runner.run("maritime_search_narratives", query="Wrecked", archive="eic")
    if "error" not in result:
        print(f"   Total matches: {result['total_count']} (EIC only)")
        for r in result["results"]:
            print(f"   [{r['record_type']}] {r['ship_name']:30s}")
            print(f"     ...{r['snippet'][:100]}...")
    else:
        print(f"   {result['error']}")

    # ----- 7. Pagination demo ------------------------------------------------
    print("\n7. Pagination: 'South Africa' (2 per page)")
    print("-" * 40)

    page = 1
    cursor = None
    while True:
        result = await runner.run(
            "maritime_search_narratives",
            query="South Africa",
            max_results=2,
            cursor=cursor,
        )
        if "error" in result:
            print(f"   {result['error']}")
            break
        print(f"   Page {page}: {len(result['results'])} results (total: {result['total_count']})")
        for r in result["results"]:
            print(f"     {r['record_id']:30s}  {r['ship_name']}")
        if not result.get("has_more"):
            break
        cursor = result["next_cursor"]
        page += 1

    # ----- 8. Cross-archive comparison ---------------------------------------
    print("\n8. Cross-archive: 'coast' across all archives")
    print("-" * 40)

    result = await runner.run("maritime_search_narratives", query="coast")
    if "error" not in result:
        archives: dict[str, int] = {}
        for r in result["results"]:
            archives[r["archive"]] = archives.get(r["archive"], 0) + 1
        print(f"   Total matches: {result['total_count']}")
        for arc, count in sorted(archives.items()):
            print(f"     {arc:15s}: {count} matches")
    else:
        print(f"   {result['error']}")

    # ----- 9. Text output mode -----------------------------------------------
    print("\n9. Text output mode")
    print("-" * 40)

    text = await runner.run_text("maritime_search_narratives", query="Gothenburg")
    print(text)

    print("\n" + "=" * 70)
    print("  Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
