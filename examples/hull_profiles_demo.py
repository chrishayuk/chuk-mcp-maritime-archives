#!/usr/bin/env python3
"""
Hull Profiles Demo -- chuk-mcp-maritime-archives

Explore the hydrodynamic hull profiles for six VOC ship types.
Each profile contains dimensions, drag coefficients, windage area,
and sinking characteristics -- essential data for drift modelling
and wreck search planning.

Demonstrates:
    maritime_list_hull_profiles
    maritime_get_hull_profile (multiple ship types)

Usage:
    python examples/hull_profiles_demo.py
"""

import asyncio

from tool_runner import ToolRunner


async def main() -> None:
    runner = ToolRunner()

    print("=" * 60)
    print("chuk-mcp-maritime-archives -- Hull Profiles Demo")
    print("=" * 60)

    # List available ship types
    profiles_list = await runner.run("maritime_list_hull_profiles")
    print(f"\nAvailable hull profiles ({profiles_list['count']}):")
    for st in profiles_list["ship_types"]:
        print(f"  - {st}")

    # Examine each profile
    for ship_type in profiles_list["ship_types"]:
        print(f"\n{'=' * 60}")
        print(f"  {ship_type.upper()}")
        print(f"{'=' * 60}")

        result = await runner.run("maritime_get_hull_profile", ship_type=ship_type)
        profile = result["profile"]

        # Description
        if profile.get("description"):
            print(f"  {profile['description']}")

        # Dimensions
        dims = profile.get("dimensions_typical", {})
        if dims:
            print("\n  Dimensions (typical):")
            for key in ["length_m", "beam_m", "draught_m"]:
                d = dims.get(key, {})
                if d:
                    print(
                        f"    {key:12s}  min={d.get('min', '?'):6}  typical={d.get('typical', '?'):6}  max={d.get('max', '?'):6}"
                    )

        # Tonnage
        tonnage = profile.get("tonnage_range_lasten", {})
        if tonnage:
            print(f"\n  Tonnage: {tonnage.get('min', '?')}-{tonnage.get('max', '?')} lasten")

        # Hydrodynamics
        hydro = profile.get("hydrodynamics", {})
        if hydro:
            print("\n  Hydrodynamics:")
            for key, value in hydro.items():
                if isinstance(value, dict):
                    print(f"    {key}:")
                    for k, v in value.items():
                        print(f"      {k}: {v}")
                else:
                    print(f"    {key}: {value}")

        # Sinking characteristics
        sinking = profile.get("sinking_characteristics", {})
        if sinking:
            print("\n  Sinking Characteristics:")
            for key, value in sinking.items():
                if isinstance(value, dict):
                    print(f"    {key}:")
                    for k, v in value.items():
                        print(f"      {k}: {v}")
                else:
                    print(f"    {key}: {value}")

        # LLM guidance
        guidance = profile.get("llm_guidance")
        if guidance:
            print(f"\n  LLM Guidance: {guidance[:120]}...")

    # Text mode comparison
    print(f"\n{'=' * 60}")
    print("Text Mode Output for retourschip:")
    print(f"{'=' * 60}")
    text = await runner.run_text("maritime_get_hull_profile", ship_type="retourschip")
    print(text)

    print(f"\n{'=' * 60}")
    print("Demo complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
