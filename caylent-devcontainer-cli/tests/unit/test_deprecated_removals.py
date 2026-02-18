"""Tests for S1.1.4 — Remove Deprecated Commands & Features.

These tests verify that deprecated commands, flags, files, and patterns
have been fully removed from the codebase.
"""

import importlib
import os
from unittest.mock import patch

import pytest


class TestEnvCommandRemoved:
    """Verify the env subcommand module has been deleted."""

    def test_env_module_does_not_exist(self):
        """commands/env.py should not be importable."""
        with pytest.raises(ImportError):
            importlib.import_module("caylent_devcontainer_cli.commands.env")

    def test_env_not_registered_in_cli(self):
        """The env subcommand should not be registered in the CLI parser."""
        from caylent_devcontainer_cli.cli import main

        with patch("sys.argv", ["cdevcontainer", "env", "export", "test.json", "-o", "out.sh"]):
            with patch(
                "caylent_devcontainer_cli.utils.version.check_for_updates",
                return_value=True,
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # argparse exits with code 2 for unrecognized commands
                assert exc_info.value.code == 2


class TestInstallCommandRemoved:
    """Verify the install/uninstall commands have been deleted."""

    def test_install_module_does_not_exist(self):
        """commands/install.py should not be importable."""
        with pytest.raises(ImportError):
            importlib.import_module("caylent_devcontainer_cli.commands.install")

    def test_install_not_registered_in_cli(self):
        """The install subcommand should not be registered in the CLI parser."""
        from caylent_devcontainer_cli.cli import main

        with patch("sys.argv", ["cdevcontainer", "install"]):
            with patch(
                "caylent_devcontainer_cli.utils.version.check_for_updates",
                return_value=True,
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2

    def test_uninstall_not_registered_in_cli(self):
        """The uninstall subcommand should not be registered in the CLI parser."""
        from caylent_devcontainer_cli.cli import main

        with patch("sys.argv", ["cdevcontainer", "uninstall"]):
            with patch(
                "caylent_devcontainer_cli.utils.version.check_for_updates",
                return_value=True,
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2


class TestBinCdevcontainerRemoved:
    """Verify the bin/cdevcontainer shell script has been deleted."""

    def test_bin_cdevcontainer_does_not_exist(self):
        """bin/cdevcontainer file should not exist."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bin_path = os.path.join(project_root, "bin", "cdevcontainer")
        assert not os.path.exists(bin_path), f"bin/cdevcontainer still exists at {bin_path}"


class TestYesFlagRemoved:
    """Verify all -y/--yes argument definitions have been removed."""

    def test_cli_main_parser_no_yes_flag(self):
        """The main CLI parser should not accept -y/--yes."""
        from caylent_devcontainer_cli.cli import main

        with patch("sys.argv", ["cdevcontainer", "-y"]):
            with patch(
                "caylent_devcontainer_cli.utils.version.check_for_updates",
                return_value=True,
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # argparse exits with 2 for unrecognized args
                assert exc_info.value.code == 2

    def test_code_parser_no_yes_flag(self):
        """The code command parser should not accept -y/--yes."""
        import argparse

        from caylent_devcontainer_cli.commands.code import register_command

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_command(subparsers)

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["code", "-y"])
        assert exc_info.value.code == 2

    def test_template_parser_no_yes_flag(self):
        """The template command parser should not accept -y/--yes at any level."""
        import argparse

        from caylent_devcontainer_cli.commands.template import register_command

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_command(subparsers)

        # Test at template level
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["template", "-y", "save", "test"])
        assert exc_info.value.code == 2

        # Test at save subcommand level
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["template", "save", "test", "-y"])
        assert exc_info.value.code == 2

        # Test at delete subcommand level
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["template", "delete", "test", "-y"])
        assert exc_info.value.code == 2

        # Test at create subcommand level
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["template", "create", "test", "-y"])
        assert exc_info.value.code == 2

        # Test at upgrade subcommand level
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["template", "upgrade", "test", "-y"])
        assert exc_info.value.code == 2


class TestVersionUpdated:
    """Verify version and Python requirement updates."""

    def test_cli_version_is_2_0_0(self):
        """The CLI version should be 2.0.0."""
        from caylent_devcontainer_cli import __version__

        assert __version__ == "2.0.0"

    def test_pyproject_version_is_2_0_0(self):
        """pyproject.toml should have version 2.0.0."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pyproject_path = os.path.join(project_root, "pyproject.toml")

        with open(pyproject_path, "r") as f:
            content = f.read()

        assert 'version = "2.0.0"' in content

    def test_python_requires_3_10(self):
        """pyproject.toml should require Python >= 3.10."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pyproject_path = os.path.join(project_root, "pyproject.toml")

        with open(pyproject_path, "r") as f:
            content = f.read()

        assert 'requires-python = ">=3.10"' in content
        # Old Python versions should not be in classifiers
        assert "Python :: 3.8" not in content
        assert "Python :: 3.9" not in content


class TestImportHygiene:
    """Verify inline imports have been moved to module level."""

    def test_no_inline_colors_imports_in_template(self):
        """template.py should import COLORS at module level, not inline."""
        import inspect

        from caylent_devcontainer_cli.commands import template

        source = inspect.getsource(template)

        # Count occurrences of inline COLORS import inside function bodies
        # Module-level imports happen before any def/class, so check for imports after def
        lines = source.split("\n")
        in_function = False
        inline_colors_imports = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                in_function = True
            if in_function and "from caylent_devcontainer_cli.utils.ui import COLORS" in stripped:
                inline_colors_imports += 1

        assert inline_colors_imports == 0, (
            f"Found {inline_colors_imports} inline COLORS imports in template.py function bodies"
        )


class TestInstallDirConstantRemoved:
    """Verify INSTALL_DIR constant is removed since install command is gone."""

    def test_install_dir_not_in_constants(self):
        """INSTALL_DIR should be removed from constants.py since install/uninstall are removed."""
        from caylent_devcontainer_cli.utils import constants

        assert not hasattr(constants, "INSTALL_DIR"), "INSTALL_DIR should be removed from constants.py"


class TestCliImportsClean:
    """Verify cli.py does not import removed modules."""

    def test_cli_does_not_import_env(self):
        """cli.py should not import commands.env."""
        import inspect

        from caylent_devcontainer_cli import cli

        source = inspect.getsource(cli)
        assert "from caylent_devcontainer_cli.commands import" in source or "import" in source
        # Ensure env is not in any import statement
        assert (
            "env" not in source.split("from caylent_devcontainer_cli.commands import")[1].split("\n")[0]
            if "from caylent_devcontainer_cli.commands import" in source
            else True
        )

    def test_cli_does_not_import_install(self):
        """cli.py should not import commands.install."""
        import inspect

        from caylent_devcontainer_cli import cli

        source = inspect.getsource(cli)
        assert "install" not in source, "cli.py should not reference 'install'"
