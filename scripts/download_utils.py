"""
Shared download / cache utilities for maritime data scripts.

Provides the cache-check-download pattern used by all download and
generate scripts in this project.

Functions:
    parse_args       -- Standard --force / --cache-max-age argument parser
    is_cached        -- Check whether a local file is recent enough to reuse
    download_file    -- Download a URL with progress reporting
    save_json        -- Write JSON with size reporting
    ensure_cache_dir -- Create data/cache/ if needed

Constants:
    PROJECT_ROOT, DATA_DIR, CACHE_DIR
"""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

DEFAULT_CACHE_MAX_AGE_HOURS = 24 * 7  # 1 week

USER_AGENT = "chuk-mcp-maritime-archives/0.7.0"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args(description: str) -> argparse.Namespace:
    """Standard argument parser for download / generate scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download/regeneration even if cached data exists",
    )
    parser.add_argument(
        "--cache-max-age",
        type=int,
        default=DEFAULT_CACHE_MAX_AGE_HOURS,
        dest="cache_max_age",
        help=(
            f"Max cache age in hours before re-downloading (default: {DEFAULT_CACHE_MAX_AGE_HOURS})"
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Cache checking
# ---------------------------------------------------------------------------


def is_cached(
    filepath: Path,
    max_age_hours: int = DEFAULT_CACHE_MAX_AGE_HOURS,
) -> bool:
    """Return True if *filepath* exists, is non-empty, and younger than *max_age_hours*."""
    if not filepath.exists():
        return False
    if filepath.stat().st_size == 0:
        return False
    age_hours = (time.time() - filepath.stat().st_mtime) / 3600
    return age_hours < max_age_hours


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------


def _progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    """Callback for urlretrieve progress."""
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100.0, downloaded / total_size * 100)
        mb = downloaded / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        sys.stdout.write(f"\r  {mb:.1f} / {total_mb:.1f} MB ({pct:.0f}%)")
    else:
        mb = downloaded / (1024 * 1024)
        sys.stdout.write(f"\r  {mb:.1f} MB downloaded")
    sys.stdout.flush()


def download_file(
    url: str,
    dest: Path,
    description: str,
    timeout: int = 300,
) -> Path:
    """
    Download *url* to *dest* with progress reporting.

    Returns the destination path on success.
    Raises on failure.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {description}...")
    print(f"    {url}")

    # Build request with User-Agent
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    # urlretrieve doesn't accept Request objects, so do it manually
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        block_size = 65536
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                _progress_hook(downloaded // block_size, block_size, total)
    print()  # newline after progress
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"  Saved {dest.name} ({size_mb:.1f} MB)")
    return dest


# ---------------------------------------------------------------------------
# JSON saving
# ---------------------------------------------------------------------------


def save_json(
    data: list | dict,
    filename: str,
    data_dir: Path = DATA_DIR,
    compact: bool = False,
) -> Path:
    """
    Write *data* as JSON to *data_dir*/*filename*.

    Set compact=True for large datasets (crew, cargo) to use
    minimal whitespace and reduce file size.

    Returns the output path.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = path.stat().st_size / 1024
    if size_kb > 1024:
        print(f"  Wrote {path.name} ({size_kb / 1024:.1f} MB)")
    else:
        print(f"  Wrote {path.name} ({size_kb:.0f} KB)")
    return path


# ---------------------------------------------------------------------------
# Cache directory
# ---------------------------------------------------------------------------


def ensure_cache_dir() -> Path:
    """Create and return the data/cache/ directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR
