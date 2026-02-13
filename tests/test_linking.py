"""Tests for cross-archive linking — VoyageFullResponse, linking tool, and client methods."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from chuk_mcp_maritime_archives.core.clients.das_client import DASClient
from chuk_mcp_maritime_archives.core.clients.wreck_client import WreckClient
from chuk_mcp_maritime_archives.core.cliwoc_tracks import (
    find_track_for_voyage,
    get_track_by_das_number,
    search_tracks,
)
from chuk_mcp_maritime_archives.models import LinkAuditResponse, VoyageFullResponse

from .conftest import (
    MockMCPServer,
    SAMPLE_VOYAGES,
    SAMPLE_VESSELS,
    SAMPLE_WRECKS,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# VoyageFullResponse model
# ---------------------------------------------------------------------------


class TestVoyageFullResponse:
    def test_minimal(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            links_found=[],
        )
        assert resp.voyage["ship_name"] == "Batavia"
        assert resp.wreck is None
        assert resp.vessel is None
        assert resp.hull_profile is None
        assert resp.cliwoc_track is None

    def test_all_links(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            wreck=SAMPLE_WRECKS[0],
            vessel=SAMPLE_VESSELS[0],
            hull_profile={"ship_type": "retourschip", "description": "Large ship"},
            cliwoc_track={"voyage_id": 42, "nationality": "NL", "position_count": 100},
            links_found=["wreck", "vessel", "hull_profile", "cliwoc_track"],
        )
        assert resp.wreck["wreck_id"] == "maarer:VOC-0789"
        assert resp.vessel["name"] == "Batavia"
        assert resp.hull_profile["ship_type"] == "retourschip"
        assert resp.cliwoc_track["position_count"] == 100
        assert len(resp.links_found) == 4

    def test_to_text_minimal(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            links_found=[],
            message="Voyage das:3456: Batavia (0 linked records)",
        )
        text = resp.to_text()
        assert "Batavia" in text
        assert "Links found: none" in text

    def test_to_text_with_wreck(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            wreck=SAMPLE_WRECKS[0],
            links_found=["wreck"],
            message="Test",
        )
        text = resp.to_text()
        assert "Wreck Record" in text
        assert "reef" in text

    def test_to_text_with_vessel(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            vessel=SAMPLE_VESSELS[0],
            links_found=["vessel"],
            message="Test",
        )
        text = resp.to_text()
        assert "Vessel" in text
        assert "600" in text

    def test_to_text_with_cliwoc_track(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            cliwoc_track={
                "voyage_id": 42,
                "nationality": "NL",
                "start_date": "1628-10-29",
                "end_date": "1629-06-04",
                "position_count": 200,
            },
            links_found=["cliwoc_track"],
            message="Test",
        )
        text = resp.to_text()
        assert "CLIWOC Track" in text
        assert "200" in text

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            VoyageFullResponse(
                voyage=SAMPLE_VOYAGES[0],
                links_found=[],
                bogus_field="should fail",
            )

    def test_json_round_trip(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            wreck=SAMPLE_WRECKS[0],
            links_found=["wreck"],
            message="Test",
        )
        dumped = resp.model_dump_json()
        parsed = json.loads(dumped)
        assert parsed["voyage"]["ship_name"] == "Batavia"
        assert parsed["wreck"]["wreck_id"] == "maarer:VOC-0789"
        assert parsed["links_found"] == ["wreck"]


# ---------------------------------------------------------------------------
# WreckClient.get_by_voyage_id
# ---------------------------------------------------------------------------


class TestWreckClientLinking:
    def setup_method(self):
        self.client = WreckClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_get_by_voyage_id_found(self):
        result = await self.client.get_by_voyage_id("das:3456")
        assert result is not None
        assert result["ship_name"] == "Batavia"
        assert result["wreck_id"] == "maarer:VOC-0789"

    @pytest.mark.asyncio
    async def test_get_by_voyage_id_not_found(self):
        result = await self.client.get_by_voyage_id("das:99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_voyage_id_no_field(self):
        """Wrecks without voyage_id field should not match."""
        result = await self.client.get_by_voyage_id("das:5678")
        assert result is None


# ---------------------------------------------------------------------------
# DASClient.get_vessel_for_voyage
# ---------------------------------------------------------------------------


class TestDASClientLinking:
    def setup_method(self):
        self.client = DASClient(data_dir=FIXTURES_DIR)

    def test_get_vessel_for_voyage_found(self):
        vessel = self.client.get_vessel_for_voyage("das:3456")
        assert vessel is not None
        assert vessel["name"] == "Batavia"
        assert vessel["vessel_id"] == "das_vessel:001"

    def test_get_vessel_for_voyage_not_found(self):
        vessel = self.client.get_vessel_for_voyage("das:99999")
        assert vessel is None

    def test_get_vessel_for_voyage_second_vessel(self):
        vessel = self.client.get_vessel_for_voyage("das:1234")
        assert vessel is not None
        assert vessel["name"] == "Amsterdam"

    def test_get_vessel_for_voyage_caches_index(self):
        """Second call should use cached index."""
        self.client.get_vessel_for_voyage("das:3456")
        assert self.client._voyage_vessel_index is not None
        # Call again — should hit cache
        vessel = self.client.get_vessel_for_voyage("das:3456")
        assert vessel["name"] == "Batavia"


# ---------------------------------------------------------------------------
# CLIWOC cross-archive linking functions
# ---------------------------------------------------------------------------


class TestCLIWOCLinking:
    def test_get_track_by_das_number_found(self):
        """Test DAS number linking (requires CLIWOC 2.1 Full data)."""
        # Use a known DAS number from the live dataset
        result = get_track_by_das_number("3984.6")
        if result is None:
            pytest.skip("CLIWOC 2.1 Full data not available (no DAS index)")
        assert result.get("das_number") == "3984.6"
        assert "positions" in result

    def test_get_track_by_das_number_not_found(self):
        result = get_track_by_das_number("99999.0")
        assert result is None

    def test_find_track_for_voyage_by_name(self):
        """Test ship name matching (requires CLIWOC 2.1 Full data)."""
        result, confidence = find_track_for_voyage(
            ship_name="BATAVIA",
            departure_date="1628-10-28",
            nationality="NL",
        )
        if result is None:
            pytest.skip("CLIWOC 2.1 Full data not available (no ship name index)")
        assert "voyage_id" in result
        assert "positions" not in result  # Should be summary only
        assert 0.0 < confidence <= 1.0

    def test_find_track_for_voyage_empty_name(self):
        result, confidence = find_track_for_voyage(ship_name="", departure_date="1700-01-01")
        assert result is None
        assert confidence == 0.0

    def test_find_track_for_voyage_no_match(self):
        result, confidence = find_track_for_voyage(
            ship_name="ZZZZNONEXISTENTZZZ",
            departure_date="1700-01-01",
        )
        assert result is None
        assert confidence == 0.0

    def test_find_track_case_insensitive(self):
        """Ship name lookup should be case-insensitive."""
        lower, lower_conf = find_track_for_voyage(ship_name="batavia")
        upper, upper_conf = find_track_for_voyage(ship_name="BATAVIA")
        # Both should return the same result (or both None if data missing)
        if lower is not None and upper is not None:
            assert lower["voyage_id"] == upper["voyage_id"]

    def test_search_tracks_by_ship_name(self):
        """Test the ship_name parameter added to search_tracks."""
        results = search_tracks(ship_name="BATAVIA", max_results=10)
        if not results:
            pytest.skip("CLIWOC 2.1 Full data not available (no ship names)")
        for r in results:
            assert "BATAVIA" in r.get("ship_name", "").upper()

    def test_search_tracks_ship_name_partial(self):
        """Partial ship name match should work."""
        results = search_tracks(ship_name="BATAV", max_results=10)
        if not results:
            pytest.skip("CLIWOC 2.1 Full data not available (no ship names)")
        for r in results:
            assert "BATAV" in r.get("ship_name", "").upper()


# ---------------------------------------------------------------------------
# ArchiveManager.get_voyage_full (using fixture data)
# ---------------------------------------------------------------------------


class TestArchiveManagerLinking:
    @pytest.fixture
    def manager(self):
        from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager

        return ArchiveManager(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_get_voyage_full_with_wreck_and_vessel(self, manager):
        result = await manager.get_voyage_full("das:3456")
        assert result is not None
        assert result["voyage"]["ship_name"] == "Batavia"

        # Should find linked wreck
        assert result["wreck"] is not None
        assert result["wreck"]["ship_name"] == "Batavia"

        # Should find linked vessel
        assert result["vessel"] is not None
        assert result["vessel"]["name"] == "Batavia"

        # Wreck and vessel should be in links_found
        assert "wreck" in result["links_found"]
        assert "vessel" in result["links_found"]

        # link_confidence should be populated
        assert "link_confidence" in result
        assert result["link_confidence"]["wreck"] == 1.0
        assert result["link_confidence"]["vessel"] == 1.0

    @pytest.mark.asyncio
    async def test_get_voyage_full_no_wreck(self, manager):
        """Voyage das:5678 (Ridderschap) arrived safely — no wreck."""
        result = await manager.get_voyage_full("das:5678")
        assert result is not None
        assert result["wreck"] is None
        assert "wreck" not in result["links_found"]
        assert "wreck" not in result["link_confidence"]

    @pytest.mark.asyncio
    async def test_get_voyage_full_not_found(self, manager):
        result = await manager.get_voyage_full("das:99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_voyage_full_links_found_accurate(self, manager):
        result = await manager.get_voyage_full("das:3456")
        assert result is not None
        # links_found should only list non-None records
        for link_name in result["links_found"]:
            assert result.get(link_name) is not None
        # link_confidence keys should match links_found
        for link_name in result["link_confidence"]:
            assert link_name in result["links_found"]


# ---------------------------------------------------------------------------
# maritime_get_voyage_full tool (mocked manager)
# ---------------------------------------------------------------------------


class TestLinkingTool:
    @pytest.fixture(autouse=True)
    def _register(self):
        from chuk_mcp_maritime_archives.tools.linking.api import register_linking_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        self.mgr.get_voyage_full = AsyncMock(
            return_value={
                "voyage": SAMPLE_VOYAGES[0],
                "wreck": SAMPLE_WRECKS[0],
                "vessel": SAMPLE_VESSELS[0],
                "hull_profile": {"ship_type": "retourschip", "description": "Large ship"},
                "cliwoc_track": None,
                "crew": None,
                "links_found": ["wreck", "vessel", "hull_profile"],
                "link_confidence": {"wreck": 1.0, "vessel": 1.0, "hull_profile": 1.0},
            }
        )
        self.mgr.audit_links = AsyncMock(
            return_value={
                "wreck_links": {
                    "ground_truth_count": 54,
                    "matched_count": 54,
                    "precision": 1.0,
                    "recall": 1.0,
                },
                "cliwoc_links": {
                    "direct_links": 48,
                    "fuzzy_matches": 150,
                    "mean_confidence": 0.78,
                    "high_confidence_count": 120,
                    "moderate_confidence_count": 150,
                },
                "crew_links": {"exact_matches": 500, "fuzzy_matches": 0},
                "total_links_evaluated": 600,
                "confidence_distribution": {
                    "0.9-1.0": 48,
                    "0.7-0.9": 120,
                    "0.5-0.7": 30,
                },
            }
        )
        register_linking_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_get_voyage_full_success(self):
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert parsed["voyage"]["ship_name"] == "Batavia"
        assert parsed["wreck"]["wreck_id"] == "maarer:VOC-0789"
        assert parsed["vessel"]["name"] == "Batavia"
        assert "wreck" in parsed["links_found"]
        assert "vessel" in parsed["links_found"]
        assert "hull_profile" in parsed["links_found"]
        # cliwoc_track is None, so excluded from JSON serialization
        assert "cliwoc_track" not in parsed

    @pytest.mark.asyncio
    async def test_get_voyage_full_not_found(self):
        self.mgr.get_voyage_full.return_value = None
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:99999")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_voyage_full_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456", output_mode="text")
        assert "Batavia" in result
        assert "Wreck Record" in result
        assert "Vessel" in result

    @pytest.mark.asyncio
    async def test_get_voyage_full_no_links(self):
        self.mgr.get_voyage_full.return_value = {
            "voyage": SAMPLE_VOYAGES[2],  # Ridderschap — arrived safely
            "wreck": None,
            "vessel": None,
            "hull_profile": None,
            "cliwoc_track": None,
            "crew": None,
            "links_found": [],
            "link_confidence": {},
        }
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:5678")
        parsed = json.loads(result)
        assert parsed["links_found"] == []
        # None values are excluded from JSON serialization
        assert "wreck" not in parsed

    @pytest.mark.asyncio
    async def test_get_voyage_full_error(self):
        self.mgr.get_voyage_full.side_effect = RuntimeError("DB error")
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "DB error" in parsed["error"]

    @pytest.mark.asyncio
    async def test_message_includes_link_count(self):
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "3 linked records" in parsed["message"]

    @pytest.mark.asyncio
    async def test_message_singular_link(self):
        self.mgr.get_voyage_full.return_value = {
            "voyage": SAMPLE_VOYAGES[0],
            "wreck": SAMPLE_WRECKS[0],
            "vessel": None,
            "hull_profile": None,
            "cliwoc_track": None,
            "crew": None,
            "links_found": ["wreck"],
            "link_confidence": {"wreck": 1.0},
        }
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "1 linked record)" in parsed["message"]

    @pytest.mark.asyncio
    async def test_link_confidence_present(self):
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "link_confidence" in parsed
        assert parsed["link_confidence"]["wreck"] == 1.0
        assert parsed["link_confidence"]["vessel"] == 1.0
        assert parsed["link_confidence"]["hull_profile"] == 1.0

    @pytest.mark.asyncio
    async def test_link_confidence_empty_when_no_links(self):
        self.mgr.get_voyage_full.return_value = {
            "voyage": SAMPLE_VOYAGES[2],
            "wreck": None,
            "vessel": None,
            "hull_profile": None,
            "cliwoc_track": None,
            "crew": None,
            "links_found": [],
            "link_confidence": {},
        }
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:5678")
        parsed = json.loads(result)
        assert parsed["link_confidence"] == {}

    @pytest.mark.asyncio
    async def test_include_crew_parameter(self):
        self.mgr.get_voyage_full.return_value = {
            "voyage": SAMPLE_VOYAGES[0],
            "wreck": None,
            "vessel": None,
            "hull_profile": None,
            "cliwoc_track": None,
            "crew": [{"name": "Jan Jansen", "rank": "matroos", "link_confidence": 1.0}],
            "links_found": ["crew"],
            "link_confidence": {"crew": 1.0},
        }
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456", include_crew=True)
        parsed = json.loads(result)
        assert parsed["crew"] is not None
        assert len(parsed["crew"]) == 1
        assert parsed["crew"][0]["name"] == "Jan Jansen"
        assert "crew" in parsed["links_found"]

    @pytest.mark.asyncio
    async def test_link_confidence_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_voyage_full")
        result = await fn(voyage_id="das:3456", output_mode="text")
        assert "Link confidence:" in result
        assert "100%" in result

    @pytest.mark.asyncio
    async def test_audit_links_success(self):
        fn = self.mcp.get_tool("maritime_audit_links")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["wreck_links"]["ground_truth_count"] == 54
        assert parsed["cliwoc_links"]["direct_links"] == 48
        assert parsed["cliwoc_links"]["fuzzy_matches"] == 150
        assert parsed["total_links_evaluated"] == 600

    @pytest.mark.asyncio
    async def test_audit_links_text_mode(self):
        fn = self.mcp.get_tool("maritime_audit_links")
        result = await fn(output_mode="text")
        assert "Wreck Links" in result
        assert "CLIWOC Track Links" in result
        assert "Crew Links" in result
        assert "Confidence Distribution" in result

    @pytest.mark.asyncio
    async def test_audit_links_error(self):
        self.mgr.audit_links.side_effect = RuntimeError("DB error")
        fn = self.mcp.get_tool("maritime_audit_links")
        result = await fn()
        parsed = json.loads(result)
        assert "error" in parsed


# ---------------------------------------------------------------------------
# LinkAuditResponse model
# ---------------------------------------------------------------------------


class TestLinkAuditResponse:
    def test_minimal(self):
        resp = LinkAuditResponse(
            wreck_links={
                "ground_truth_count": 10,
                "matched_count": 8,
                "precision": 1.0,
                "recall": 0.8,
            },
            cliwoc_links={
                "direct_links": 5,
                "fuzzy_matches": 20,
                "mean_confidence": 0.75,
                "high_confidence_count": 15,
                "moderate_confidence_count": 20,
            },
            crew_links={"exact_matches": 100, "fuzzy_matches": 0},
            total_links_evaluated=50,
            message="Test audit",
        )
        assert resp.total_links_evaluated == 50

    def test_to_text(self):
        resp = LinkAuditResponse(
            wreck_links={
                "ground_truth_count": 10,
                "matched_count": 8,
                "precision": 1.0,
                "recall": 0.8,
            },
            cliwoc_links={
                "direct_links": 5,
                "fuzzy_matches": 20,
                "mean_confidence": 0.75,
                "high_confidence_count": 15,
                "moderate_confidence_count": 20,
            },
            crew_links={"exact_matches": 100, "fuzzy_matches": 0},
            total_links_evaluated=50,
            confidence_distribution={"0.9-1.0": 5, "0.7-0.9": 15},
            message="Audit complete",
        )
        text = resp.to_text()
        assert "Wreck Links" in text
        assert "CLIWOC Track Links" in text
        assert "Crew Links" in text
        assert "0.9-1.0: 5" in text

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            LinkAuditResponse(
                wreck_links={},
                cliwoc_links={},
                crew_links={},
                total_links_evaluated=0,
                bogus="fail",
            )


# ---------------------------------------------------------------------------
# VoyageFullResponse with new fields
# ---------------------------------------------------------------------------


class TestVoyageFullResponseV016:
    def test_link_confidence_field(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            wreck=SAMPLE_WRECKS[0],
            links_found=["wreck"],
            link_confidence={"wreck": 1.0},
        )
        assert resp.link_confidence["wreck"] == 1.0

    def test_crew_field(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            crew=[{"name": "Jan", "rank": "matroos"}],
            links_found=["crew"],
        )
        assert len(resp.crew) == 1

    def test_defaults(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            links_found=[],
        )
        assert resp.link_confidence == {}
        assert resp.crew is None

    def test_json_round_trip_with_confidence(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            wreck=SAMPLE_WRECKS[0],
            links_found=["wreck"],
            link_confidence={"wreck": 1.0, "cliwoc_track": 0.85},
        )
        dumped = resp.model_dump_json()
        parsed = json.loads(dumped)
        assert parsed["link_confidence"]["wreck"] == 1.0
        assert parsed["link_confidence"]["cliwoc_track"] == 0.85

    def test_to_text_with_crew(self):
        resp = VoyageFullResponse(
            voyage=SAMPLE_VOYAGES[0],
            crew=[
                {"name": "Jan Jansen", "rank_english": "sailor"},
                {"name": "Pieter de Vries", "rank_english": "boatswain"},
            ],
            links_found=["crew"],
            message="Test",
        )
        text = resp.to_text()
        assert "Crew (2 records)" in text
        assert "Jan Jansen" in text
