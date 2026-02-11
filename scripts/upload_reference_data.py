#!/usr/bin/env python3
"""
Upload reference data files to a chuk-artifacts store.

Reads each JSON file from data/, stores it as an artifact, then creates
a manifest artifact mapping filenames to artifact IDs.  Print the
manifest artifact ID at the end — set MARITIME_REFERENCE_MANIFEST to
this value in .env so that new servers can preload data from the store
instead of requiring local files.

Requires environment variables for the artifact store (see .env.example).

Run from the project root:

    python scripts/upload_reference_data.py
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Reference data files to upload
DATA_FILES = [
    "cliwoc_tracks.json",
    "voyages.json",
    "vessels.json",
    "wrecks.json",
    "speed_profiles.json",
    "gazetteer.json",
    "routes.json",
    "hull_profiles.json",
    "eic_voyages.json",
    "eic_wrecks.json",
    "carreira_voyages.json",
    "carreira_wrecks.json",
    "galleon_voyages.json",
    "galleon_wrecks.json",
    "soic_voyages.json",
    "soic_wrecks.json",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def upload_all() -> str:
    """Upload data files and return the manifest artifact ID."""
    from chuk_artifacts import ArtifactStore

    # Build store from env vars (same logic as server.py)
    provider = os.environ.get("CHUK_ARTIFACTS_PROVIDER", "memory")
    session_provider = "redis" if os.environ.get("REDIS_URL") else "memory"

    store_kwargs: dict = {
        "storage_provider": provider,
        "session_provider": session_provider,
    }

    bucket = os.environ.get("BUCKET_NAME")
    artifacts_path = os.environ.get("CHUK_ARTIFACTS_PATH")

    if provider == "s3" and bucket:
        store_kwargs["bucket"] = bucket
    elif provider == "filesystem" and artifacts_path:
        store_kwargs["bucket"] = artifacts_path

    store = ArtifactStore(**store_kwargs)
    logger.info("Artifact store created (provider: %s)", provider)

    manifest: dict[str, str] = {}

    for filename in DATA_FILES:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            logger.warning("Skipping %s (file not found)", filename)
            continue

        data = filepath.read_bytes()
        size_mb = len(data) / (1024 * 1024)

        artifact_id = await store.store(
            data=data,
            mime="application/json",
            summary=f"Maritime reference data: {filename}",
            meta={"filename": filename, "size_bytes": len(data)},
            filename=filename,
            scope="sandbox",
            ttl=0,
        )

        manifest[filename] = artifact_id
        logger.info("  Uploaded %s (%.1f MB) → %s", filename, size_mb, artifact_id)

    if not manifest:
        logger.error("No files uploaded. Check that data/ directory contains JSON files.")
        sys.exit(1)

    # Store the manifest itself
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    manifest_id = await store.store(
        data=manifest_bytes,
        mime="application/json",
        summary=f"Reference data manifest ({len(manifest)} files)",
        meta={"file_count": len(manifest)},
        filename="reference_manifest.json",
        scope="sandbox",
        ttl=0,
    )

    return manifest_id


def main() -> None:
    # Load .env from project root
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("Loaded %s", env_path)

    logger.info("Uploading %d reference data files from %s", len(DATA_FILES), DATA_DIR)
    manifest_id = asyncio.run(upload_all())

    print()
    print("=" * 60)
    print(f"Manifest artifact ID: {manifest_id}")
    print()
    print("Add this to your .env file:")
    print(f"  MARITIME_REFERENCE_MANIFEST={manifest_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
