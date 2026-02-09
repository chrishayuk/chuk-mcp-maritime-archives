"""Tests for all MCP tool registration modules."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from .conftest import (
    MockMCPServer,
    SAMPLE_CARGO,
    SAMPLE_CREW,
    SAMPLE_VESSELS,
    SAMPLE_VOYAGES,
    SAMPLE_WRECKS,
)


@pytest.fixture
def mock_mcp() -> MockMCPServer:
    return MockMCPServer()


@pytest.fixture
def mock_manager() -> MagicMock:
    """Manager with all methods mocked."""
    mgr = MagicMock()
    # Async methods
    mgr.search_voyages = AsyncMock(return_value=SAMPLE_VOYAGES)
    mgr.get_voyage = AsyncMock(return_value=SAMPLE_VOYAGES[0])
    mgr.search_wrecks = AsyncMock(return_value=SAMPLE_WRECKS)
    mgr.get_wreck = AsyncMock(return_value=SAMPLE_WRECKS[0])
    mgr.search_vessels = AsyncMock(return_value=SAMPLE_VESSELS)
    mgr.get_vessel = AsyncMock(return_value=SAMPLE_VESSELS[0])
    mgr.search_crew = AsyncMock(return_value=SAMPLE_CREW)
    mgr.get_crew_member = AsyncMock(return_value=SAMPLE_CREW[0])
    mgr.search_cargo = AsyncMock(return_value=SAMPLE_CARGO)
    mgr.get_cargo_manifest = AsyncMock(return_value=SAMPLE_CARGO)
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
        self.mgr.search_voyages.return_value = []
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
        self.mgr.search_wrecks.return_value = []
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
        self.mgr.search_vessels.return_value = []
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
        self.mgr.search_crew.return_value = []
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
        self.mgr.search_cargo.return_value = []
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
