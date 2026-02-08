"""Tests for Pydantic models."""

import json

from chuk_mcp_maritime_archives.models import (
    ArchiveInfo,
    ArchiveListResponse,
    CargoInfo,
    CrewInfo,
    ErrorResponse,
    HullProfile,
    Incident,
    Position,
    PositionUncertainty,
    SourceReference,
    Vessel,
    VesselDimensions,
    VoyageInfo,
    VoyageSearchResponse,
    WreckInfo,
    format_response,
)


# ---------------------------------------------------------------------------
# Domain models (extra="allow")
# ---------------------------------------------------------------------------


class TestDomainModels:
    def test_position_basic(self):
        p = Position(lat=-35.0, lon=25.0)
        assert p.lat == -35.0
        assert p.lon == 25.0
        assert p.uncertainty is None

    def test_position_with_uncertainty(self):
        u = PositionUncertainty(
            type="circle", radius_km=100.0, confidence=0.68, source="dead_reckoning"
        )
        p = Position(lat=-35.0, lon=25.0, uncertainty=u)
        assert p.uncertainty.radius_km == 100.0

    def test_position_extra_fields_allowed(self):
        p = Position(lat=0, lon=0, extra_field="test")
        assert p.extra_field == "test"  # type: ignore[attr-defined]

    def test_vessel_basic(self):
        v = Vessel(name="Batavia", type="retourschip", tonnage=600)
        assert v.name == "Batavia"
        assert v.tonnage == 600

    def test_vessel_with_dimensions(self):
        d = VesselDimensions(length_m=45.0, beam_m=11.5, draught_m=5.5)
        v = Vessel(name="Batavia", dimensions=d)
        assert v.dimensions.length_m == 45.0

    def test_incident(self):
        i = Incident(
            fate="wrecked",
            date="1629-06-04",
            cause="reef",
            position=Position(lat=-28.49, lon=113.79),
            lives_lost=125,
            survivors=216,
        )
        assert i.fate == "wrecked"
        assert i.position.lat == -28.49

    def test_source_reference(self):
        s = SourceReference(reference="DAS voyage 3456")
        assert s.url is None

    def test_hull_profile(self):
        hp = HullProfile(ship_type="retourschip", description="Large VOC ship")
        assert hp.ship_type == "retourschip"
        assert hp.subtypes == {}


# ---------------------------------------------------------------------------
# Response models (extra="forbid")
# ---------------------------------------------------------------------------


class TestResponseModels:
    def test_error_response(self):
        e = ErrorResponse(error="Not found")
        assert e.error == "Not found"
        assert "Not found" in e.to_text()

    def test_archive_info(self):
        a = ArchiveInfo(
            archive_id="das",
            name="Dutch Asiatic Shipping",
            coverage_start="1595",
            coverage_end="1795",
        )
        assert a.archive_id == "das"

    def test_archive_list_response(self):
        a = ArchiveInfo(archive_id="das", name="DAS")
        resp = ArchiveListResponse(archive_count=1, archives=[a], message="1 archive")
        assert resp.archive_count == 1
        text = resp.to_text()
        assert "das" in text

    def test_voyage_info(self):
        v = VoyageInfo(voyage_id="das:3456", ship_name="Batavia", fate="wrecked")
        assert v.voyage_id == "das:3456"

    def test_voyage_search_response(self):
        v = VoyageInfo(voyage_id="das:3456", ship_name="Batavia")
        resp = VoyageSearchResponse(voyage_count=1, voyages=[v], message="Found 1")
        text = resp.to_text()
        assert "Batavia" in text

    def test_wreck_info(self):
        w = WreckInfo(wreck_id="maarer:VOC-0789", ship_name="Batavia", status="found")
        assert w.status == "found"

    def test_crew_info(self):
        c = CrewInfo(
            crew_id="voc_crew:445892",
            name="Jan Pietersz",
            rank="schipper",
            rank_english="captain",
        )
        assert c.rank_english == "captain"

    def test_cargo_info(self):
        c = CargoInfo(
            cargo_id="voc_cargo:23456",
            commodity="pepper",
            value_guilders=187500,
        )
        assert c.value_guilders == 187500


# ---------------------------------------------------------------------------
# format_response helper
# ---------------------------------------------------------------------------


class TestFormatResponse:
    def test_json_mode(self):
        resp = ErrorResponse(error="test")
        result = format_response(resp, "json")
        parsed = json.loads(result)
        assert parsed["error"] == "test"

    def test_text_mode(self):
        resp = ErrorResponse(error="test error")
        result = format_response(resp, "text")
        assert "test error" in result

    def test_default_is_json(self):
        resp = ErrorResponse(error="test")
        result = format_response(resp)
        parsed = json.loads(result)
        assert "error" in parsed
