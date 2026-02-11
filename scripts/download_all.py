#!/usr/bin/env python3
"""
Download and generate all maritime archive data.

Runs each archive-specific download/generate script to produce the
local JSON data files used by the MCP server.  All scripts support
the cache-check pattern: existing data is reused unless --force is set.

Usage:
    python scripts/download_all.py            # cache-aware (skip recent files)
    python scripts/download_all.py --force    # force re-download/regeneration
"""

import subprocess
import sys
from pathlib import Path

from download_utils import parse_args

SCRIPTS_DIR = Path(__file__).resolve().parent


def run_script(name: str, force: bool = False) -> bool:
    """Run a download/generate script, passing --force if requested."""
    script = SCRIPTS_DIR / name
    if not script.exists():
        print(f"\n  Skipping {name} (not found)")
        return True  # not a failure

    cmd = [sys.executable, str(script)]
    if force:
        cmd.append("--force")

    print(f"\n{'=' * 60}")
    print(f"Running {name}{'  --force' if force else ''}...")
    print(f"{'=' * 60}\n")
    result = subprocess.run(cmd, check=False)
    return result.returncode == 0


def main() -> None:
    args = parse_args("Download all maritime archive data")

    print("Maritime Archives — Download All Data")
    print("=" * 60)
    if args.force:
        print("  Mode: FORCE (re-download/regenerate all data)")
    else:
        print("  Mode: cache-aware (skip recent files)")

    scripts = [
        # Downloads from external sources
        "download_das.py",  # VOC voyages/vessels/wrecks from Huygens DAS
        "download_cliwoc.py",  # CLIWOC ship tracks (~261K positions)
        "download_crew.py",  # VOC crew from Nationaal Archief (~774K records)
        "download_cargo.py",  # BGB cargo from Huygens/Zenodo
        "download_eic.py",  # EIC from ThreeDecks / curated
        # Curated data generation
        "generate_carreira.py",  # Portuguese Carreira da India
        "generate_galleon.py",  # Spanish Manila Galleon
        "generate_soic.py",  # Swedish East India Company
        # Reference data
        "generate_reference.py",  # Gazetteer, routes, hull profiles
        "generate_speed_profiles.py",  # CLIWOC-derived speed statistics
    ]

    results = {}
    for script in scripts:
        results[script] = run_script(script, force=args.force)

    print(f"\n{'=' * 60}")
    print("Summary:")
    for script, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {script}: {status}")
    print(f"{'=' * 60}")

    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
