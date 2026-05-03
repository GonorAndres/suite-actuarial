"""
Tests para el CLI de suite_actuarial (cli.py)

Cubre: main(), mostrar_ayuda(), ejecutar_demo(), ejecutar_api(),
       flags --help/-h, --version/-v, comandos desconocidos.
"""

from unittest.mock import patch

import pytest

from suite_actuarial import __version__
from suite_actuarial.cli import ejecutar_api, ejecutar_demo, main, mostrar_ayuda


# ---------------------------------------------------------------------------
# main() -- no args
# ---------------------------------------------------------------------------
class TestMainNoArgs:
    def test_main_no_args_shows_help(self, capsys):
        """Calling main() with no args prints help text and returns 0."""
        with patch("sys.argv", ["seguros"]):
            rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        # Help text includes the word "Comandos disponibles"
        assert "Comandos disponibles" in out

    def test_main_no_args_prints_banner(self, capsys):
        """Banner line with version is always printed."""
        with patch("sys.argv", ["seguros"]):
            main()
        out = capsys.readouterr().out
        assert f"v{__version__}" in out


# ---------------------------------------------------------------------------
# main() -- help flag
# ---------------------------------------------------------------------------
class TestMainHelp:
    @pytest.mark.parametrize("flag", ["--help", "-h", "help"])
    def test_main_help_flag(self, flag, capsys):
        """main() with help flags shows help and returns 0."""
        with patch("sys.argv", ["seguros", flag]):
            rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Comandos disponibles" in out


# ---------------------------------------------------------------------------
# main() -- version flag
# ---------------------------------------------------------------------------
class TestMainVersion:
    @pytest.mark.parametrize("flag", ["--version", "-v", "version"])
    def test_main_version_flag(self, flag, capsys):
        """main() with version flags prints version and returns 0."""
        with patch("sys.argv", ["seguros", flag]):
            rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        assert __version__ in out


# ---------------------------------------------------------------------------
# main() -- demo command
# ---------------------------------------------------------------------------
class TestMainDemo:
    def test_main_demo_command(self, capsys):
        """main() with 'demo' dispatches to ejecutar_demo and returns 0."""
        with patch("sys.argv", ["seguros", "demo"]):
            rc = main()
        assert rc == 0
        out = capsys.readouterr().out
        # ejecutar_demo prints at least one of these even on error paths
        assert "Demostracion" in out or "Error" in out


# ---------------------------------------------------------------------------
# main() -- api command (mock uvicorn to avoid server start)
# ---------------------------------------------------------------------------
class TestMainApi:
    def test_main_api_command_starts(self, capsys):
        """main() with 'api' calls uvicorn.run (mocked) and returns 0."""
        with (
            patch("sys.argv", ["seguros", "api"]),
            patch("uvicorn.run") as mock_uvicorn,
        ):
            rc = main()
        assert rc == 0
        mock_uvicorn.assert_called_once_with(
            "suite_actuarial.api.main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
        )

    def test_api_prints_startup_message(self, capsys):
        """ejecutar_api() prints URL info before starting server."""
        with patch("uvicorn.run"):
            ejecutar_api()
        out = capsys.readouterr().out
        assert "http://localhost:8000" in out
        assert "/docs" in out

    def test_api_missing_uvicorn(self, capsys):
        """When uvicorn is not installed, ejecutar_api prints an error."""
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "uvicorn":
                raise ImportError("No module named 'uvicorn'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            ejecutar_api()
        out = capsys.readouterr().out
        assert "Error" in out or "no instalado" in out.lower() or "pip install" in out


# ---------------------------------------------------------------------------
# main() -- unknown command
# ---------------------------------------------------------------------------
class TestMainUnknown:
    def test_main_unknown_command_returns_error(self, capsys):
        """main() with an unrecognised command returns 1."""
        with patch("sys.argv", ["seguros", "unknown_xyz"]):
            rc = main()
        assert rc == 1

    def test_main_unknown_command_prints_message(self, capsys):
        """Error message mentions the bad command."""
        with patch("sys.argv", ["seguros", "unknown_xyz"]):
            main()
        out = capsys.readouterr().out
        assert "unknown_xyz" in out
        assert "desconocido" in out.lower()


# ---------------------------------------------------------------------------
# mostrar_ayuda()
# ---------------------------------------------------------------------------
class TestMostrarAyuda:
    def test_mostrar_ayuda_contains_commands(self, capsys):
        """Help text lists the 'demo' and 'api' subcommands."""
        mostrar_ayuda()
        out = capsys.readouterr().out
        assert "demo" in out
        assert "api" in out

    def test_mostrar_ayuda_contains_flags(self, capsys):
        """Help text lists --help and --version flags."""
        mostrar_ayuda()
        out = capsys.readouterr().out
        assert "--help" in out
        assert "--version" in out


# ---------------------------------------------------------------------------
# ejecutar_demo()
# ---------------------------------------------------------------------------
class TestEjecutarDemo:
    def test_ejecutar_demo_prints_output(self, capsys):
        """ejecutar_demo() prints pricing results or a handled error."""
        ejecutar_demo()
        out = capsys.readouterr().out
        # The function always prints the header
        assert "Demostracion" in out
        # Then either success or the FileNotFoundError path
        success = "Prima Neta" in out or "completada" in out.lower()
        handled_error = "Error" in out
        assert success or handled_error, (
            "Expected either pricing output or a handled error message"
        )


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------
class TestVersionConsistency:
    def test_version_matches_package(self, capsys):
        """The version printed by CLI matches suite_actuarial.__version__."""
        with patch("sys.argv", ["seguros", "--version"]):
            main()
        out = capsys.readouterr().out
        assert __version__ in out

    def test_version_is_semver(self):
        """__version__ looks like a semantic version string."""
        parts = __version__.split(".")
        assert len(parts) >= 2, "Version should have at least major.minor"
        for p in parts:
            # Each part should be numeric (ignoring pre-release suffixes)
            base = p.split("-")[0].split("+")[0]
            assert base.isdigit(), f"Version part '{p}' is not numeric"
