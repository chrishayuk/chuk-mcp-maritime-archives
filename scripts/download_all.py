#!/usr/bin/env python3
"""
Download all maritime archive data.

Runs each archive-specific download script to produce the
local JSON data files used by the MCP server.

Usage:
    python scripts/download_all.py
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def run_script(name: str) -> bool:
    """Run a download script and return True on success."""
    script = SCRIPTS_DIR / name
    print(f"\n{'=' * 60}")
    print(f"Running {name}...")
    print(f"{'=' * 60}\n")
    result = subprocess.run([sys.executable, str(script)], check=False)
    return result.returncode == 0


def main() -> None:
    print("Maritime Archives — Download All Data")
    print("=" * 60)

    scripts = [
        "download_das.py",
        "download_cliwoc.py",
        "generate_eic.py",
        "generate_carreira.py",
        "generate_galleon.py",
        "generate_soic.py",
    ]

    results = {}
    for script in scripts:
        results[script] = run_script(script)

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
