"""Tests for response model to_text() methods and format_response edge cases."""

import pytest

from chuk_mcp_maritime_archives.models.responses import (
    ArchiveDetailResponse,
    ArchiveInfo,
    ArchiveListResponse,
    CapabilitiesResponse,
    CareerRecord,
    CareerVoyage,
    CargoDetailResponse,
    CargoInfo,
    CargoSearchResponse,
    CrewCareerResponse,
    CrewDemographicsResponse,
    CrewDetailResponse,
    CrewInfo,
    CrewSearchResponse,
    CrewSurvivalResponse,
    DemographicsGroup,
    ErrorResponse,
    GeoJSONExportResponse,
    HullProfileListResponse,
    HullProfileResponse,
    PositionAssessmentResponse,
    StatisticsResponse,
    SurvivalGroup,
    ToolInfo,
    VesselDetailResponse,
    VesselInfo,
    VesselSearchResponse,
    VoyageDetailResponse,
    VoyageInfo,
    VoyageSearchResponse,
    WreckDetailResponse,
    WreckInfo,
    WreckSearchResponse,
    decode_cursor,
    encode_cursor,
    format_response,
)


# ---------------------------------------------------------------------------
# Cursor utility tests
# ---------------------------------------------------------------------------


class TestCursorUtilities:
    def test_encode_decode_roundtrip(self):
        for offset in [0, 1, 50, 100, 999]:
            assert decode_cursor(encode_cursor(offset)) == offset

    def test_decode_none_returns_zero(self):
        assert decode_cursor(None) == 0

    def test_decode_empty_returns_zero(self):
        assert decode_cursor("") == 0

    def test_encode_produces_url_safe_string(self):
        cursor = encode_cursor(42)
        assert isinstance(cursor, str)
        assert "=" not in cursor  # padding stripped


class TestArchiveListResponseToText:
    def test_basic(self):
        a = ArchiveInfo(
            archive_id="das",
            name="Dutch Asiatic Shipping",
            coverage_start="1595",
            coverage_end="1795",
            description="A comprehensive database of VOC voyages between the Netherlands and Asia covering the entire period.",
        )
        resp = ArchiveListResponse(archive_count=1, archives=[a], message="1 archive")
        text = resp.to_text()
        assert "das" in text
        assert "1595" in text
        assert "..." in text  # description is truncated

    def test_no_coverage(self):
        a = ArchiveInfo(archive_id="test", name="Test")
        resp = ArchiveListResponse(archive_count=1, archives=[a], message="1 archive")
        text = resp.to_text()
        assert "test" in text
        # No "Period:" line since no coverage_start
        assert "Period" not in text


class TestArchiveDetailResponseToText:
    def test_basic(self):
        a = ArchiveInfo(
            archive_id="das",
            name="Dutch Asiatic Shipping",
            organisation="Huygens",
            coverage_start="1595",
            coverage_end="1795",
            record_types=["voyages", "vessels"],
            description="Full description here",
        )
        resp = ArchiveDetailResponse(archive=a, message="Archive: DAS")
        text = resp.to_text()
        assert "Dutch Asiatic Shipping" in text
        assert "Huygens" in text
        assert "1595" in text
        assert "voyages" in text
        assert "Full description here" in text

    def test_missing_fields(self):
        a = ArchiveInfo(archive_id="x", name="X")
        resp = ArchiveDetailResponse(archive=a, message="test")
        text = resp.to_text()
        assert "Unknown" in text  # organisation defaults to Unknown
        assert "?" in text  # coverage defaults to ?


class TestVoyageSearchResponseToText:
    def test_with_fate_and_ports(self):
        v = VoyageInfo(
            voyage_id="das:3456",
            ship_name="Batavia",
            fate="wrecked",
            departure_port="Texel",
            departure_date="1628-10-28",
            destination_port="Batavia",
        )
        resp = VoyageSearchResponse(voyage_count=1, voyages=[v], message="Found 1")
        text = resp.to_text()
        assert "Batavia" in text
        assert "[wrecked]" in text
        assert "Texel" in text
        assert "1628-10-28" in text

    def test_no_fate_no_ports(self):
        v = VoyageInfo(voyage_id="das:1", ship_name="Test")
        resp = VoyageSearchResponse(voyage_count=1, voyages=[v], message="Found 1")
        text = resp.to_text()
        assert "das:1" in text
        assert "[" not in text  # no fate bracket

    def test_pagination_footer_in_text(self):
        v = VoyageInfo(voyage_id="das:1", ship_name="Test")
        resp = VoyageSearchResponse(
            voyage_count=1,
            voyages=[v],
            message="Found 1",
            total_count=100,
            next_cursor="abc",
            has_more=True,
        )
        text = resp.to_text()
        assert "1 of 100" in text
        assert 'cursor="abc"' in text


class TestVoyageDetailResponseToText:
    def test_with_summary(self):
        resp = VoyageDetailResponse(
            voyage={
                "voyage_id": "das:3456",
                "ship_name": "Batavia",
                "ship_type": "retourschip",
                "captain": "Ariaen Jacobsz",
                "departure_port": "Texel",
                "destination_port": "Batavia",
                "departure_date": "1628-10-28",
                "fate": "wrecked",
                "summary": "Wrecked in WA",
            },
            message="test",
        )
        text = resp.to_text()
        assert "Batavia" in text
        assert "retourschip" in text
        assert "Ariaen Jacobsz" in text
        assert "Wrecked in WA" in text

    def test_minimal(self):
        resp = VoyageDetailResponse(voyage={}, message="test")
        text = resp.to_text()
        assert "?" in text


class TestWreckSearchResponseToText:
    def test_with_status_and_date(self):
        w = WreckInfo(
            wreck_id="maarer:VOC-0789",
            ship_name="Batavia",
            status="found",
            loss_date="1629-06-04",
            loss_cause="reef",
        )
        resp = WreckSearchResponse(wreck_count=1, wrecks=[w], message="Found 1")
        text = resp.to_text()
        assert "Batavia" in text
        assert "[found]" in text
        assert "1629-06-04" in text
        assert "reef" in text

    def test_no_status(self):
        w = WreckInfo(wreck_id="x", ship_name="Test")
        resp = WreckSearchResponse(wreck_count=1, wrecks=[w], message="Found 1")
        text = resp.to_text()
        assert "[" not in text


class TestWreckDetailResponseToText:
    def test_with_position(self):
        resp = WreckDetailResponse(
            wreck={
                "wreck_id": "maarer:VOC-0789",
                "ship_name": "Batavia",
                "loss_date": "1629-06-04",
                "loss_cause": "reef",
                "region": "western_australia",
                "status": "found",
                "position": {"lat": -28.49, "lon": 113.79, "uncertainty_km": 0.1},
            },
            message="test",
        )
        text = resp.to_text()
        assert "Batavia" in text
        assert "-28.49" in text
        assert "113.79" in text

    def test_without_position(self):
        resp = WreckDetailResponse(
            wreck={"wreck_id": "x", "ship_name": "Test"},
            message="test",
        )
        text = resp.to_text()
        assert "Position" not in text


class TestVesselSearchResponseToText:
    def test_basic(self):
        v = VesselInfo(
            vessel_id="das_vessel:001",
            name="Batavia",
            type="retourschip",
            tonnage=600,
        )
        resp = VesselSearchResponse(vessel_count=1, vessels=[v], message="Found 1")
        text = resp.to_text()
        assert "Batavia" in text
        assert "retourschip" in text
        assert "600" in text

    def test_missing_type_and_tonnage(self):
        v = VesselInfo(vessel_id="x", name="Test")
        resp = VesselSearchResponse(vessel_count=1, vessels=[v], message="Found 1")
        text = resp.to_text()
        assert "?" in text


class TestVesselDetailResponseToText:
    def test_basic(self):
        resp = VesselDetailResponse(
            vessel={
                "name": "Batavia",
                "type": "retourschip",
                "tonnage": 600,
                "built_year": 1628,
                "shipyard": "Amsterdam",
                "chamber": "Amsterdam",
            },
            message="test",
        )
        text = resp.to_text()
        assert "Batavia" in text
        assert "600" in text
        assert "1628" in text


class TestCrewSearchResponseToText:
    def test_with_ship(self):
        c = CrewInfo(
            crew_id="voc_crew:445892",
            name="Jan Pietersz",
            rank="schipper",
            rank_english="captain",
            ship_name="Ridderschap",
        )
        resp = CrewSearchResponse(crew_count=1, crew=[c], message="Found 1")
        text = resp.to_text()
        assert "Jan Pietersz" in text
        assert "captain" in text
        assert "Ridderschap" in text

    def test_no_rank_english(self):
        c = CrewInfo(crew_id="x", name="Test", rank="matroos")
        resp = CrewSearchResponse(crew_count=1, crew=[c], message="Found 1")
        text = resp.to_text()
        assert "matroos" in text

    def test_no_ship(self):
        c = CrewInfo(crew_id="x", name="Test")
        resp = CrewSearchResponse(crew_count=1, crew=[c], message="Found 1")
        text = resp.to_text()
        assert "Ship" not in text


class TestCrewDetailResponseToText:
    def test_basic(self):
        resp = CrewDetailResponse(
            crew_member={
                "name": "Jan",
                "rank_english": "captain",
                "origin": "Amsterdam",
                "ship_name": "Batavia",
                "monthly_pay_guilders": 60,
            },
            message="test",
        )
        text = resp.to_text()
        assert "Jan" in text
        assert "captain" in text
        assert "Amsterdam" in text
        assert "60" in text


class TestCargoSearchResponseToText:
    def test_with_value(self):
        c = CargoInfo(
            cargo_id="voc_cargo:23456",
            commodity="pepper",
            quantity=5000,
            unit="pounds",
            value_guilders=187500,
        )
        resp = CargoSearchResponse(cargo_count=1, cargo=[c], message="Found 1")
        text = resp.to_text()
        assert "pepper" in text
        assert "187,500" in text
        assert "5000" in text

    def test_no_value(self):
        c = CargoInfo(cargo_id="x", commodity="spice")
        resp = CargoSearchResponse(cargo_count=1, cargo=[c], message="Found 1")
        text = resp.to_text()
        assert "spice" in text
        assert "guilders" not in text


class TestCargoDetailResponseToText:
    def test_basic(self):
        resp = CargoDetailResponse(
            cargo_entries=[
                {"commodity": "pepper", "quantity": 5000, "unit": "pounds"},
                {"commodity": "nutmeg", "quantity": 1000, "unit": "pounds"},
            ],
            voyage_id="das:8123",
            message="Manifest",
        )
        text = resp.to_text()
        assert "pepper" in text
        assert "nutmeg" in text
        assert "das:8123" in text


class TestLocationSearchResponseToText:
    def test_basic(self):
        from chuk_mcp_maritime_archives.models.responses import (
            LocationInfo,
            LocationSearchResponse,
        )

        loc = LocationInfo(
            name="Batavia",
            lat=-6.13,
            lon=106.85,
            region="indonesia",
            type="port",
            aliases=["Jakarta"],
            notes="VOC Asian headquarters from 1619.",
        )
        resp = LocationSearchResponse(
            location_count=1,
            locations=[loc],
            message="Found 1 location",
        )
        text = resp.to_text()
        assert "Batavia" in text
        assert "Jakarta" in text
        assert "indonesia" in text
        assert "VOC" in text

    def test_no_aliases(self):
        from chuk_mcp_maritime_archives.models.responses import (
            LocationInfo,
            LocationSearchResponse,
        )

        loc = LocationInfo(
            name="Goa",
            lat=15.50,
            lon=73.83,
            region="malabar",
            type="port",
        )
        resp = LocationSearchResponse(
            location_count=1,
            locations=[loc],
            message="Found 1 location",
        )
        text = resp.to_text()
        assert "Goa" in text
        assert "aka" not in text


class TestLocationDetailResponseToText:
    def test_basic(self):
        from chuk_mcp_maritime_archives.models.responses import (
            LocationDetailResponse,
            LocationInfo,
        )

        loc = LocationInfo(
            name="Cape of Good Hope",
            lat=-34.36,
            lon=18.47,
            region="cape",
            type="cape",
            aliases=["Kaap de Goede Hoop"],
            notes="Southern tip of Africa.",
        )
        resp = LocationDetailResponse(location=loc, message="test")
        text = resp.to_text()
        assert "Cape of Good Hope" in text
        assert "Kaap de Goede Hoop" in text
        assert "-34.36" in text
        assert "18.47" in text
        assert "cape" in text
        assert "Southern tip" in text

    def test_no_notes(self):
        from chuk_mcp_maritime_archives.models.responses import (
            LocationDetailResponse,
            LocationInfo,
        )

        loc = LocationInfo(
            name="Test",
            lat=0.0,
            lon=0.0,
            region="test",
            type="port",
        )
        resp = LocationDetailResponse(location=loc, message="test")
        text = resp.to_text()
        assert "Test" in text
        assert "Notes" not in text


class TestHullProfileListResponseToText:
    def test_basic(self):
        resp = HullProfileListResponse(
            ship_types=["retourschip", "fluit"],
            count=2,
            message="2 profiles",
        )
        text = resp.to_text()
        assert "retourschip" in text
        assert "fluit" in text


class TestHullProfileResponseToText:
    def test_with_dimensions_and_guidance(self):
        resp = HullProfileResponse(
            profile={
                "ship_type": "retourschip",
                "description": "Large VOC ship",
                "dimensions_typical": {
                    "length_m": {"typical": 45.0},
                    "beam_m": {"typical": 11.5},
                    "draught_m": {"typical": 5.5},
                },
                "llm_guidance": "Use for drift modelling",
            },
            message="test",
        )
        text = resp.to_text()
        assert "retourschip" in text
        assert "45.0" in text
        assert "drift modelling" in text

    def test_no_dimensions(self):
        resp = HullProfileResponse(
            profile={"ship_type": "test", "description": "Test"},
            message="test",
        )
        text = resp.to_text()
        assert "test" in text
        assert "Length" not in text


class TestPositionAssessmentResponseToText:
    def test_with_recommendations(self):
        resp = PositionAssessmentResponse(
            assessment={
                "assessment": {
                    "quality_label": "moderate",
                    "quality_score": 0.5,
                    "uncertainty_type": "approximate",
                    "uncertainty_radius_km": 50,
                },
                "recommendations": {
                    "for_drift_modelling": "Use 50km radius.",
                },
            },
            message="test",
        )
        text = resp.to_text()
        assert "moderate" in text
        assert "50" in text
        assert "drift modelling" in text

    def test_no_recommendations(self):
        resp = PositionAssessmentResponse(
            assessment={"assessment": {"quality_label": "poor"}},
            message="test",
        )
        text = resp.to_text()
        assert "poor" in text


class TestStatisticsResponseToText:
    def test_basic(self):
        resp = StatisticsResponse(
            statistics={
                "summary": {
                    "total_voyages": 8194,
                    "total_losses": 734,
                    "loss_rate_percent": 8.9,
                },
            },
            message="Stats",
        )
        text = resp.to_text()
        assert "8194" in text
        assert "734" in text
        assert "8.9" in text


class TestGeoJSONExportResponseToText:
    def test_basic(self):
        resp = GeoJSONExportResponse(
            geojson={"type": "FeatureCollection", "features": []},
            feature_count=0,
            message="Exported 0 features",
        )
        text = resp.to_text()
        assert "Features: 0" in text

    def test_with_artifact(self):
        resp = GeoJSONExportResponse(
            geojson={"type": "FeatureCollection", "features": []},
            feature_count=5,
            artifact_ref="artifact:12345",
            message="Exported 5 features",
        )
        text = resp.to_text()
        assert "artifact:12345" in text


class TestCapabilitiesResponseToText:
    def test_basic(self):
        a = ArchiveInfo(archive_id="das", name="DAS")
        t = ToolInfo(name="maritime_search_voyages", category="voyages", description="Search")
        resp = CapabilitiesResponse(
            server_name="test-server",
            version="0.1.0",
            archives=[a],
            tools=[t],
            ship_types=["retourschip"],
            regions={"cape": "Cape of Good Hope"},
            message="test",
        )
        text = resp.to_text()
        assert "test-server" in text
        assert "das" in text
        assert "maritime_search_voyages" in text
        assert "[voyages]" in text


class TestFormatResponseEdgeCases:
    def test_text_mode_without_to_text(self):
        """Model without to_text falls back to JSON."""
        from pydantic import BaseModel

        class PlainModel(BaseModel):
            value: str

        resp = PlainModel(value="test")
        result = format_response(resp, "text")
        # Should fall back to JSON since PlainModel has no to_text
        assert '"value"' in result

    def test_json_mode(self):
        resp = ErrorResponse(error="test")
        result = format_response(resp, "json")
        assert '"error"' in result

    def test_text_mode_calls_to_text(self):
        resp = ErrorResponse(error="test error")
        result = format_response(resp, "text")
        assert "Error: test error" in result


# ---------------------------------------------------------------------------
# Demographics response models
# ---------------------------------------------------------------------------


class TestDemographicsGroup:
    def test_basic(self):
        g = DemographicsGroup(
            group_key="matroos",
            count=1000,
            percentage=32.3,
            fate_distribution={"returned": 500, "died_voyage": 300},
        )
        assert g.group_key == "matroos"
        assert g.count == 1000
        assert g.percentage == 32.3
        assert g.fate_distribution["returned"] == 500

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            DemographicsGroup(
                group_key="x",
                count=1,
                percentage=1.0,
                extra_field="bad",
            )

    def test_serialization(self):
        g = DemographicsGroup(group_key="soldaat", count=50, percentage=10.0)
        data = g.model_dump()
        assert data["group_key"] == "soldaat"
        assert data["fate_distribution"] == {}


class TestCrewDemographicsResponse:
    def test_basic(self):
        resp = CrewDemographicsResponse(
            total_records=100,
            total_filtered=80,
            group_by="rank",
            group_count=2,
            groups=[
                DemographicsGroup(group_key="matroos", count=50, percentage=62.5),
                DemographicsGroup(group_key="schipper", count=30, percentage=37.5),
            ],
            message="test",
        )
        assert resp.total_records == 100
        assert resp.group_count == 2

    def test_to_text(self):
        resp = CrewDemographicsResponse(
            total_records=100,
            total_filtered=80,
            group_by="rank",
            group_count=1,
            groups=[DemographicsGroup(group_key="matroos", count=80, percentage=100.0)],
            other_count=0,
            message="Demographics",
        )
        text = resp.to_text()
        assert "Grouped by: rank" in text
        assert "matroos" in text
        assert "100.0%" in text

    def test_to_text_with_other(self):
        resp = CrewDemographicsResponse(
            total_records=100,
            total_filtered=100,
            group_by="origin",
            group_count=1,
            groups=[DemographicsGroup(group_key="Amsterdam", count=60, percentage=60.0)],
            other_count=40,
            message="test",
        )
        text = resp.to_text()
        assert "(other)" in text

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            CrewDemographicsResponse(
                total_records=1,
                total_filtered=1,
                group_by="rank",
                group_count=0,
                groups=[],
                bad_field=True,
            )


class TestCareerVoyage:
    def test_basic(self):
        v = CareerVoyage(
            crew_id="voc_crew:1",
            ship_name="Batavia",
            voyage_id="das:3456",
            rank="matroos",
            embarkation_date="1628-10-28",
            service_end_reason="returned",
        )
        assert v.crew_id == "voc_crew:1"
        assert v.rank == "matroos"

    def test_optional_fields(self):
        v = CareerVoyage(crew_id="voc_crew:1")
        assert v.ship_name is None
        assert v.rank is None


class TestCareerRecord:
    def test_basic(self):
        rec = CareerRecord(
            name="Jan Pietersz",
            voyage_count=3,
            distinct_ships=["A", "B"],
            ranks_held=["matroos", "schipper"],
            final_fate="returned",
        )
        assert rec.voyage_count == 3
        assert len(rec.distinct_ships) == 2

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            CareerRecord(name="x", voyage_count=1, bad="field")


class TestCrewCareerResponse:
    def test_basic(self):
        resp = CrewCareerResponse(
            query_name="Jan",
            individual_count=1,
            total_matches=3,
            individuals=[
                CareerRecord(
                    name="Jan Pietersz",
                    voyage_count=3,
                    ranks_held=["matroos", "schipper"],
                    distinct_ships=["Batavia"],
                    final_fate="returned",
                ),
            ],
            message="test",
        )
        assert resp.individual_count == 1

    def test_to_text(self):
        resp = CrewCareerResponse(
            query_name="Jan",
            individual_count=1,
            total_matches=2,
            individuals=[
                CareerRecord(
                    name="Jan Pietersz",
                    origin="Amsterdam",
                    voyage_count=2,
                    first_date="1694-01-03",
                    last_date="1699-03-15",
                    ranks_held=["schipper", "stuurman"],
                    distinct_ships=["Ship A", "Ship B"],
                    final_fate="returned",
                ),
            ],
            message="Found 1 individual",
        )
        text = resp.to_text()
        assert "Jan Pietersz" in text
        assert "Ranks:" in text
        assert "Ships:" in text

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            CrewCareerResponse(
                query_name="x",
                individual_count=0,
                total_matches=0,
                individuals=[],
                bad="field",
            )


class TestSurvivalGroup:
    def test_basic(self):
        g = SurvivalGroup(
            group_key="matroos",
            total=100,
            survived=40,
            died_voyage=30,
            died_asia=10,
            deserted=15,
            discharged=5,
            survival_rate=40.0,
            mortality_rate=40.0,
            desertion_rate=15.0,
        )
        assert g.total == 100
        assert g.survival_rate == 40.0

    def test_defaults(self):
        g = SurvivalGroup(group_key="test", total=0)
        assert g.survived == 0
        assert g.survival_rate == 0.0

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            SurvivalGroup(group_key="x", total=1, bad="field")


class TestCrewSurvivalResponse:
    def test_basic(self):
        resp = CrewSurvivalResponse(
            total_records=1000,
            total_with_known_fate=800,
            group_by="rank",
            group_count=2,
            groups=[
                SurvivalGroup(
                    group_key="matroos",
                    total=500,
                    survival_rate=40.0,
                    mortality_rate=45.0,
                    desertion_rate=10.0,
                ),
                SurvivalGroup(
                    group_key="schipper",
                    total=300,
                    survival_rate=75.0,
                    mortality_rate=17.5,
                    desertion_rate=2.5,
                ),
            ],
            message="test",
        )
        assert resp.total_with_known_fate == 800

    def test_to_text(self):
        resp = CrewSurvivalResponse(
            total_records=100,
            total_with_known_fate=80,
            group_by="rank",
            group_count=1,
            groups=[
                SurvivalGroup(
                    group_key="matroos",
                    total=80,
                    survived=32,
                    died_voyage=24,
                    died_asia=8,
                    deserted=12,
                    discharged=4,
                    survival_rate=40.0,
                    mortality_rate=40.0,
                    desertion_rate=15.0,
                ),
            ],
            message="Survival analysis",
        )
        text = resp.to_text()
        assert "Grouped by: rank" in text
        assert "matroos" in text
        assert "survived=" in text
        assert "mortality=" in text

    def test_extra_forbid(self):
        with pytest.raises(Exception):
            CrewSurvivalResponse(
                total_records=1,
                total_with_known_fate=1,
                group_by="rank",
                group_count=0,
                groups=[],
                bad="field",
            )
