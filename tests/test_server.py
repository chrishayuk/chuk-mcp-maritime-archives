"""Tests for server initialization and async_server setup."""

import os
import sys
from unittest.mock import MagicMock, patch


class TestInitArtifactStore:
    """Test _init_artifact_store with various environment configurations."""

    def _import_init(self):
        """Import fresh to avoid module-level side effects."""
        with patch.dict("sys.modules", {"chuk_mcp_server": MagicMock()}):
            from chuk_mcp_maritime_archives.server import _init_artifact_store

            return _init_artifact_store

    def test_memory_provider_default(self):
        """Default memory provider should succeed."""
        mock_store = MagicMock()
        mock_set_global = MagicMock()

        with patch.dict(os.environ, {}, clear=False):
            init_fn = self._import_init()
            with patch.dict(
                "sys.modules",
                {
                    "chuk_artifacts": MagicMock(ArtifactStore=mock_store),
                    "chuk_mcp_server": MagicMock(set_global_artifact_store=mock_set_global),
                },
            ):
                result = init_fn()
                assert result is True

    def test_s3_provider_missing_credentials(self):
        """S3 provider without credentials should return False."""
        env = {"CHUK_ARTIFACTS_PROVIDER": "s3"}
        with patch.dict(os.environ, env, clear=True):
            init_fn = self._import_init()
            result = init_fn()
            assert result is False

    def test_s3_provider_with_credentials(self):
        """S3 provider with credentials should succeed."""
        env = {
            "CHUK_ARTIFACTS_PROVIDER": "s3",
            "BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "key",
            "AWS_SECRET_ACCESS_KEY": "secret",
        }
        mock_store = MagicMock()
        mock_set_global = MagicMock()

        with patch.dict(os.environ, env, clear=True):
            init_fn = self._import_init()
            with patch.dict(
                "sys.modules",
                {
                    "chuk_artifacts": MagicMock(ArtifactStore=mock_store),
                    "chuk_mcp_server": MagicMock(set_global_artifact_store=mock_set_global),
                },
            ):
                result = init_fn()
                assert result is True

    def test_filesystem_provider_missing_path(self):
        """Filesystem provider without path should fall back to memory."""
        env = {"CHUK_ARTIFACTS_PROVIDER": "filesystem"}
        mock_store = MagicMock()
        mock_set_global = MagicMock()

        with patch.dict(os.environ, env, clear=True):
            init_fn = self._import_init()
            with patch.dict(
                "sys.modules",
                {
                    "chuk_artifacts": MagicMock(ArtifactStore=mock_store),
                    "chuk_mcp_server": MagicMock(set_global_artifact_store=mock_set_global),
                },
            ):
                result = init_fn()
                assert result is True

    def test_filesystem_provider_with_path(self):
        """Filesystem provider with path should succeed."""
        env = {
            "CHUK_ARTIFACTS_PROVIDER": "filesystem",
            "CHUK_ARTIFACTS_PATH": "/tmp/test_artifacts",
        }
        mock_store = MagicMock()
        mock_set_global = MagicMock()

        with patch.dict(os.environ, env, clear=True):
            init_fn = self._import_init()
            with (
                patch.dict(
                    "sys.modules",
                    {
                        "chuk_artifacts": MagicMock(ArtifactStore=mock_store),
                        "chuk_mcp_server": MagicMock(set_global_artifact_store=mock_set_global),
                    },
                ),
                patch("pathlib.Path.mkdir"),
            ):
                result = init_fn()
                assert result is True

    def test_init_exception_returns_false(self):
        """Exception during init should return False."""
        env = {"CHUK_ARTIFACTS_PROVIDER": "memory"}
        with patch.dict(os.environ, env, clear=True):
            init_fn = self._import_init()
            with patch.dict(
                "sys.modules",
                {
                    "chuk_artifacts": MagicMock(
                        ArtifactStore=MagicMock(side_effect=RuntimeError("fail"))
                    ),
                    "chuk_mcp_server": MagicMock(),
                },
            ):
                result = init_fn()
                assert result is False


class TestMainFunction:
    """Test the main() CLI entry point."""

    def _import_main(self):
        with patch.dict("sys.modules", {"chuk_mcp_server": MagicMock()}):
            from chuk_mcp_maritime_archives.server import main

            return main

    def _make_mock_async_server(self):
        """Create a mock async_server module with a mock mcp object."""
        mock_mcp = MagicMock()
        mock_module = MagicMock()
        mock_module.mcp = mock_mcp
        return mock_mcp, mock_module

    def test_main_stdio_mode(self):
        """Test main() in explicit stdio mode."""
        mock_mcp, mock_async_server = self._make_mock_async_server()
        with (
            patch.dict(
                "sys.modules",
                {
                    "chuk_mcp_server": MagicMock(),
                    "chuk_mcp_maritime_archives.async_server": mock_async_server,
                },
            ),
            patch("chuk_mcp_maritime_archives.server._init_artifact_store"),
            patch("chuk_mcp_maritime_archives.server.preload_reference_data", create=True),
            patch("sys.argv", ["server", "stdio"]),
        ):
            main_fn = self._import_main()
            main_fn()
            mock_mcp.run.assert_called_once_with(stdio=True)

    def test_main_http_mode(self):
        """Test main() in explicit http mode."""
        mock_mcp, mock_async_server = self._make_mock_async_server()
        with (
            patch.dict(
                "sys.modules",
                {
                    "chuk_mcp_server": MagicMock(),
                    "chuk_mcp_maritime_archives.async_server": mock_async_server,
                },
            ),
            patch("chuk_mcp_maritime_archives.server._init_artifact_store"),
            patch("chuk_mcp_maritime_archives.server.preload_reference_data", create=True),
            patch("sys.argv", ["server", "http", "--host", "0.0.0.0", "--port", "9000"]),
        ):
            main_fn = self._import_main()
            main_fn()
            mock_mcp.run.assert_called_once_with(host="0.0.0.0", port=9000, stdio=False)

    def test_main_auto_detect_stdio(self):
        """Test main() auto-detects stdio when MCP_STDIO env is set."""
        mock_mcp, mock_async_server = self._make_mock_async_server()
        with (
            patch.dict(
                "sys.modules",
                {
                    "chuk_mcp_server": MagicMock(),
                    "chuk_mcp_maritime_archives.async_server": mock_async_server,
                },
            ),
            patch("chuk_mcp_maritime_archives.server._init_artifact_store"),
            patch("chuk_mcp_maritime_archives.server.preload_reference_data", create=True),
            patch("sys.argv", ["server"]),
            patch.dict(os.environ, {"MCP_STDIO": "1"}),
        ):
            main_fn = self._import_main()
            main_fn()
            mock_mcp.run.assert_called_once_with(stdio=True)

    def test_main_auto_detect_http(self):
        """Test main() defaults to HTTP when stdin is a tty."""
        mock_mcp, mock_async_server = self._make_mock_async_server()
        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        with (
            patch.dict(
                "sys.modules",
                {
                    "chuk_mcp_server": MagicMock(),
                    "chuk_mcp_maritime_archives.async_server": mock_async_server,
                },
            ),
            patch("chuk_mcp_maritime_archives.server._init_artifact_store"),
            patch("chuk_mcp_maritime_archives.server.preload_reference_data", create=True),
            patch("sys.argv", ["server"]),
            patch.dict(os.environ, {}, clear=True),
            patch.object(sys, "stdin", mock_stdin),
        ):
            main_fn = self._import_main()
            main_fn()
            mock_mcp.run.assert_called_once_with(host="localhost", port=8005, stdio=False)

    def test_main_auto_detect_pipe(self):
        """Test main() auto-detects stdio when stdin is not a tty (piped)."""
        mock_mcp, mock_async_server = self._make_mock_async_server()
        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False
        with (
            patch.dict(
                "sys.modules",
                {
                    "chuk_mcp_server": MagicMock(),
                    "chuk_mcp_maritime_archives.async_server": mock_async_server,
                },
            ),
            patch("chuk_mcp_maritime_archives.server._init_artifact_store"),
            patch("chuk_mcp_maritime_archives.server.preload_reference_data", create=True),
            patch("sys.argv", ["server"]),
            patch.dict(os.environ, {}, clear=True),
            patch.object(sys, "stdin", mock_stdin),
        ):
            main_fn = self._import_main()
            main_fn()
            mock_mcp.run.assert_called_once_with(stdio=True)


class TestAsyncServer:
    """Test async_server module-level setup."""

    def test_imports_and_registers_tools(self):
        """async_server.py should create mcp and manager and register all tools."""
        mock_chuk_mcp = MagicMock()
        mock_server_instance = MagicMock()
        mock_chuk_mcp.ChukMCPServer.return_value = mock_server_instance

        with patch.dict("sys.modules", {"chuk_mcp_server": mock_chuk_mcp}):
            import importlib

            import chuk_mcp_maritime_archives.async_server as async_mod

            importlib.reload(async_mod)

            assert hasattr(async_mod, "mcp")
            assert hasattr(async_mod, "manager")


class TestToolsInit:
    """Test tools __init__.py exports."""

    def test_all_register_functions_exported(self):
        from chuk_mcp_maritime_archives.tools import (
            register_archive_tools,
            register_cargo_tools,
            register_crew_tools,
            register_discovery_tools,
            register_export_tools,
            register_position_tools,
            register_vessel_tools,
            register_voyage_tools,
            register_wreck_tools,
        )

        assert callable(register_archive_tools)
        assert callable(register_cargo_tools)
        assert callable(register_crew_tools)
        assert callable(register_discovery_tools)
        assert callable(register_export_tools)
        assert callable(register_position_tools)
        assert callable(register_vessel_tools)
        assert callable(register_voyage_tools)
        assert callable(register_wreck_tools)
