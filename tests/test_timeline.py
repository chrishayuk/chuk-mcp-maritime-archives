"""Tests for the voyage timeline feature — models and MCP tool."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from chuk_mcp_maritime_archives.models.responses import TimelineEvent, TimelineResponse

from .conftest import MockMCPServer


# ---------------------------------------------------------------------------
# Sample timeline data
# ---------------------------------------------------------------------------

SAMPLE_TIMELINE = {
    "voyage_id": "das:3456",
    "ship_name": "Batavia",
    "events": [
        {
            "date": "1628-10-28",
            "type": "departure",
            "title": "Departed Texel",
            "details": {"port": "Texel", "captain": "Ariaen Jacobsz"},
            "position": None,
            "source": "das",
        },
        {
            "date": "1629-01-15",
            "type": "waypoint_estimate",
            "title": "Estimated at Cape of Good Hope",
            "details": {"waypoint": "Cape of Good Hope", "region": "cape"},
            "position": {"lat": -33.93, "lon": 18.42},
            "source": "route_estimate",
        },
        {
            "date": "1629-06-04",
            "type": "loss",
            "title": "Lost: reef",
            "details": {"wreck_id": "maarer:VOC-0789", "loss_cause": "reef"},
            "position": {"lat": -28.49, "lon": 113.79},
            "source": "maarer",
        },
    ],
    "data_sources": ["das", "route_estimate", "maarer"],
    "geojson": {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[18.42, -33.93], [113.79, -28.49]],
        },
        "properties": {"voyage_id": "das:3456", "ship_name": "Batavia", "point_count": 2},
    },
}


# ---------------------------------------------------------------------------
# TimelineEvent and TimelineResponse model tests
# ---------------------------------------------------------------------------


class TestTimelineModels:
    def test_timeline_event_all_fields(self):
        event = TimelineEvent(
            date="1628-10-28",
            type="departure",
            title="Departed Texel",
            details={"port": "Texel", "captain": "Ariaen Jacobsz"},
            position=None,
            source="das",
        )
        assert event.date == "1628-10-28"
        assert event.type == "departure"
        assert event.title == "Departed Texel"
        assert event.details["port"] == "Texel"
        assert event.position is None
        assert event.source == "das"

    def test_timeline_event_with_position(self):
        event = TimelineEvent(
            date="1629-01-15",
            type="waypoint_estimate",
            title="Estimated at Cape of Good Hope",
            details={"waypoint": "Cape of Good Hope"},
            position={"lat": -33.93, "lon": 18.42},
            source="route_estimate",
        )
        assert event.position is not None
        assert event.position["lat"] == -33.93
        assert event.position["lon"] == 18.42

    def test_timeline_event_default_details(self):
        event = TimelineEvent(
            date="1628-10-28",
            type="departure",
            title="Departed Texel",
            source="das",
        )
        assert event.details == {}

    def test_timeline_event_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            TimelineEvent(
                date="1628-10-28",
                type="departure",
                title="Departed Texel",
                source="das",
                bogus_field="should fail",
            )

    def test_timeline_response_to_text_shows_events(self):
        events = [
            TimelineEvent(
                date="1628-10-28",
                type="departure",
                title="Departed Texel",
                source="das",
            ),
            TimelineEvent(
                date="1629-06-04",
                type="loss",
                title="Lost: reef",
                position={"lat": -28.49, "lon": 113.79},
                source="maarer",
            ),
        ]
        resp = TimelineResponse(
            voyage_id="das:3456",
            ship_name="Batavia",
            event_count=2,
            events=events,
            data_sources=["das", "maarer"],
            message="Timeline for voyage das:3456: 2 events from das, maarer",
        )
        text = resp.to_text()
        assert "das:3456" in text
        assert "Batavia" in text
        assert "Departed Texel" in text
        assert "Lost: reef" in text
        assert "Events: 2" in text

    def test_timeline_response_to_text_shows_sources(self):
        events = [
            TimelineEvent(
                date="1628-10-28",
                type="departure",
                title="Departed Texel",
                source="das",
            ),
        ]
        resp = TimelineResponse(
            voyage_id="das:3456",
            ship_name="Batavia",
            event_count=1,
            events=events,
            data_sources=["das", "route_estimate", "maarer"],
            message="Test",
        )
        text = resp.to_text()
        assert "Sources: das, route_estimate, maarer" in text

    def test_timeline_response_to_text_shows_position(self):
        events = [
            TimelineEvent(
                date="1629-06-04",
                type="loss",
                title="Lost: reef",
                position={"lat": -28.49, "lon": 113.79},
                source="maarer",
            ),
        ]
        resp = TimelineResponse(
            voyage_id="das:3456",
            event_count=1,
            events=events,
            message="Test",
        )
        text = resp.to_text()
        assert "-28.49" in text
        assert "113.79" in text

    def test_timeline_response_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            TimelineResponse(
                voyage_id="das:3456",
                event_count=0,
                events=[],
                bogus_field="should fail",
            )

    def test_timeline_response_with_geojson(self):
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[18.42, -33.93], [113.79, -28.49]],
            },
            "properties": {"voyage_id": "das:3456"},
        }
        resp = TimelineResponse(
            voyage_id="das:3456",
            event_count=0,
            events=[],
            geojson=geojson,
            message="Test",
        )
        assert resp.geojson is not None
        assert resp.geojson["type"] == "Feature"
        assert resp.geojson["geometry"]["type"] == "LineString"

    def test_timeline_response_no_events(self):
        resp = TimelineResponse(
            voyage_id="das:3456",
            ship_name="Batavia",
            event_count=0,
            events=[],
            message="No events",
        )
        assert resp.event_count == 0
        assert resp.events == []
        text = resp.to_text()
        assert "Events: 0" in text
        assert "Batavia" in text

    def test_timeline_response_json_round_trip(self):
        events = [
            TimelineEvent(
                date="1628-10-28",
                type="departure",
                title="Departed Texel",
                details={"port": "Texel"},
                source="das",
            ),
        ]
        resp = TimelineResponse(
            voyage_id="das:3456",
            ship_name="Batavia",
            event_count=1,
            events=events,
            data_sources=["das"],
            message="Test",
        )
        dumped = resp.model_dump_json()
        parsed = json.loads(dumped)
        assert parsed["voyage_id"] == "das:3456"
        assert parsed["ship_name"] == "Batavia"
        assert len(parsed["events"]) == 1
        assert parsed["events"][0]["title"] == "Departed Texel"
        assert parsed["data_sources"] == ["das"]

    def test_timeline_response_no_ship_name(self):
        resp = TimelineResponse(
            voyage_id="das:3456",
            event_count=0,
            events=[],
            message="Test",
        )
        assert resp.ship_name is None
        text = resp.to_text()
        # ship_name line should not appear when None
        assert "Ship:" not in text


# ---------------------------------------------------------------------------
# Timeline MCP tool tests
# ---------------------------------------------------------------------------


class TestTimelineTool:
    @pytest.fixture(autouse=True)
    def _register(self):
        from chuk_mcp_maritime_archives.tools.timeline.api import register_timeline_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_timeline_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_tool_registered(self):
        assert "maritime_get_timeline" in self.mcp.tool_names

    @pytest.mark.asyncio
    async def test_success_returns_events(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert parsed["voyage_id"] == "das:3456"
        assert parsed["ship_name"] == "Batavia"
        assert parsed["event_count"] == 3
        assert len(parsed["events"]) == 3
        assert parsed["events"][0]["type"] == "departure"
        assert parsed["events"][1]["type"] == "waypoint_estimate"
        assert parsed["events"][2]["type"] == "loss"

    @pytest.mark.asyncio
    async def test_success_includes_data_sources(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "das" in parsed["data_sources"]
        assert "route_estimate" in parsed["data_sources"]
        assert "maarer" in parsed["data_sources"]

    @pytest.mark.asyncio
    async def test_success_includes_geojson(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert parsed["geojson"] is not None
        assert parsed["geojson"]["type"] == "Feature"
        assert parsed["geojson"]["geometry"]["type"] == "LineString"

    @pytest.mark.asyncio
    async def test_success_message_format(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "3 events" in parsed["message"]
        assert "das:3456" in parsed["message"]

    @pytest.mark.asyncio
    async def test_not_found_returns_error(self):
        self.mgr.build_timeline = AsyncMock(return_value=None)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:99999")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "das:99999" in parsed["error"]

    @pytest.mark.asyncio
    async def test_no_events_returns_error(self):
        self.mgr.build_timeline = AsyncMock(
            return_value={
                "voyage_id": "das:3456",
                "ship_name": "Batavia",
                "events": [],
                "data_sources": ["das"],
                "geojson": None,
            }
        )
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "das:3456" in parsed["error"]

    @pytest.mark.asyncio
    async def test_with_include_positions(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        await fn(voyage_id="das:3456", include_positions=True)
        self.mgr.build_timeline.assert_called_once_with(
            voyage_id="das:3456",
            include_positions=True,
            max_positions=20,
        )

    @pytest.mark.asyncio
    async def test_with_custom_max_positions(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        await fn(voyage_id="das:3456", include_positions=True, max_positions=50)
        self.mgr.build_timeline.assert_called_once_with(
            voyage_id="das:3456",
            include_positions=True,
            max_positions=50,
        )

    @pytest.mark.asyncio
    async def test_text_mode_output(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456", output_mode="text")
        # Text mode should not be JSON
        assert not result.startswith("{")
        assert "Batavia" in result
        assert "Departed Texel" in result
        assert "Lost: reef" in result
        assert "Sources:" in result

    @pytest.mark.asyncio
    async def test_text_mode_not_found(self):
        self.mgr.build_timeline = AsyncMock(return_value=None)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:99999", output_mode="text")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_error_handling(self):
        self.mgr.build_timeline = AsyncMock(side_effect=RuntimeError("Database connection lost"))
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Database connection lost" in parsed["error"]

    @pytest.mark.asyncio
    async def test_error_handling_text_mode(self):
        self.mgr.build_timeline = AsyncMock(side_effect=RuntimeError("timeout"))
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456", output_mode="text")
        assert "Error" in result
        assert "timeout" in result

    @pytest.mark.asyncio
    async def test_default_parameters(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        await fn(voyage_id="das:3456")
        self.mgr.build_timeline.assert_called_once_with(
            voyage_id="das:3456",
            include_positions=False,
            max_positions=20,
        )

    @pytest.mark.asyncio
    async def test_events_preserve_position_data(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        # First event has no position
        assert parsed["events"][0].get("position") is None
        # Second event has Cape position
        assert parsed["events"][1]["position"]["lat"] == -33.93
        assert parsed["events"][1]["position"]["lon"] == 18.42
        # Third event has wreck position
        assert parsed["events"][2]["position"]["lat"] == -28.49
        assert parsed["events"][2]["position"]["lon"] == 113.79

    @pytest.mark.asyncio
    async def test_events_preserve_details(self):
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE)
        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert parsed["events"][0]["details"]["port"] == "Texel"
        assert parsed["events"][0]["details"]["captain"] == "Ariaen Jacobsz"
        assert parsed["events"][2]["details"]["wreck_id"] == "maarer:VOC-0789"
        assert parsed["events"][2]["details"]["loss_cause"] == "reef"
