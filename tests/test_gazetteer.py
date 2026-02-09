"""Tests for the VOC gazetteer module."""

import json

import pytest

from chuk_mcp_maritime_archives.core.voc_gazetteer import (
    VOC_GAZETTEER,
    list_location_types,
    list_regions,
    lookup_location,
    search_locations,
)

from .conftest import MockMCPServer


# ---------------------------------------------------------------------------
# Gazetteer data integrity
# ---------------------------------------------------------------------------


class TestGazetteerData:
    def test_has_minimum_entries(self):
        assert len(VOC_GAZETTEER) >= 100

    def test_all_entries_have_required_fields(self):
        for name, entry in VOC_GAZETTEER.items():
            assert "lat" in entry, f"{name} missing lat"
            assert "lon" in entry, f"{name} missing lon"
            assert "region" in entry, f"{name} missing region"
            assert "type" in entry, f"{name} missing type"

    def test_all_regions_are_valid(self):
        from chuk_mcp_maritime_archives.constants import REGIONS

        valid_regions = set(REGIONS.keys())
        for name, entry in VOC_GAZETTEER.items():
            assert entry["region"] in valid_regions, f"{name} has invalid region: {entry['region']}"

    def test_all_types_are_known(self):
        known_types = {
            "port",
            "island",
            "cape",
            "anchorage",
            "waterway",
            "coast",
            "channel",
            "region",
        }
        for name, entry in VOC_GAZETTEER.items():
            assert entry["type"] in known_types, f"{name} has unknown type: {entry['type']}"

    def test_coordinates_are_reasonable(self):
        for name, entry in VOC_GAZETTEER.items():
            assert -90 <= entry["lat"] <= 90, f"{name} lat out of range: {entry['lat']}"
            assert -180 <= entry["lon"] <= 180, f"{name} lon out of range: {entry['lon']}"

    def test_key_voc_locations_present(self):
        expected = [
            "Batavia",
            "Texel",
            "Cape of Good Hope",
            "Malacca",
            "Ambon",
            "Banda Islands",
            "Galle",
            "Cochin",
            "Deshima",
        ]
        for name in expected:
            assert name in VOC_GAZETTEER, f"Missing key location: {name}"


# ---------------------------------------------------------------------------
# lookup_location
# ---------------------------------------------------------------------------


class TestLookupLocation:
    def test_exact_match(self):
        result = lookup_location("Batavia")
        assert result is not None
        assert result["name"] == "Batavia"
        assert result["region"] == "indonesia"
        assert abs(result["lat"] - (-6.13)) < 0.01

    def test_case_insensitive(self):
        result = lookup_location("batavia")
        assert result is not None
        assert result["name"] == "Batavia"

    def test_alias_match(self):
        result = lookup_location("Jakarta")
        assert result is not None
        assert result["name"] == "Batavia"

    def test_alias_case_insensitive(self):
        result = lookup_location("jakarta")
        assert result is not None
        assert result["name"] == "Batavia"

    def test_alias_formosa(self):
        result = lookup_location("Formosa")
        assert result is not None
        assert result["name"] == "Taiwan"

    def test_alias_dejima(self):
        result = lookup_location("Dejima")
        assert result is not None
        assert result["name"] == "Deshima"

    def test_substring_match(self):
        result = lookup_location("Abrolhos")
        assert result is not None
        assert "Abrolhos" in result["name"]

    def test_not_found(self):
        result = lookup_location("Nonexistent Place")
        assert result is None

    def test_empty_query(self):
        assert lookup_location("") is None
        assert lookup_location("  ") is None

    def test_none_query(self):
        assert lookup_location(None) is None

    def test_dutch_alias(self):
        result = lookup_location("Kaap de Goede Hoop")
        assert result is not None
        assert result["name"] == "Cape of Good Hope"

    def test_result_has_all_fields(self):
        result = lookup_location("Texel")
        assert "name" in result
        assert "lat" in result
        assert "lon" in result
        assert "region" in result
        assert "type" in result
        assert "aliases" in result


# ---------------------------------------------------------------------------
# search_locations
# ---------------------------------------------------------------------------


class TestSearchLocations:
    def test_no_filters_returns_all(self):
        results = search_locations(max_results=200)
        assert len(results) >= 100

    def test_filter_by_region(self):
        results = search_locations(region="indonesia")
        assert len(results) >= 10
        assert all(r["region"] == "indonesia" for r in results)

    def test_filter_by_type(self):
        results = search_locations(location_type="port")
        assert len(results) >= 20
        assert all(r["type"] == "port" for r in results)

    def test_filter_by_query(self):
        results = search_locations(query="VOC")
        assert len(results) >= 1
        # Should match entries with "VOC" in notes

    def test_filter_combined(self):
        results = search_locations(region="cape", location_type="anchorage")
        assert len(results) >= 1
        for r in results:
            assert r["region"] == "cape"
            assert r["type"] == "anchorage"

    def test_max_results(self):
        results = search_locations(max_results=5)
        assert len(results) <= 5

    def test_no_match(self):
        results = search_locations(query="xyznonexistent")
        assert len(results) == 0

    def test_query_searches_aliases(self):
        results = search_locations(query="Flushing")
        assert len(results) >= 1
        assert any(r["name"] == "Vlissingen" for r in results)


# ---------------------------------------------------------------------------
# list_regions / list_location_types
# ---------------------------------------------------------------------------


class TestListHelpers:
    def test_list_regions(self):
        regions = list_regions()
        assert "indonesia" in regions
        assert "cape" in regions
        assert regions["indonesia"] >= 10

    def test_list_location_types(self):
        types = list_location_types()
        assert "port" in types
        assert "island" in types
        assert types["port"] >= 20


# ---------------------------------------------------------------------------
# Location MCP tools
# ---------------------------------------------------------------------------


class TestLocationTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.location.api import register_location_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_location_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_lookup_location_success(self):
        fn = self.mcp.get_tool("maritime_lookup_location")
        result = await fn(name="Batavia")
        parsed = json.loads(result)
        assert "location" in parsed
        assert parsed["location"]["name"] == "Batavia"
        assert parsed["location"]["region"] == "indonesia"

    @pytest.mark.asyncio
    async def test_lookup_location_alias(self):
        fn = self.mcp.get_tool("maritime_lookup_location")
        result = await fn(name="Jakarta")
        parsed = json.loads(result)
        assert parsed["location"]["name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_lookup_location_not_found(self):
        fn = self.mcp.get_tool("maritime_lookup_location")
        result = await fn(name="Nonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_lookup_location_text_mode(self):
        fn = self.mcp.get_tool("maritime_lookup_location")
        result = await fn(name="Texel", output_mode="text")
        assert "Texel" in result
        assert "north_sea" in result

    @pytest.mark.asyncio
    async def test_list_locations_no_filters(self):
        fn = self.mcp.get_tool("maritime_list_locations")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["location_count"] >= 50

    @pytest.mark.asyncio
    async def test_list_locations_by_region(self):
        fn = self.mcp.get_tool("maritime_list_locations")
        result = await fn(region="cape")
        parsed = json.loads(result)
        assert parsed["location_count"] >= 1
        for loc in parsed["locations"]:
            assert loc["region"] == "cape"

    @pytest.mark.asyncio
    async def test_list_locations_by_type(self):
        fn = self.mcp.get_tool("maritime_list_locations")
        result = await fn(location_type="island")
        parsed = json.loads(result)
        assert parsed["location_count"] >= 5

    @pytest.mark.asyncio
    async def test_list_locations_no_results(self):
        fn = self.mcp.get_tool("maritime_list_locations")
        result = await fn(query="xyznonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_list_locations_text_mode(self):
        fn = self.mcp.get_tool("maritime_list_locations")
        result = await fn(region="japan", output_mode="text")
        assert "Deshima" in result or "Nagasaki" in result

    @pytest.mark.asyncio
    async def test_list_locations_max_results(self):
        fn = self.mcp.get_tool("maritime_list_locations")
        result = await fn(max_results=3)
        parsed = json.loads(result)
        assert parsed["location_count"] <= 3

    @pytest.mark.asyncio
    async def test_lookup_location_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_lookup_location")
        with patch(
            "chuk_mcp_maritime_archives.tools.location.api.lookup_location",
            side_effect=RuntimeError("boom"),
        ):
            result = await fn(name="Batavia")
        parsed = json.loads(result)
        assert "boom" in parsed["error"]

    @pytest.mark.asyncio
    async def test_list_locations_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_list_locations")
        with patch(
            "chuk_mcp_maritime_archives.tools.location.api.search_locations",
            side_effect=RuntimeError("crash"),
        ):
            result = await fn()
        parsed = json.loads(result)
        assert "crash" in parsed["error"]
