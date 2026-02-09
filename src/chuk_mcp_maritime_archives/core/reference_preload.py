"""
Preload reference data from artifact store to local data/ directory.

Called by server.py before async_server is imported, so that module-level
data loaders (_load_tracks, _load_routes, etc.) find their files.

Falls back silently if the manifest env var is not set, the store is
unavailable, or any download fails -- local data/ files are used instead.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from ..constants import EnvVar

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


async def _preload_async(data_dir: Path) -> bool:
    """Download reference data files from artifact store.

    Returns True if at least one file was downloaded.
    """
    manifest_id = os.environ.get(EnvVar.REFERENCE_MANIFEST)
    if not manifest_id:
        return False

    try:
        from chuk_mcp_server import get_artifact_store

        store = get_artifact_store()
        if store is None:
            logger.debug("No artifact store available for reference preload")
            return False
    except Exception as e:
        logger.debug("Cannot get artifact store for preload: %s", e)
        return False

    # Retrieve manifest
    try:
        manifest_bytes = await store.retrieve(manifest_id)
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except Exception as e:
        logger.warning("Failed to retrieve reference manifest %s: %s", manifest_id, e)
        return False

    # Ensure data dir exists
    data_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for filename, artifact_id in manifest.items():
        target = data_dir / filename
        # Skip if local file already exists and is non-empty
        if target.exists() and target.stat().st_size > 0:
            logger.debug("Skipping %s (already present locally)", filename)
            continue
        try:
            data = await store.retrieve(artifact_id)
            target.write_bytes(data)
            size_mb = len(data) / (1024 * 1024)
            logger.info("Preloaded %s (%.1f MB) from artifact store", filename, size_mb)
            downloaded += 1
        except Exception as e:
            logger.warning("Failed to preload %s: %s", filename, e)

    if downloaded > 0:
        logger.info("Preloaded %d reference data files from artifact store", downloaded)
    return downloaded > 0


def preload_reference_data(data_dir: Path | None = None) -> bool:
    """Synchronous entry point for preloading reference data.

    Runs the async preload in a new event loop. Safe to call from
    synchronous code (e.g., server.py main()).

    Returns True if any files were downloaded.
    """
    manifest_id = os.environ.get(EnvVar.REFERENCE_MANIFEST)
    if not manifest_id:
        logger.debug("MARITIME_REFERENCE_MANIFEST not set; using local data files")
        return False

    target_dir = data_dir or _DEFAULT_DATA_DIR

    try:
        return asyncio.run(_preload_async(target_dir))
    except Exception as e:
        logger.warning("Reference data preload failed: %s", e)
        return False
