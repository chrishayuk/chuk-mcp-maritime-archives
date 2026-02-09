"""
Synchronous entry point for chuk-mcp-maritime-archives.

Initialises the artifact store and launches the MCP server in
either stdio or HTTP mode.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .constants import EnvVar, ServerConfig, SessionProvider, StorageProvider

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)


def _init_artifact_store() -> bool:
    """
    Initialize the artifact store from environment variables.

    Returns:
        True if artifact store was initialized, False otherwise
    """
    provider = os.environ.get(EnvVar.ARTIFACTS_PROVIDER, StorageProvider.MEMORY)
    bucket = os.environ.get(EnvVar.BUCKET_NAME)
    redis_url = os.environ.get(EnvVar.REDIS_URL)
    artifacts_path = os.environ.get(EnvVar.ARTIFACTS_PATH)

    if provider == StorageProvider.S3:
        aws_key = os.environ.get(EnvVar.AWS_ACCESS_KEY_ID)
        aws_secret = os.environ.get(EnvVar.AWS_SECRET_ACCESS_KEY)

        if not all([bucket, aws_key, aws_secret]):
            logger.warning(
                "S3 provider configured but missing credentials. "
                f"Set {EnvVar.AWS_ACCESS_KEY_ID}, {EnvVar.AWS_SECRET_ACCESS_KEY}, "
                f"and {EnvVar.BUCKET_NAME}."
            )
            return False

    elif provider == StorageProvider.FILESYSTEM:
        if artifacts_path:
            path_obj = Path(artifacts_path)
            path_obj.mkdir(parents=True, exist_ok=True)
        else:
            logger.warning(
                f"Filesystem provider configured but {EnvVar.ARTIFACTS_PATH} not set. "
                "Defaulting to memory provider."
            )
            provider = StorageProvider.MEMORY

    try:
        from chuk_artifacts import ArtifactStore
        from chuk_mcp_server import set_global_artifact_store

        provider_str = provider.value if isinstance(provider, StorageProvider) else provider
        session_str = SessionProvider.REDIS.value if redis_url else SessionProvider.MEMORY.value

        store_kwargs: dict[str, Any] = {
            "storage_provider": provider_str,
            "session_provider": session_str,
        }

        if provider_str == StorageProvider.S3.value and bucket:
            store_kwargs["bucket"] = bucket
        elif provider_str == StorageProvider.FILESYSTEM.value and artifacts_path:
            store_kwargs["bucket"] = artifacts_path

        store = ArtifactStore(**store_kwargs)
        set_global_artifact_store(store)

        logger.info("Artifact store initialized (provider: %s)", provider)
        return True

    except Exception as e:
        logger.error("Failed to initialize artifact store: %s", e)
        return False


def main() -> None:
    """CLI entry point."""
    # 1. Initialize artifact store (before data loading)
    _init_artifact_store()

    # 2. Preload reference data from artifacts if configured
    from .core.reference_preload import preload_reference_data

    preload_reference_data()

    # 3. Import async_server (triggers module-level data loaders)
    from .async_server import mcp

    parser = argparse.ArgumentParser(
        prog=ServerConfig.NAME,
        description=ServerConfig.DESCRIPTION,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["stdio", "http"],
        default=None,
        help="Transport mode (stdio for Claude Desktop, http for API)",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for HTTP mode (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8005,
        help="Port for HTTP mode (default: 8005)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if args.mode == "stdio":
        logger.info("Starting %s in stdio mode", ServerConfig.NAME)
        mcp.run(stdio=True)
    elif args.mode == "http":
        logger.info("Starting %s in HTTP mode on %s:%d", ServerConfig.NAME, args.host, args.port)
        mcp.run(host=args.host, port=args.port, stdio=False)
    else:
        if os.environ.get(EnvVar.MCP_STDIO) or (not sys.stdin.isatty()):
            logger.info("Starting %s in stdio mode (auto-detected)", ServerConfig.NAME)
            mcp.run(stdio=True)
        else:
            logger.info(
                "Starting %s in HTTP mode on %s:%d",
                ServerConfig.NAME,
                args.host,
                args.port,
            )
            mcp.run(host=args.host, port=args.port, stdio=False)


if __name__ == "__main__":
    main()
