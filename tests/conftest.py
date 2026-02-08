"""Shared fixtures for chuk-mcp-maritime-archives tests."""

import pytest

from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager


# ---------------------------------------------------------------------------
# Mock MCP server — collects registered tools without a real MCP runtime
# ---------------------------------------------------------------------------


class MockMCPServer:
    """Minimal MCP server mock that captures tools registered via @mcp.tool."""

    def __init__(self) -> None:
        self._tools: dict[str, object] = {}

    def tool(self, fn: object) -> object:
        """Decorator that registers the function and returns it unchanged."""
        self._tools[fn.__name__] = fn  # type: ignore[union-attr]
        return fn

    def get_tool(self, name: str) -> object:
        return self._tools[name]

    def get_tools(self) -> list[object]:
        return list(self._tools.values())

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


@pytest.fixture
def mock_mcp() -> MockMCPServer:
    return MockMCPServer()


# ---------------------------------------------------------------------------
# ArchiveManager fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager() -> ArchiveManager:
    """Fresh ArchiveManager with no cached records."""
    return ArchiveManager()
