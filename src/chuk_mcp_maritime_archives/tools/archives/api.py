"""MCP tools for browsing maritime archive metadata."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ArchiveDetailResponse,
    ArchiveInfo,
    ArchiveListResponse,
    ErrorResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_archive_tools(mcp: object, manager: object) -> None:
    """Register archive discovery tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_list_archives(
        output_mode: str = "json",
    ) -> str:
        """
        List all available maritime archives.

        Returns metadata for each archive including name, organisation,
        coverage period, record types, and a brief description.

        Args:
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text listing of available archives

        Tips for LLMs:
            - Call this first to discover which archives are available
            - Use maritime_capabilities for a full overview of all tools
              and reference data
            - Archive IDs: das, voc_crew, voc_cargo, maarer
            - DAS covers voyages/vessels, voc_crew covers personnel,
              voc_cargo covers trade goods, maarer covers wreck sites
        """
        try:
            results = manager.list_archives()  # type: ignore[union-attr]

            archives = []
            for r in results:
                archives.append(
                    ArchiveInfo(
                        archive_id=r.get("id", ""),
                        name=r.get("name", ""),
                        organisation=r.get("organisation"),
                        coverage_start=r.get("coverage_start"),
                        coverage_end=r.get("coverage_end"),
                        record_types=r.get("record_types", []),
                        total_records=r.get("total_voyages")
                        or r.get("total_records")
                        or r.get("total_wrecks"),
                        description=r.get("description"),
                    )
                )

            return format_response(
                ArchiveListResponse(
                    archive_count=len(archives),
                    archives=archives,
                    message=SuccessMessages.ARCHIVES_LISTED.format(len(archives)),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to list archives: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to list archives"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_archive(
        archive_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get detailed metadata for a specific maritime archive.

        Returns full information about the archive including organisation,
        coverage period, record types, citation, licence, and access method.

        Args:
            archive_id: Archive identifier (das, voc_crew, voc_cargo, maarer)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with archive details

        Tips for LLMs:
            - Use maritime_list_archives first to see valid archive IDs
            - DAS (Dutch Asiatic Shipping) is the primary source for
              voyages and vessels
            - voc_crew links to personnel muster rolls
            - voc_cargo links to trade goods manifests
            - maarer covers compiled wreck position data
        """
        try:
            result = manager.get_archive(archive_id)  # type: ignore[union-attr]

            if result is None:
                available = manager.get_available_archive_ids()  # type: ignore[union-attr]
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.ARCHIVE_NOT_FOUND.format(
                            archive_id, ", ".join(available)
                        ),
                    ),
                    output_mode,
                )

            archive = ArchiveInfo(
                archive_id=result.get("archive_id", archive_id),
                name=result.get("name", ""),
                organisation=result.get("organisation"),
                coverage_start=result.get("coverage_start"),
                coverage_end=result.get("coverage_end"),
                record_types=result.get("record_types", []),
                total_records=result.get("total_voyages")
                or result.get("total_records")
                or result.get("total_wrecks"),
                description=result.get("description"),
            )

            return format_response(
                ArchiveDetailResponse(
                    archive=archive,
                    message=f"Archive: {archive.name}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get archive '%s': %s", archive_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get archive"),
                output_mode,
            )
