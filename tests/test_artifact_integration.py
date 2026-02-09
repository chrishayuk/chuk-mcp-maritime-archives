"""Tests for artifact store integration — export, timeline, reference preload, and data loading edge cases."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from chuk_mcp_maritime_archives.models.responses import TimelineResponse

from .conftest import MockMCPServer


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_GEOJSON_RESULT = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [113.79, -28.49]},
            "properties": {"wreck_id": "maarer:VOC-0789"},
        }
    ],
}

SAMPLE_TIMELINE_RESULT = {
    "voyage_id": "das:3456",
    "ship_name": "Batavia",
    "events": [
        {
            "date": "1628-10-28",
            "type": "departure",
            "title": "Departed Texel",
            "details": {"port": "Texel"},
            "position": None,
            "source": "das",
        },
    ],
    "data_sources": ["das"],
    "geojson": {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[18.42, -33.93], [113.79, -28.49]],
        },
        "properties": {"voyage_id": "das:3456"},
    },
}


# ---------------------------------------------------------------------------
# Export artifact tests
# ---------------------------------------------------------------------------


class TestExportArtifact:
    @pytest.fixture(autouse=True)
    def _register(self):
        from chuk_mcp_maritime_archives.tools.export.api import register_export_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        self.mgr.export_geojson = AsyncMock(return_value=SAMPLE_GEOJSON_RESULT)
        register_export_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_artifact_ref_populated_when_store_available(self):
        """When artifact store is available, artifact_ref should be set."""
        mock_store = AsyncMock()
        mock_store.store = AsyncMock(return_value="art-12345")

        with patch.dict(
            "sys.modules",
            {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
        ):
            fn = self.mcp.get_tool("maritime_export_geojson")
            result = await fn()
            parsed = json.loads(result)
            assert parsed["artifact_ref"] == "art-12345"
            assert parsed["feature_count"] == 1

    @pytest.mark.asyncio
    async def test_artifact_ref_none_when_store_unavailable(self):
        """When artifact store import fails, artifact_ref should be None."""
        with patch.dict(
            "sys.modules",
            {"chuk_mcp_server": MagicMock(get_artifact_store=MagicMock(side_effect=ImportError))},
        ):
            fn = self.mcp.get_tool("maritime_export_geojson")
            result = await fn()
            parsed = json.loads(result)
            assert parsed.get("artifact_ref") is None
            assert parsed["feature_count"] == 1

    @pytest.mark.asyncio
    async def test_artifact_ref_none_when_store_raises(self):
        """When store.store() raises, artifact_ref should be None."""
        mock_store = AsyncMock()
        mock_store.store = AsyncMock(side_effect=RuntimeError("S3 unavailable"))

        with patch.dict(
            "sys.modules",
            {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
        ):
            fn = self.mcp.get_tool("maritime_export_geojson")
            result = await fn()
            parsed = json.loads(result)
            assert parsed.get("artifact_ref") is None
            assert parsed["feature_count"] == 1

    @pytest.mark.asyncio
    async def test_text_mode_shows_artifact_ref(self):
        """Text mode output should include the artifact reference."""
        mock_store = AsyncMock()
        mock_store.store = AsyncMock(return_value="art-text-001")

        with patch.dict(
            "sys.modules",
            {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
        ):
            fn = self.mcp.get_tool("maritime_export_geojson")
            result = await fn(output_mode="text")
            assert "Artifact: art-text-001" in result


# ---------------------------------------------------------------------------
# Timeline artifact tests
# ---------------------------------------------------------------------------


class TestTimelineArtifact:
    @pytest.fixture(autouse=True)
    def _register(self):
        from chuk_mcp_maritime_archives.tools.timeline.api import register_timeline_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_timeline_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_artifact_ref_populated_when_geojson_present(self):
        """When timeline has geojson and store is available, artifact_ref should be set."""
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE_RESULT)
        mock_store = AsyncMock()
        mock_store.store = AsyncMock(return_value="timeline-art-001")

        with patch.dict(
            "sys.modules",
            {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
        ):
            fn = self.mcp.get_tool("maritime_get_timeline")
            result = await fn(voyage_id="das:3456")
            parsed = json.loads(result)
            assert parsed["artifact_ref"] == "timeline-art-001"

    @pytest.mark.asyncio
    async def test_artifact_ref_none_when_no_geojson(self):
        """When timeline has no geojson, artifact_ref should be None."""
        no_geojson = {
            **SAMPLE_TIMELINE_RESULT,
            "geojson": None,
        }
        self.mgr.build_timeline = AsyncMock(return_value=no_geojson)

        fn = self.mcp.get_tool("maritime_get_timeline")
        result = await fn(voyage_id="das:3456")
        parsed = json.loads(result)
        assert parsed.get("artifact_ref") is None

    @pytest.mark.asyncio
    async def test_artifact_ref_none_when_store_unavailable(self):
        """When store is unavailable, artifact_ref should be None."""
        self.mgr.build_timeline = AsyncMock(return_value=SAMPLE_TIMELINE_RESULT)

        with patch.dict(
            "sys.modules",
            {"chuk_mcp_server": MagicMock(get_artifact_store=MagicMock(side_effect=ImportError))},
        ):
            fn = self.mcp.get_tool("maritime_get_timeline")
            result = await fn(voyage_id="das:3456")
            parsed = json.loads(result)
            assert parsed.get("artifact_ref") is None
            assert parsed["event_count"] == 1


# ---------------------------------------------------------------------------
# TimelineResponse artifact_ref model tests
# ---------------------------------------------------------------------------


class TestTimelineResponseArtifactRef:
    def test_artifact_ref_in_model_dump(self):
        """artifact_ref should appear in JSON output."""
        resp = TimelineResponse(
            voyage_id="das:3456",
            event_count=0,
            events=[],
            artifact_ref="art-abc-123",
            message="Test",
        )
        dumped = json.loads(resp.model_dump_json())
        assert dumped["artifact_ref"] == "art-abc-123"

    def test_artifact_ref_in_to_text(self):
        """to_text() should show artifact reference."""
        resp = TimelineResponse(
            voyage_id="das:3456",
            event_count=0,
            events=[],
            artifact_ref="art-abc-123",
            message="Test",
        )
        text = resp.to_text()
        assert "Artifact: art-abc-123" in text

    def test_artifact_ref_not_in_text_when_none(self):
        """to_text() should not show artifact line when None."""
        resp = TimelineResponse(
            voyage_id="das:3456",
            event_count=0,
            events=[],
            message="Test",
        )
        text = resp.to_text()
        assert "Artifact:" not in text

    def test_extra_field_still_forbidden(self):
        """extra='forbid' should still be enforced with artifact_ref field."""
        with pytest.raises(ValidationError):
            TimelineResponse(
                voyage_id="das:3456",
                event_count=0,
                events=[],
                artifact_ref="art-abc-123",
                bogus_field="should fail",
            )


# ---------------------------------------------------------------------------
# Reference data preload tests
# ---------------------------------------------------------------------------


class TestReferencePreload:
    def test_returns_false_when_no_manifest_env(self):
        """Without MARITIME_REFERENCE_MANIFEST, should return False immediately."""
        from chuk_mcp_maritime_archives.core.reference_preload import preload_reference_data

        with patch.dict(os.environ, {}, clear=True):
            assert preload_reference_data() is False

    @pytest.mark.asyncio
    async def test_returns_false_when_store_is_none(self, tmp_path):
        """When get_artifact_store() returns None, should return False."""
        from chuk_mcp_maritime_archives.core.reference_preload import _preload_async

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict(
                "sys.modules",
                {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: None)},
            ),
        ):
            result = await _preload_async(tmp_path)
            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_store_import_fails(self, tmp_path):
        """When chuk_mcp_server import raises, should return False."""
        from chuk_mcp_maritime_archives.core.reference_preload import _preload_async

        mock_module = MagicMock()
        mock_module.get_artifact_store = MagicMock(side_effect=RuntimeError("no store"))

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict("sys.modules", {"chuk_mcp_server": mock_module}),
        ):
            result = await _preload_async(tmp_path)
            assert result is False

    def test_sync_wrapper_runs_preload(self, tmp_path):
        """Sync preload_reference_data should run async preload and return result."""
        from chuk_mcp_maritime_archives.core.reference_preload import preload_reference_data

        manifest = {"test.json": "art-t1"}
        manifest_bytes = json.dumps(manifest).encode("utf-8")

        mock_store = AsyncMock()
        mock_store.retrieve = AsyncMock(
            side_effect=lambda aid: {
                "manifest-001": manifest_bytes,
                "art-t1": b'{"test": true}',
            }[aid]
        )

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict(
                "sys.modules",
                {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
            ),
        ):
            result = preload_reference_data(data_dir=tmp_path)
            assert result is True
            assert (tmp_path / "test.json").exists()

    def test_sync_wrapper_handles_exception(self):
        """Sync wrapper should handle asyncio.run exceptions gracefully."""
        from chuk_mcp_maritime_archives.core.reference_preload import preload_reference_data

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch("asyncio.run", side_effect=RuntimeError("event loop crash")),
        ):
            result = preload_reference_data()
            assert result is False

    @pytest.mark.asyncio
    async def test_downloads_missing_files(self, tmp_path):
        """Should download files listed in manifest to data_dir."""
        from chuk_mcp_maritime_archives.core.reference_preload import _preload_async

        manifest = {"wrecks.json": "art-w1", "routes.json": "art-r1"}
        manifest_bytes = json.dumps(manifest).encode("utf-8")

        mock_store = AsyncMock()
        mock_store.retrieve = AsyncMock(
            side_effect=lambda aid: {
                "manifest-001": manifest_bytes,
                "art-w1": b'{"wrecks": []}',
                "art-r1": b'{"routes": []}',
            }[aid]
        )

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict(
                "sys.modules",
                {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
            ),
        ):
            result = await _preload_async(tmp_path)
            assert result is True
            assert (tmp_path / "wrecks.json").exists()
            assert (tmp_path / "routes.json").exists()
            assert json.loads((tmp_path / "wrecks.json").read_text()) == {"wrecks": []}

    @pytest.mark.asyncio
    async def test_skips_existing_files(self, tmp_path):
        """Should skip files that already exist locally."""
        from chuk_mcp_maritime_archives.core.reference_preload import _preload_async

        # Pre-create a file
        existing = tmp_path / "wrecks.json"
        existing.write_text('{"already": "here"}')

        manifest = {"wrecks.json": "art-w1"}
        manifest_bytes = json.dumps(manifest).encode("utf-8")

        mock_store = AsyncMock()
        mock_store.retrieve = AsyncMock(
            side_effect=lambda aid: {
                "manifest-001": manifest_bytes,
            }.get(aid, b"should not be called")
        )

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict(
                "sys.modules",
                {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
            ),
        ):
            result = await _preload_async(tmp_path)
            # No files downloaded (existing file was skipped)
            assert result is False
            # Original content preserved
            assert json.loads(existing.read_text()) == {"already": "here"}

    @pytest.mark.asyncio
    async def test_handles_store_retrieval_failure(self, tmp_path):
        """Should handle store.retrieve() failures gracefully."""
        from chuk_mcp_maritime_archives.core.reference_preload import _preload_async

        manifest = {"wrecks.json": "art-w1"}
        manifest_bytes = json.dumps(manifest).encode("utf-8")

        mock_store = AsyncMock()
        call_count = 0

        async def side_effect(aid):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return manifest_bytes  # manifest retrieval succeeds
            raise RuntimeError("S3 timeout")  # data file fails

        mock_store.retrieve = AsyncMock(side_effect=side_effect)

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict(
                "sys.modules",
                {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
            ),
        ):
            result = await _preload_async(tmp_path)
            assert result is False
            assert not (tmp_path / "wrecks.json").exists()

    @pytest.mark.asyncio
    async def test_handles_manifest_retrieval_failure(self, tmp_path):
        """Should handle manifest retrieval failure gracefully."""
        from chuk_mcp_maritime_archives.core.reference_preload import _preload_async

        mock_store = AsyncMock()
        mock_store.retrieve = AsyncMock(side_effect=RuntimeError("manifest not found"))

        with (
            patch.dict(os.environ, {"MARITIME_REFERENCE_MANIFEST": "manifest-001"}),
            patch.dict(
                "sys.modules",
                {"chuk_mcp_server": MagicMock(get_artifact_store=lambda: mock_store)},
            ),
        ):
            result = await _preload_async(tmp_path)
            assert result is False


# ---------------------------------------------------------------------------
# Data loading edge cases (hull profiles, speed profiles)
# ---------------------------------------------------------------------------


class TestHullProfileLoading:
    def test_load_hull_profiles_already_loaded_returns_early(self):
        """When HULL_PROFILES is already populated, _load_hull_profiles returns immediately."""
        from chuk_mcp_maritime_archives.core.hull_profiles import (
            HULL_PROFILES,
            _load_hull_profiles,
        )

        # Since the module loads at import, HULL_PROFILES is already populated
        assert len(HULL_PROFILES) >= 6
        # Calling again should return the same dict (early return path)
        result = _load_hull_profiles()
        assert result is HULL_PROFILES
        assert len(result) >= 6

    def test_load_hull_profiles_file_not_found(self, tmp_path):
        """When JSON file is missing, should return empty dict and log warning."""
        from chuk_mcp_maritime_archives.core import hull_profiles

        # Save original state
        original = hull_profiles.HULL_PROFILES.copy()
        try:
            # Clear the global to force re-load
            hull_profiles.HULL_PROFILES.clear()
            result = hull_profiles._load_hull_profiles(data_dir=tmp_path)
            assert result == {}
        finally:
            # Restore
            hull_profiles.HULL_PROFILES.update(original)


class TestSpeedProfileLoading:
    def test_load_speed_profiles_file_not_found(self, tmp_path):
        """When JSON file is missing, should log warning and leave empty."""
        from chuk_mcp_maritime_archives.core import speed_profiles

        # Save original state
        original_profiles = speed_profiles._PROFILES.copy()
        original_index = speed_profiles._PROFILES_BY_ROUTE.copy()
        try:
            speed_profiles._PROFILES.clear()
            speed_profiles._PROFILES_BY_ROUTE.clear()
            speed_profiles._load_speed_profiles(data_dir=tmp_path)
            assert speed_profiles._PROFILES == []
            assert speed_profiles._PROFILES_BY_ROUTE == {}
        finally:
            speed_profiles._PROFILES.extend(original_profiles)
            speed_profiles._PROFILES_BY_ROUTE.update(original_index)
