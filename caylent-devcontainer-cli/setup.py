#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Get version from git tag if available, otherwise use a default
version = os.environ.get("GITHUB_REF_NAME", "0.1.0")
if version.startswith("v"):
    version = version[1:]

setup(
    name="caylent-devcontainer-cli",
    version=version,
    description="CLI tool for managing Caylent devcontainers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Caylent",
    author_email="info@caylent.com",
    url="https://github.com/caylent-solutions/devcontainer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "setuptools~=68.0",
        "wheel~=0.40",
        "black~=24.0",
        "flake8~=7.0",
        "isort~=5.0",
        "pytest~=7.0",
        "pytest-cov~=4.0",
    ],
    entry_points={
        "console_scripts": [
            "cdevcontainer=caylent_devcontainer_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)