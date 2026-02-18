"""Functional tests for VERSION file handling in setup-devcontainer."""

import os
import tempfile

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup import create_version_file


def test_create_version_file_writes_correct_version():
    """Test that create_version_file writes the current CLI version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        devcontainer_dir = os.path.join(tmpdir, ".devcontainer")
        os.makedirs(devcontainer_dir)

        create_version_file(tmpdir)

        version_file = os.path.join(devcontainer_dir, "VERSION")
        assert os.path.isfile(version_file)

        with open(version_file, "r") as f:
            version = f.read().strip()

        assert version == __version__
        assert "." in version, "VERSION should be in semver format"
