"""Template management for Relay pipelines."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

from relay.models import PipelineConfig

# Default templates directory
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "data" / "templates"
USER_TEMPLATES_DIR = Path.home() / ".relay" / "templates"


class TemplateNotFoundError(Exception):
    """Raised when a template is not found."""

    pass


class TemplateVersionError(Exception):
    """Raised when a template version is invalid or not found."""

    pass


def _parse_template_ref(template_ref: str) -> tuple[str, Optional[str]]:
    """Parse a template reference like 'python-project@1.0.0'.

    Returns tuple of (name, version). Version is None if not specified.
    """
    match = re.match(r"^([^@]+)(?:@(.+))?$", template_ref)
    if not match:
        raise TemplateVersionError(f"Invalid template reference: {template_ref}")
    return match.group(1), match.group(2)


class TemplateManager:
    """Manages pipeline templates."""

    def __init__(
        self,
        user_dir: Optional[Path] = None,
        builtin_dir: Optional[Path] = None,
    ) -> None:
        """Initialize template manager.

        Args:
            user_dir: Directory for user-defined templates
            builtin_dir: Directory for built-in templates
        """
        self.user_dir = user_dir or USER_TEMPLATES_DIR
        self.builtin_dir = builtin_dir or DEFAULT_TEMPLATES_DIR

    def _find_template_file(self, name: str, version: Optional[str] = None) -> Optional[Path]:
        """Find a template file by name and optional version.

        Checks user directory first, then built-in directory.
        """
        # Build filename with version if specified
        if version:
            filename = f"{name}@{version}.yml"
            versioned_alt = f"{name}@{version}.yaml"
        else:
            filename = f"{name}.yml"
            versioned_alt = f"{name}.yaml"

        # Check user directory first
        user_path_yml = self.user_dir / filename
        user_path_yaml = self.user_dir / versioned_alt
        if user_path_yml.exists():
            return user_path_yml
        if user_path_yaml.exists():
            return user_path_yaml

        # Check built-in directory
        builtin_path_yml = self.builtin_dir / filename
        builtin_path_yaml = self.builtin_dir / versioned_alt
        if builtin_path_yml.exists():
            return builtin_path_yml
        if builtin_path_yaml.exists():
            return builtin_path_yaml

        # If no version specified, look for any version
        if version is None:
            # Look in user dir first
            for pattern in [f"{name}@*.yml", f"{name}@*.yaml"]:
                matches = list(self.user_dir.glob(pattern))
                if matches:
                    return matches[0]
            # Then built-in dir
            for pattern in [f"{name}@*.yml", f"{name}@*.yaml"]:
                matches = list(self.builtin_dir.glob(pattern))
                if matches:
                    return matches[0]

        return None

    def load_template(self, template_ref: str) -> dict[str, Any]:
        """Load a template by reference.

        Args:
            template_ref: Template reference like 'python-project@1.0.0'

        Returns:
            Template data as dictionary

        Raises:
            TemplateNotFoundError: If template not found
        """
        name, version = _parse_template_ref(template_ref)
        template_file = self._find_template_file(name, version)

        if not template_file:
            if version:
                raise TemplateNotFoundError(
                    f"Template '{name}' version '{version}' not found"
                )
            raise TemplateNotFoundError(f"Template '{name}' not found")

        with open(template_file) as f:
            return yaml.safe_load(f) or {}

    def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates.

        Returns list of template metadata dicts with keys:
        - name: Template name
        - version: Template version
        - description: Template description
        - source: 'builtin' or 'user'
        """
        templates: dict[str, dict[str, Any]] = {}

        # Scan directories
        for source, directory in [
            ("builtin", self.builtin_dir),
            ("user", self.user_dir),
        ]:
            if not directory.exists():
                continue

            for file in directory.glob("*.yml"):
                self._add_template_from_file(file, source, templates)
            for file in directory.glob("*.yaml"):
                self._add_template_from_file(file, source, templates)

        return list(templates.values())

    def _add_template_from_file(
        self,
        file: Path,
        source: str,
        templates: dict[str, dict[str, Any]],
    ) -> None:
        """Add a template from a file to the templates dict."""
        # Parse filename for name and version
        match = re.match(r"^([^@]+)(?:@(.+))?\.(yml|yaml)$", file.name)
        if not match:
            return

        name = match.group(1)
        version = match.group(2) or "latest"

        # Load template for description
        try:
            with open(file) as f:
                data = yaml.safe_load(f) or {}
            description = data.get("description", "No description")
        except Exception:
            description = "Error loading template"

        # Only keep the first (user overrides builtin)
        if name not in templates:
            templates[name] = {
                "name": name,
                "version": version,
                "description": description,
                "source": source,
                "file": str(file),
            }

    def show_template(self, template_ref: str) -> dict[str, Any]:
        """Show template details.

        Returns:
            Template data with metadata
        """
        name, version = _parse_template_ref(template_ref)
        template_file = self._find_template_file(name, version)

        if not template_file:
            raise TemplateNotFoundError(f"Template '{template_ref}' not found")

        with open(template_file) as f:
            data = yaml.safe_load(f) or {}

        # Add metadata
        file_version = None
        match = re.match(r"^[^@]+@(.+)\.(yml|yaml)$", template_file.name)
        if match:
            file_version = match.group(1)

        return {
            "name": name,
            "version": file_version or "latest",
            "description": data.get("description", "No description"),
            "data": data,
            "source": "user" if self.user_dir in template_file.parents else "builtin",
        }

    def resolve_pipeline(
        self,
        user_config: dict[str, Any],
    ) -> PipelineConfig:
        """Resolve a pipeline configuration with template inheritance.

        User config can specify:
        - template: Template reference to use as base
        - template_overrides: Steps to override from template

        Args:
            user_config: User's pipeline configuration

        Returns:
            Resolved PipelineConfig
        """
        template_ref = user_config.get("template")
        if not template_ref:
            # No template, return as-is
            return PipelineConfig.model_validate(user_config)

        # Load template
        template_data = self.load_template(template_ref)

        # Merge user config with template
        merged = self._merge_configs(template_data, user_config)

        return PipelineConfig.model_validate(merged)

    def _merge_configs(
        self,
        template: dict[str, Any],
        user: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge user config into template.

        - User name/description override template
        - User steps override template steps by name
        - Additional user steps are appended
        """
        merged = dict(template)

        # Remove template field from merged result
        merged.pop("template", None)

        # Override top-level fields (except steps)
        for key in ["name", "description"]:
            if key in user:
                merged[key] = user[key]

        # Merge steps
        template_steps = {s["name"]: s for s in merged.get("steps", [])}
        user_steps = user.get("steps", [])

        # Track order from template
        step_order = [s["name"] for s in merged.get("steps", [])]

        # Apply user overrides
        for user_step in user_steps:
            step_name = user_step.get("name")
            if step_name in template_steps:
                # Override existing step
                template_steps[step_name].update(user_step)
            else:
                # New step - add to order and dict
                template_steps[step_name] = user_step
                step_order.append(step_name)

        # Rebuild steps list in order
        merged["steps"] = [
            template_steps[name] for name in step_order if name in template_steps
        ]

        return merged

    def install_builtin_templates(self) -> list[str]:
        """Install built-in templates to user directory.

        Returns list of installed template names.
        """
        installed = []
        self.user_dir.mkdir(parents=True, exist_ok=True)

        for file in self.builtin_dir.glob("*.yml"):
            target = self.user_dir / file.name
            if not target.exists():
                import shutil
                shutil.copy(file, target)
                installed.append(file.stem)

        return installed


def get_template_manager() -> TemplateManager:
    """Get the default template manager."""
    return TemplateManager()
