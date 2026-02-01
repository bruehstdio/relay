"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path

import yaml

from relay.models import PipelineConfig, RelayConfig


def load_config(path: Path) -> RelayConfig:
    """Load Relay configuration from a YAML file."""
    if not path.exists():
        return RelayConfig()

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    return RelayConfig.model_validate(data)


def load_pipeline(path: Path) -> PipelineConfig:
    """Load a pipeline configuration from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    return PipelineConfig.model_validate(data)


def find_config_file() -> Path | None:
    """Find a relay configuration file in the current directory or parents."""
    names = ["relay.yml", "relay.yaml", ".relay.yml", ".relay.yaml"]

    current = Path.cwd()
    for _ in range(10):  # Limit search depth
        for name in names:
            path = current / name
            if path.exists():
                return path
        if current == current.parent:
            break
        current = current.parent

    return None
