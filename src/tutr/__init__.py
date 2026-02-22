"""tutr - a CLI tool."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tutr")
except PackageNotFoundError:
    __version__ = "0.0.0"
