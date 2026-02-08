"""
Synchronous entry point for chuk-mcp-maritime-archives.

Initialises the artifact store and launches the MCP server in
either stdio or HTTP mode.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from .constants import EnvVar, ServerConfig, StorageProvider

load_dotenv()

logger = logging.getLogger(__name__)


def _init_artifact_store() -> None:
    """Configure chuk-artifacts from environment variables."""
    try:
        from chuk_artifacts import ArtifactStore
        from chuk_mcp_server import set_artifact_store

        provider = os.getenv(EnvVar.ARTIFACTS_PROVIDER, StorageProvider.MEMORY)
        store = ArtifactStore(provider=provider)
        set_artifact_store(store)
        logger.info("Artifact store initialised: provider=%s", provider)
    except ImportError:
        logger.info(
            "chuk-artifacts not available — artifact storage disabled. "
            "Install with: pip install chuk-artifacts"
        )
    except Exception as e:
        logger.warning("Failed to initialise artifact store: %s", e)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog=ServerConfig.NAME,
        description=ServerConfig.DESCRIPTION,
    )
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8005,
        help="HTTP port (only used with --mode http)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    _init_artifact_store()

    from .async_server import mcp

    if args.mode == "http":
        logger.info("Starting %s in HTTP mode on port %d", ServerConfig.NAME, args.port)
        mcp.run(transport="streamable-http", port=args.port)
    else:
        if os.getenv(EnvVar.MCP_STDIO):
            logger.info("MCP_STDIO detected — running in stdio mode")
        logger.info("Starting %s in stdio mode", ServerConfig.NAME)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
