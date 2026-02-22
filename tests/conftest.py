"""Shared pytest fixtures for test isolation helpers."""

from pathlib import Path

import pytest

import tutr.config as config_module


@pytest.fixture()
def tutr_config_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Redirect tutr config paths to a temp directory."""
    config_dir = tmp_path / ".tutr"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    return config_dir, config_file


@pytest.fixture()
def config_dir(tutr_config_paths: tuple[Path, Path]) -> Path:
    return tutr_config_paths[0]


@pytest.fixture()
def config_file(tutr_config_paths: tuple[Path, Path]) -> Path:
    return tutr_config_paths[1]


@pytest.fixture()
def isolated_update_cache_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect update-check cache file to a temp path."""
    cache_file = tmp_path / "update-check.json"
    monkeypatch.setattr("tutr.update_check.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("tutr.update_check.UPDATE_CHECK_CACHE_FILE", cache_file)
    return cache_file
