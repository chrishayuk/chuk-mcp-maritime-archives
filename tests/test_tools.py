"""Tests for all MCP tool registration modules."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from chuk_mcp_maritime_archives.core.archive_manager import PaginatedResult

from .conftest import (
    MockMCPServer,
    SAMPLE_CAREER,
    SAMPLE_CARGO,
    SAMPLE_CREW,
    SAMPLE_DEMOGRAPHICS,
    SAMPLE_MUSTERS,
    SAMPLE_NARRATIVE_HITS,
    SAMPLE_SURVIVAL,
    SAMPLE_VESSELS,
    SAMPLE_VOYAGES,
    SAMPLE_WAGE_COMPARISON,
    SAMPLE_WRECKS,
)


def _paginated(items: list[dict]) -> PaginatedResult:
    """Wrap a list of dicts in a PaginatedResult with no pagination."""
    return PaginatedResult(items=items, total_count=len(items), next_cursor=None, has_more=False)


@pytest.fixture
def mock_mcp() -> MockMCPServer:
    return MockMCPServer()


@pytest.fixture
def mock_manager() -> MagicMock:
    """Manager with all methods mocked."""
    mgr = MagicMock()
    # Async methods — search methods return PaginatedResult
    mgr.search_voyages = AsyncMock(return_value=_paginated(SAMPLE_VOYAGES))
    mgr.get_voyage = AsyncMock(return_value=SAMPLE_VOYAGES[0])
    mgr.search_wrecks = AsyncMock(return_value=_paginated(SAMPLE_WRECKS))
    mgr.get_wreck = AsyncMock(return_value=SAMPLE_WRECKS[0])
    mgr.search_vessels = AsyncMock(return_value=_paginated(SAMPLE_VESSELS))
    mgr.get_vessel = AsyncMock(return_value=SAMPLE_VESSELS[0])
    mgr.search_crew = AsyncMock(return_value=_paginated(SAMPLE_CREW))
    mgr.get_crew_member = AsyncMock(return_value=SAMPLE_CREW[0])
    mgr.search_cargo = AsyncMock(return_value=_paginated(SAMPLE_CARGO))
    mgr.get_cargo_manifest = AsyncMock(return_value=SAMPLE_CARGO)
    mgr.search_musters = AsyncMock(return_value=_paginated(SAMPLE_MUSTERS))
    mgr.get_muster = AsyncMock(return_value=SAMPLE_MUSTERS[0])
    mgr.compare_wages = AsyncMock(return_value=SAMPLE_WAGE_COMPARISON)
    mgr.search_narratives = AsyncMock(return_value=_paginated(SAMPLE_NARRATIVE_HITS))
    mgr.assess_position = AsyncMock(
        return_value={
            "assessment": {
                "quality_score": 0.5,
                "quality_label": "moderate",
                "uncertainty_type": "approximate",
                "uncertainty_radius_km": 50,
            },
            "recommendations": {"for_drift_modelling": "Use 50km radius."},
        }
    )
    mgr.export_geojson = AsyncMock(
        return_value={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [113.79, -28.49]},
                    "properties": {"wreck_id": "maarer:VOC-0789"},
                }
            ],
        }
    )
    mgr.get_statistics = AsyncMock(
        return_value={
            "summary": {"total_losses": 3, "total_voyages": 100, "loss_rate_percent": 3.0},
            "losses_by_region": {"cape": 1},
            "losses_by_cause": {"reef": 2},
            "date_range": "1595-1795",
        }
    )
    # Sync methods
    mgr.list_archives.return_value = [
        {"id": "das", "name": "Dutch Asiatic Shipping", "organisation": "Huygens"},
    ]
    mgr.get_archive.return_value = {
        "archive_id": "das",
        "name": "Dutch Asiatic Shipping",
        "organisation": "Huygens",
        "coverage_start": "1595",
        "coverage_end": "1795",
        "record_types": ["voyages"],
        "description": "Test description",
    }
    mgr.get_available_archive_ids.return_value = ["das", "voc_crew", "voc_cargo", "maarer"]
    mgr.list_hull_profiles.return_value = ["retourschip", "fluit", "jacht"]
    mgr.get_hull_profile.return_value = {
        "ship_type": "retourschip",
        "description": "Large VOC ship",
        "dimensions_typical": {
            "length_m": {"typical": 45.0},
            "beam_m": {"typical": 11.5},
            "draught_m": {"typical": 5.5},
        },
        "llm_guidance": "Use for drift modelling",
    }
    return mgr


# ---------------------------------------------------------------------------
# Voyage tools
# ---------------------------------------------------------------------------


class TestVoyageTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.voyages.api import register_voyage_tools

        register_voyage_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_voyages_success(self):
        fn = self.mcp.get_tool("maritime_search_voyages")
        result = await fn(ship_name="Batavia")
        parsed = json.loads(result)
        assert parsed["voyage_count"] == 3
        assert len(parsed["voyages"]) == 3

    @pytest.mark.asyncio
    async def test_search_voyages_no_results(self):
        self.mgr.search_voyages.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_voyages")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_voyages_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_voyages")
        result = await fn(output_mode="text")
        assert "Batavia" in result

    @pytest.mark.asyncio
    async def test_search_voyages_error(self):
        self.mgr.search_voyages.side_effect = RuntimeError("API down")
        fn = self.mcp.get_tool("maritime_search_voyages")
        result = await fn()
        parsed = json.loads(result)
        assert "API down" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_voyage_success(self):
        fn = self.mcp.get_tool("maritime_get_voyage")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "voyage" in parsed

    @pytest.mark.asyncio
    async def test_get_voyage_not_found(self):
        self.mgr.get_voyage.return_value = None
        fn = self.mcp.get_tool("maritime_get_voyage")
        result = await fn(voyage_id="das:99999")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_voyage_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_voyage")
        result = await fn(voyage_id="das:3456", output_mode="text")
        assert "Voyage" in result

    @pytest.mark.asyncio
    async def test_get_voyage_error(self):
        self.mgr.get_voyage.side_effect = RuntimeError("timeout")
        fn = self.mcp.get_tool("maritime_get_voyage")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "timeout" in parsed["error"]


# ---------------------------------------------------------------------------
# Wreck tools
# ---------------------------------------------------------------------------


class TestWreckTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.wrecks.api import register_wreck_tools

        register_wreck_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_wrecks_success(self):
        fn = self.mcp.get_tool("maritime_search_wrecks")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["wreck_count"] == 3

    @pytest.mark.asyncio
    async def test_search_wrecks_no_results(self):
        self.mgr.search_wrecks.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_wrecks")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_wrecks_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_wrecks")
        result = await fn(output_mode="text")
        assert "Batavia" in result

    @pytest.mark.asyncio
    async def test_search_wrecks_error(self):
        self.mgr.search_wrecks.side_effect = RuntimeError("oops")
        fn = self.mcp.get_tool("maritime_search_wrecks")
        result = await fn()
        parsed = json.loads(result)
        assert "oops" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_wreck_success(self):
        fn = self.mcp.get_tool("maritime_get_wreck")
        result = await fn(wreck_id="maarer:VOC-0789")
        parsed = json.loads(result)
        assert "wreck" in parsed

    @pytest.mark.asyncio
    async def test_get_wreck_not_found(self):
        self.mgr.get_wreck.return_value = None
        fn = self.mcp.get_tool("maritime_get_wreck")
        result = await fn(wreck_id="maarer:NONE")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_wreck_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_wreck")
        result = await fn(wreck_id="maarer:VOC-0789", output_mode="text")
        assert "Wreck" in result

    @pytest.mark.asyncio
    async def test_get_wreck_error(self):
        self.mgr.get_wreck.side_effect = RuntimeError("fail")
        fn = self.mcp.get_tool("maritime_get_wreck")
        result = await fn(wreck_id="x")
        parsed = json.loads(result)
        assert "fail" in parsed["error"]


# ---------------------------------------------------------------------------
# Vessel tools
# ---------------------------------------------------------------------------


class TestVesselTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.vessels.api import register_vessel_tools

        register_vessel_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_vessels_success(self):
        fn = self.mcp.get_tool("maritime_search_vessels")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["vessel_count"] == 2

    @pytest.mark.asyncio
    async def test_search_vessels_no_results(self):
        self.mgr.search_vessels.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_vessels")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_vessels_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_vessels")
        result = await fn(output_mode="text")
        assert "Batavia" in result

    @pytest.mark.asyncio
    async def test_search_vessels_error(self):
        self.mgr.search_vessels.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_search_vessels")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_vessel_success(self):
        fn = self.mcp.get_tool("maritime_get_vessel")
        result = await fn(vessel_id="das_vessel:001")
        parsed = json.loads(result)
        assert "vessel" in parsed

    @pytest.mark.asyncio
    async def test_get_vessel_not_found(self):
        self.mgr.get_vessel.return_value = None
        fn = self.mcp.get_tool("maritime_get_vessel")
        result = await fn(vessel_id="none")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_vessel_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_vessel")
        result = await fn(vessel_id="das_vessel:001", output_mode="text")
        assert "Vessel" in result

    @pytest.mark.asyncio
    async def test_get_vessel_error(self):
        self.mgr.get_vessel.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_vessel")
        result = await fn(vessel_id="x")
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_hull_profile_success(self):
        fn = self.mcp.get_tool("maritime_get_hull_profile")
        result = await fn(ship_type="retourschip")
        parsed = json.loads(result)
        assert "profile" in parsed

    @pytest.mark.asyncio
    async def test_get_hull_profile_not_found(self):
        self.mgr.get_hull_profile.return_value = None
        fn = self.mcp.get_tool("maritime_get_hull_profile")
        result = await fn(ship_type="unknown")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_hull_profile_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_hull_profile")
        result = await fn(ship_type="retourschip", output_mode="text")
        assert "retourschip" in result

    @pytest.mark.asyncio
    async def test_get_hull_profile_error(self):
        self.mgr.list_hull_profiles.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_hull_profile")
        result = await fn(ship_type="x")
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_list_hull_profiles(self):
        fn = self.mcp.get_tool("maritime_list_hull_profiles")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["count"] == 3
        assert "retourschip" in parsed["ship_types"]

    @pytest.mark.asyncio
    async def test_list_hull_profiles_text_mode(self):
        fn = self.mcp.get_tool("maritime_list_hull_profiles")
        result = await fn(output_mode="text")
        assert "retourschip" in result

    @pytest.mark.asyncio
    async def test_list_hull_profiles_error(self):
        self.mgr.list_hull_profiles.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_list_hull_profiles")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Crew tools
# ---------------------------------------------------------------------------


class TestCrewTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.crew.api import register_crew_tools

        register_crew_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_crew_success(self):
        fn = self.mcp.get_tool("maritime_search_crew")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["crew_count"] == 2

    @pytest.mark.asyncio
    async def test_search_crew_no_results(self):
        self.mgr.search_crew.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_crew")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_crew_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_crew")
        result = await fn(output_mode="text")
        assert "Jan Pietersz" in result

    @pytest.mark.asyncio
    async def test_search_crew_error(self):
        self.mgr.search_crew.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_search_crew")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_crew_member_success(self):
        fn = self.mcp.get_tool("maritime_get_crew_member")
        result = await fn(crew_id="voc_crew:445892")
        parsed = json.loads(result)
        assert "crew_member" in parsed

    @pytest.mark.asyncio
    async def test_get_crew_member_not_found(self):
        self.mgr.get_crew_member.return_value = None
        fn = self.mcp.get_tool("maritime_get_crew_member")
        result = await fn(crew_id="none")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_crew_member_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_crew_member")
        result = await fn(crew_id="voc_crew:445892", output_mode="text")
        assert "Crew" in result

    @pytest.mark.asyncio
    async def test_get_crew_member_error(self):
        self.mgr.get_crew_member.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_crew_member")
        result = await fn(crew_id="x")
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Cargo tools
# ---------------------------------------------------------------------------


class TestCargoTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.cargo.api import register_cargo_tools

        register_cargo_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_cargo_success(self):
        fn = self.mcp.get_tool("maritime_search_cargo")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["cargo_count"] == 2

    @pytest.mark.asyncio
    async def test_search_cargo_no_results(self):
        self.mgr.search_cargo.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_cargo")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_cargo_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_cargo")
        result = await fn(output_mode="text")
        assert "pepper" in result

    @pytest.mark.asyncio
    async def test_search_cargo_error(self):
        self.mgr.search_cargo.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_search_cargo")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_cargo_manifest_success(self):
        fn = self.mcp.get_tool("maritime_get_cargo_manifest")
        result = await fn(voyage_id="das:8123")
        parsed = json.loads(result)
        assert "cargo_entries" in parsed

    @pytest.mark.asyncio
    async def test_get_cargo_manifest_no_results(self):
        self.mgr.get_cargo_manifest.return_value = []
        fn = self.mcp.get_tool("maritime_get_cargo_manifest")
        result = await fn(voyage_id="das:9999")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_cargo_manifest_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_cargo_manifest")
        result = await fn(voyage_id="das:8123", output_mode="text")
        assert "Manifest" in result

    @pytest.mark.asyncio
    async def test_get_cargo_manifest_error(self):
        self.mgr.get_cargo_manifest.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_cargo_manifest")
        result = await fn(voyage_id="x")
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Archive tools
# ---------------------------------------------------------------------------


class TestArchiveTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.archives.api import register_archive_tools

        register_archive_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_list_archives(self):
        fn = self.mcp.get_tool("maritime_list_archives")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["archive_count"] == 1

    @pytest.mark.asyncio
    async def test_list_archives_text_mode(self):
        fn = self.mcp.get_tool("maritime_list_archives")
        result = await fn(output_mode="text")
        assert "das" in result

    @pytest.mark.asyncio
    async def test_list_archives_error(self):
        self.mgr.list_archives.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_list_archives")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_archive_success(self):
        fn = self.mcp.get_tool("maritime_get_archive")
        result = await fn(archive_id="das")
        parsed = json.loads(result)
        assert "archive" in parsed

    @pytest.mark.asyncio
    async def test_get_archive_not_found(self):
        self.mgr.get_archive.return_value = None
        fn = self.mcp.get_tool("maritime_get_archive")
        result = await fn(archive_id="nonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_archive_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_archive")
        result = await fn(archive_id="das", output_mode="text")
        assert "Dutch Asiatic Shipping" in result

    @pytest.mark.asyncio
    async def test_get_archive_error(self):
        self.mgr.get_archive.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_archive")
        result = await fn(archive_id="x")
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Position tools
# ---------------------------------------------------------------------------


class TestPositionTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.position.api import register_position_tools

        register_position_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_assess_position_success(self):
        fn = self.mcp.get_tool("maritime_assess_position")
        result = await fn(date="1700-01-01")
        parsed = json.loads(result)
        assert "assessment" in parsed

    @pytest.mark.asyncio
    async def test_assess_position_with_coords(self):
        fn = self.mcp.get_tool("maritime_assess_position")
        result = await fn(latitude=-28.49, longitude=113.79)
        parsed = json.loads(result)
        assert "assessment" in parsed

    @pytest.mark.asyncio
    async def test_assess_position_text_mode(self):
        fn = self.mcp.get_tool("maritime_assess_position")
        result = await fn(date="1700-01-01", output_mode="text")
        assert "Position Quality" in result

    @pytest.mark.asyncio
    async def test_assess_position_error(self):
        self.mgr.assess_position.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_assess_position")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Export tools
# ---------------------------------------------------------------------------


class TestExportTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.export.api import register_export_tools

        register_export_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_export_geojson_success(self):
        fn = self.mcp.get_tool("maritime_export_geojson")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["feature_count"] == 1

    @pytest.mark.asyncio
    async def test_export_geojson_text_mode(self):
        fn = self.mcp.get_tool("maritime_export_geojson")
        result = await fn(output_mode="text")
        assert "Features" in result

    @pytest.mark.asyncio
    async def test_export_geojson_error(self):
        self.mgr.export_geojson.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_export_geojson")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_statistics_success(self):
        fn = self.mcp.get_tool("maritime_get_statistics")
        result = await fn()
        parsed = json.loads(result)
        assert "statistics" in parsed

    @pytest.mark.asyncio
    async def test_get_statistics_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_statistics")
        result = await fn(output_mode="text")
        assert "Total" in result

    @pytest.mark.asyncio
    async def test_get_statistics_error(self):
        self.mgr.get_statistics.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_statistics")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Discovery tools
# ---------------------------------------------------------------------------


class TestDiscoveryTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.discovery.api import register_discovery_tools

        register_discovery_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_capabilities_success(self):
        fn = self.mcp.get_tool("maritime_capabilities")
        result = await fn()
        parsed = json.loads(result)
        assert "server_name" in parsed
        assert "tools" in parsed
        assert "ship_types" in parsed
        assert "regions" in parsed

    @pytest.mark.asyncio
    async def test_capabilities_text_mode(self):
        fn = self.mcp.get_tool("maritime_capabilities")
        result = await fn(output_mode="text")
        assert "chuk-mcp-maritime-archives" in result
        assert "Archives" in result
        assert "Tools" in result

    @pytest.mark.asyncio
    async def test_capabilities_error(self):
        self.mgr.list_archives.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_capabilities")
        result = await fn()
        parsed = json.loads(result)
        assert "err" in parsed["error"]


# ---------------------------------------------------------------------------
# Pagination tests — verify cursor propagation and response metadata
# ---------------------------------------------------------------------------


class TestPagination:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.voyages.api import register_voyage_tools

        register_voyage_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_cursor_forwarded_to_manager(self):
        fn = self.mcp.get_tool("maritime_search_voyages")
        await fn(cursor="abc123")
        self.mgr.search_voyages.assert_called_once()
        call_kwargs = self.mgr.search_voyages.call_args.kwargs
        assert call_kwargs["cursor"] == "abc123"

    @pytest.mark.asyncio
    async def test_response_includes_pagination_metadata(self):
        self.mgr.search_voyages.return_value = PaginatedResult(
            items=SAMPLE_VOYAGES[:1],
            total_count=3,
            next_cursor="eyJvIjoxfQ",
            has_more=True,
        )
        fn = self.mcp.get_tool("maritime_search_voyages")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["total_count"] == 3
        assert parsed["next_cursor"] == "eyJvIjoxfQ"
        assert parsed["has_more"] is True

    @pytest.mark.asyncio
    async def test_no_pagination_without_cursor(self):
        fn = self.mcp.get_tool("maritime_search_voyages")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["has_more"] is False
        assert "next_cursor" not in parsed  # excluded by exclude_none=True


# ---------------------------------------------------------------------------
# Narrative tools
# ---------------------------------------------------------------------------


class TestNarrativeTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.narratives.api import register_narrative_tools

        register_narrative_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_narratives_success(self):
        fn = self.mcp.get_tool("maritime_search_narratives")
        result = await fn(query="wrecked")
        parsed = json.loads(result)
        assert parsed["result_count"] == 2
        assert len(parsed["results"]) == 2
        assert parsed["results"][0]["record_id"] == "das:3456"
        assert parsed["query"] == "wrecked"

    @pytest.mark.asyncio
    async def test_search_narratives_no_results(self):
        self.mgr.search_narratives.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_narratives")
        result = await fn(query="xyznonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_narratives_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_narratives")
        result = await fn(query="wrecked", output_mode="text")
        assert "Batavia" in result
        assert "Abergavenny" in result

    @pytest.mark.asyncio
    async def test_search_narratives_error(self):
        self.mgr.search_narratives.side_effect = RuntimeError("search failed")
        fn = self.mcp.get_tool("maritime_search_narratives")
        result = await fn(query="test")
        parsed = json.loads(result)
        assert "search failed" in parsed["error"]

    @pytest.mark.asyncio
    async def test_search_narratives_with_filters(self):
        fn = self.mcp.get_tool("maritime_search_narratives")
        result = await fn(query="wrecked", record_type="voyage", archive="das")
        parsed = json.loads(result)
        assert parsed["record_type"] == "voyage"
        assert parsed["archive"] == "das"
        self.mgr.search_narratives.assert_called_once_with(
            query="wrecked",
            record_type="voyage",
            archive="das",
            max_results=50,
            cursor=None,
        )

    @pytest.mark.asyncio
    async def test_search_narratives_pagination(self):
        self.mgr.search_narratives.return_value = PaginatedResult(
            items=SAMPLE_NARRATIVE_HITS[:1],
            total_count=2,
            next_cursor="eyJvIjoxfQ",
            has_more=True,
        )
        fn = self.mcp.get_tool("maritime_search_narratives")
        result = await fn(query="wrecked", max_results=1)
        parsed = json.loads(result)
        assert parsed["total_count"] == 2
        assert parsed["has_more"] is True
        assert parsed["next_cursor"] == "eyJvIjoxfQ"


# ---------------------------------------------------------------------------
# Muster tools
# ---------------------------------------------------------------------------


class TestMusterTools:
    @pytest.fixture(autouse=True)
    def _register(self, mock_mcp, mock_manager):
        from chuk_mcp_maritime_archives.tools.musters.api import register_muster_tools

        register_muster_tools(mock_mcp, mock_manager)
        self.mcp = mock_mcp
        self.mgr = mock_manager

    @pytest.mark.asyncio
    async def test_search_musters_success(self):
        fn = self.mcp.get_tool("maritime_search_musters")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["muster_count"] == 2
        assert len(parsed["musters"]) == 2

    @pytest.mark.asyncio
    async def test_search_musters_no_results(self):
        self.mgr.search_musters.return_value = _paginated([])
        fn = self.mcp.get_tool("maritime_search_musters")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_musters_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_musters")
        result = await fn(output_mode="text")
        assert "Middelburg" in result

    @pytest.mark.asyncio
    async def test_search_musters_error(self):
        self.mgr.search_musters.side_effect = RuntimeError("muster err")
        fn = self.mcp.get_tool("maritime_search_musters")
        result = await fn()
        parsed = json.loads(result)
        assert "muster err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_muster_success(self):
        fn = self.mcp.get_tool("maritime_get_muster")
        result = await fn(muster_id="dss_muster:0001")
        parsed = json.loads(result)
        assert "muster" in parsed

    @pytest.mark.asyncio
    async def test_get_muster_not_found(self):
        self.mgr.get_muster.return_value = None
        fn = self.mcp.get_tool("maritime_get_muster")
        result = await fn(muster_id="dss_muster:9999")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_muster_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_muster")
        result = await fn(muster_id="dss_muster:0001", output_mode="text")
        assert "Middelburg" in result

    @pytest.mark.asyncio
    async def test_get_muster_error(self):
        self.mgr.get_muster.side_effect = RuntimeError("err")
        fn = self.mcp.get_tool("maritime_get_muster")
        result = await fn(muster_id="x")
        parsed = json.loads(result)
        assert "err" in parsed["error"]

    @pytest.mark.asyncio
    async def test_compare_wages_success(self):
        fn = self.mcp.get_tool("maritime_compare_wages")
        result = await fn(
            group1_start=1700,
            group1_end=1730,
            group2_start=1731,
            group2_end=1760,
        )
        parsed = json.loads(result)
        assert parsed["group1_n"] == 5
        assert parsed["group2_n"] == 8
        assert parsed["difference_pct"] == 13.0

    @pytest.mark.asyncio
    async def test_compare_wages_text_mode(self):
        fn = self.mcp.get_tool("maritime_compare_wages")
        result = await fn(
            group1_start=1700,
            group1_end=1730,
            group2_start=1731,
            group2_end=1760,
            output_mode="text",
        )
        assert "1700-1730" in result
        assert "1731-1760" in result

    @pytest.mark.asyncio
    async def test_compare_wages_error(self):
        self.mgr.compare_wages.side_effect = RuntimeError("wage err")
        fn = self.mcp.get_tool("maritime_compare_wages")
        result = await fn(
            group1_start=1700,
            group1_end=1730,
            group2_start=1731,
            group2_end=1760,
        )
        parsed = json.loads(result)
        assert "wage err" in parsed["error"]


# ---------------------------------------------------------------------------
# Demographics tools
# ---------------------------------------------------------------------------


class TestDemographicsTools:
    def setup_method(self):
        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        self.mgr.crew_demographics = MagicMock(return_value=SAMPLE_DEMOGRAPHICS)
        self.mgr.crew_career = MagicMock(return_value=SAMPLE_CAREER)
        self.mgr.crew_survival = MagicMock(return_value=SAMPLE_SURVIVAL)

        from chuk_mcp_maritime_archives.tools.demographics.api import (
            register_demographics_tools,
        )

        register_demographics_tools(self.mcp, self.mgr)

    # --- maritime_crew_demographics ---

    @pytest.mark.asyncio
    async def test_demographics_success(self):
        fn = self.mcp.get_tool("maritime_crew_demographics")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["group_by"] == "rank"
        assert parsed["group_count"] == 3
        assert len(parsed["groups"]) == 3

    @pytest.mark.asyncio
    async def test_demographics_with_filters(self):
        fn = self.mcp.get_tool("maritime_crew_demographics")
        result = await fn(
            group_by="origin",
            date_range="1700/1750",
            rank="matroos",
        )
        parsed = json.loads(result)
        assert parsed["group_by"] == "rank"  # from sample data
        self.mgr.crew_demographics.assert_called_once_with(
            group_by="origin",
            date_range="1700/1750",
            rank="matroos",
            origin=None,
            fate=None,
            ship_name=None,
            top_n=25,
        )

    @pytest.mark.asyncio
    async def test_demographics_text_mode(self):
        fn = self.mcp.get_tool("maritime_crew_demographics")
        result = await fn(output_mode="text")
        assert "Grouped by:" in result
        assert "matroos" in result

    @pytest.mark.asyncio
    async def test_demographics_invalid_group_by(self):
        self.mgr.crew_demographics.side_effect = ValueError("Invalid group_by 'bad'")
        fn = self.mcp.get_tool("maritime_crew_demographics")
        result = await fn(group_by="bad")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_demographics_error(self):
        self.mgr.crew_demographics.side_effect = RuntimeError("demo err")
        fn = self.mcp.get_tool("maritime_crew_demographics")
        result = await fn()
        parsed = json.loads(result)
        assert "demo err" in parsed["error"]

    # --- maritime_crew_career ---

    @pytest.mark.asyncio
    async def test_career_success(self):
        fn = self.mcp.get_tool("maritime_crew_career")
        result = await fn(name="Jan Pietersz")
        parsed = json.loads(result)
        assert parsed["individual_count"] == 1
        assert len(parsed["individuals"]) == 1
        ind = parsed["individuals"][0]
        assert ind["name"] == "Jan Pietersz van der Horst"
        assert len(ind["voyages"]) == 2

    @pytest.mark.asyncio
    async def test_career_with_origin(self):
        fn = self.mcp.get_tool("maritime_crew_career")
        result = await fn(name="Jan Pietersz", origin="Amsterdam")
        json.loads(result)
        self.mgr.crew_career.assert_called_once_with(
            name="Jan Pietersz",
            origin="Amsterdam",
        )

    @pytest.mark.asyncio
    async def test_career_text_mode(self):
        fn = self.mcp.get_tool("maritime_crew_career")
        result = await fn(name="Jan Pietersz", output_mode="text")
        assert "Jan Pietersz van der Horst" in result
        assert "voyages" in result.lower() or "Ranks:" in result

    @pytest.mark.asyncio
    async def test_career_no_matches(self):
        self.mgr.crew_career.return_value = {
            "query_name": "Nobody",
            "query_origin": None,
            "individual_count": 0,
            "total_matches": 0,
            "individuals": [],
        }
        fn = self.mcp.get_tool("maritime_crew_career")
        result = await fn(name="Nobody")
        parsed = json.loads(result)
        assert parsed["individual_count"] == 0

    @pytest.mark.asyncio
    async def test_career_error(self):
        self.mgr.crew_career.side_effect = RuntimeError("career err")
        fn = self.mcp.get_tool("maritime_crew_career")
        result = await fn(name="test")
        parsed = json.loads(result)
        assert "career err" in parsed["error"]

    # --- maritime_crew_survival_analysis ---

    @pytest.mark.asyncio
    async def test_survival_success(self):
        fn = self.mcp.get_tool("maritime_crew_survival_analysis")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["group_by"] == "rank"
        assert parsed["group_count"] > 0
        assert parsed["total_with_known_fate"] == 600000

    @pytest.mark.asyncio
    async def test_survival_with_filters(self):
        fn = self.mcp.get_tool("maritime_crew_survival_analysis")
        result = await fn(
            group_by="decade",
            date_range="1700/1750",
            rank="soldaat",
        )
        json.loads(result)
        self.mgr.crew_survival.assert_called_once_with(
            group_by="decade",
            date_range="1700/1750",
            rank="soldaat",
            origin=None,
            top_n=25,
        )

    @pytest.mark.asyncio
    async def test_survival_text_mode(self):
        fn = self.mcp.get_tool("maritime_crew_survival_analysis")
        result = await fn(output_mode="text")
        assert "Grouped by:" in result
        assert "survived=" in result or "survival=" in result

    @pytest.mark.asyncio
    async def test_survival_rates_present(self):
        fn = self.mcp.get_tool("maritime_crew_survival_analysis")
        result = await fn()
        parsed = json.loads(result)
        for g in parsed["groups"]:
            assert "survival_rate" in g
            assert "mortality_rate" in g
            assert "desertion_rate" in g

    @pytest.mark.asyncio
    async def test_survival_invalid_group_by(self):
        self.mgr.crew_survival.side_effect = ValueError("Invalid group_by 'bad'")
        fn = self.mcp.get_tool("maritime_crew_survival_analysis")
        result = await fn(group_by="bad")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_survival_error(self):
        self.mgr.crew_survival.side_effect = RuntimeError("surv err")
        fn = self.mcp.get_tool("maritime_crew_survival_analysis")
        result = await fn()
        parsed = json.loads(result)
        assert "surv err" in parsed["error"]
