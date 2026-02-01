"""Configuration loading utilities."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from relay.models import PipelineConfig, RelayConfig


def _interpolate_env_vars(value: Any) -> Any:
    """Recursively interpolate environment variables in a value.
    
    Supports ${VAR} and ${VAR:-default} syntax.
    """
    if isinstance(value, str):
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match: re.Match) -> str:
            var_expr = match.group(1)
            if ':-' in var_expr:
                var_name, default = var_expr.split(':-', 1)
                return os.environ.get(var_name, default)
            else:
                return os.environ.get(var_expr, '')
        
        return re.sub(pattern, replace_var, value)
    elif isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    return value


def load_config(path: Path) -> RelayConfig:
    """Load Relay configuration from a YAML file."""
    if not path.exists():
        return RelayConfig()

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    data = _interpolate_env_vars(data)
    return RelayConfig.model_validate(data)


def load_pipeline(path: Path) -> PipelineConfig:
    """Load a pipeline configuration from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    data = _interpolate_env_vars(data)
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
