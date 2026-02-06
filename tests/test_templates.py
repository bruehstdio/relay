"""Tests for Relay template system."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from relay.models import PipelineConfig, StepConfig
from relay.templates import (
    TemplateManager,
    TemplateNotFoundError,
    TemplateVersionError,
    _parse_template_ref,
)


class TestParseTemplateRef:
    """Test template reference parsing."""

    def test_parse_simple_name(self) -> None:
        """Parse template reference without version."""
        name, version = _parse_template_ref("python-project")
        assert name == "python-project"
        assert version is None

    def test_parse_with_version(self) -> None:
        """Parse template reference with version."""
        name, version = _parse_template_ref("python-project@1.0.0")
        assert name == "python-project"
        assert version == "1.0.0"

    def test_parse_with_complex_version(self) -> None:
        """Parse template reference with complex version."""
        name, version = _parse_template_ref("my-template@v2.1.0-beta")
        assert name == "my-template"
        assert version == "v2.1.0-beta"


class TestTemplateManager:
    """Test TemplateManager functionality."""

    @pytest.fixture
    def temp_dirs(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create temporary user and builtin directories."""
        user_dir = tmp_path / "user"
        builtin_dir = tmp_path / "builtin"
        user_dir.mkdir(parents=True)
        builtin_dir.mkdir(parents=True)
        return user_dir, builtin_dir

    @pytest.fixture
    def manager(self, temp_dirs: tuple[Path, Path]) -> TemplateManager:
        """Create a TemplateManager with temp directories."""
        user_dir, builtin_dir = temp_dirs
        return TemplateManager(user_dir=user_dir, builtin_dir=builtin_dir)

    def create_template(
        self,
        directory: Path,
        name: str,
        version: str | None,
        data: dict[str, Any],
    ) -> Path:
        """Helper to create a template file."""
        if version:
            filename = f"{name}@{version}.yml"
        else:
            filename = f"{name}.yml"
        path = directory / filename
        path.write_text(yaml.dump(data))
        return path

    def test_load_builtin_template(self, manager: TemplateManager, temp_dirs: tuple[Path, Path]) -> None:
        """Load a built-in template."""
        builtin_dir = temp_dirs[1]
        template_data = {
            "name": "test-template",
            "description": "A test template",
            "steps": [
                {"name": "step1", "agent": "claude-code", "prompt": "Test prompt"}
            ],
        }
        self.create_template(builtin_dir, "test-template", "1.0.0", template_data)

        loaded = manager.load_template("test-template@1.0.0")
        assert loaded["name"] == "test-template"
        assert loaded["description"] == "A test template"

    def test_load_user_template_overrides_builtin(
        self,
        manager: TemplateManager,
        temp_dirs: tuple[Path, Path],
    ) -> None:
        """User template should override built-in template."""
        user_dir, builtin_dir = temp_dirs

        builtin_data = {"name": "builtin", "steps": []}
        user_data = {"name": "user", "steps": []}

        self.create_template(builtin_dir, "my-template", "1.0.0", builtin_data)
        self.create_template(user_dir, "my-template", "1.0.0", user_data)

        loaded = manager.load_template("my-template@1.0.0")
        assert loaded["name"] == "user"

    def test_load_template_not_found(self, manager: TemplateManager) -> None:
        """Loading non-existent template raises error."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            manager.load_template("nonexistent")
        assert "nonexistent" in str(exc_info.value)

    def test_list_templates(self, manager: TemplateManager, temp_dirs: tuple[Path, Path]) -> None:
        """List available templates."""
        user_dir, builtin_dir = temp_dirs

        self.create_template(
            builtin_dir,
            "builtin-template",
            "1.0.0",
            {"name": "builtin", "description": "Built-in template", "steps": []},
        )
        self.create_template(
            user_dir,
            "user-template",
            "2.0.0",
            {"name": "user", "description": "User template", "steps": []},
        )

        templates = manager.list_templates()
        names = {t["name"] for t in templates}

        assert "builtin-template" in names
        assert "user-template" in names

    def test_show_template(self, manager: TemplateManager, temp_dirs: tuple[Path, Path]) -> None:
        """Show template details."""
        user_dir, builtin_dir = temp_dirs
        template_data = {
            "name": "test-template",
            "description": "Test description",
            "steps": [{"name": "step1", "agent": "claude-code", "prompt": "Do something"}],
        }
        self.create_template(builtin_dir, "test-template", "1.0.0", template_data)

        info = manager.show_template("test-template@1.0.0")
        assert info["name"] == "test-template"
        assert info["version"] == "1.0.0"
        assert info["description"] == "Test description"
        assert len(info["data"]["steps"]) == 1


class TestTemplateResolution:
    """Test template resolution and merging."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TemplateManager:
        """Create a TemplateManager with a temp directory."""
        return TemplateManager(user_dir=tmp_path, builtin_dir=tmp_path)

    def test_resolve_without_template(self, manager: TemplateManager) -> None:
        """Resolve pipeline without template reference."""
        user_config = {
            "name": "my-pipeline",
            "description": "My custom pipeline",
            "steps": [{"name": "custom", "agent": "claude-code", "prompt": "Do it"}],
        }

        result = manager.resolve_pipeline(user_config)

        assert result.name == "my-pipeline"
        assert result.description == "My custom pipeline"
        assert len(result.steps) == 1

    def test_resolve_with_template(self, manager: TemplateManager, tmp_path: Path) -> None:
        """Resolve pipeline with template inheritance."""
        template_data = {
            "name": "base-template",
            "description": "Base template",
            "steps": [
                {"name": "step1", "agent": "claude-code", "prompt": "First step"},
                {"name": "step2", "agent": "opencode", "prompt": "Second step"},
            ],
        }
        template_file = tmp_path / "base@1.0.0.yml"
        template_file.write_text(yaml.dump(template_data))

        user_config = {
            "template": "base@1.0.0",
            "name": "my-pipeline",
            "steps": [{"name": "step1", "prompt": "Overridden first step"}],
        }

        result = manager.resolve_pipeline(user_config)

        assert result.name == "my-pipeline"  # User overrides
        assert result.description == "Base template"  # From template
        assert len(result.steps) == 2
        assert result.steps[0].prompt == "Overridden first step"  # User overrides
        assert result.steps[1].prompt == "Second step"  # From template

    def test_resolve_adds_new_steps(self, manager: TemplateManager, tmp_path: Path) -> None:
        """User can add new steps not in template."""
        template_data = {
            "name": "base",
            "steps": [{"name": "existing", "agent": "claude-code", "prompt": "Existing"}],
        }
        template_file = tmp_path / "base@1.0.0.yml"
        template_file.write_text(yaml.dump(template_data))

        user_config = {
            "template": "base@1.0.0",
            "steps": [
                {"name": "new-step", "agent": "opencode", "prompt": "New step"}
            ],
        }

        result = manager.resolve_pipeline(user_config)

        assert len(result.steps) == 2
        step_names = [s.name for s in result.steps]
        assert "existing" in step_names
        assert "new-step" in step_names

    def test_resolve_template_field_removed(self, manager: TemplateManager, tmp_path: Path) -> None:
        """Template field is removed from resolved pipeline."""
        template_data = {
            "name": "base",
            "steps": [{"name": "step1", "agent": "claude-code", "prompt": "Do it"}],
        }
        template_file = tmp_path / "base@1.0.0.yml"
        template_file.write_text(yaml.dump(template_data))

        user_config = {
            "template": "base@1.0.0",
            "name": "my-pipeline",
            "steps": [],
        }

        result = manager.resolve_pipeline(user_config)

        # template field should be removed
        assert result.template is None


class TestBuiltinTemplates:
    """Test that built-in templates are valid."""

    def test_python_project_template(self) -> None:
        """Python project template is valid YAML."""
        from relay.templates import DEFAULT_TEMPLATES_DIR

        template_file = DEFAULT_TEMPLATES_DIR / "python-project@1.0.0.yml"
        if template_file.exists():
            with open(template_file) as f:
                data = yaml.safe_load(f)
            assert "steps" in data
            assert len(data["steps"]) >= 3

    def test_node_project_template(self) -> None:
        """Node project template is valid YAML."""
        from relay.templates import DEFAULT_TEMPLATES_DIR

        template_file = DEFAULT_TEMPLATES_DIR / "node-project@1.0.0.yml"
        if template_file.exists():
            with open(template_file) as f:
                data = yaml.safe_load(f)
            assert "steps" in data
            assert len(data["steps"]) >= 4

    def test_docker_build_template(self) -> None:
        """Docker build template is valid YAML."""
        from relay.templates import DEFAULT_TEMPLATES_DIR

        template_file = DEFAULT_TEMPLATES_DIR / "docker-build@1.0.0.yml"
        if template_file.exists():
            with open(template_file) as f:
                data = yaml.safe_load(f)
            assert "steps" in data

    def test_github_release_template(self) -> None:
        """GitHub release template is valid YAML."""
        from relay.templates import DEFAULT_TEMPLATES_DIR

        template_file = DEFAULT_TEMPLATES_DIR / "github-release@1.0.0.yml"
        if template_file.exists():
            with open(template_file) as f:
                data = yaml.safe_load(f)
            assert "steps" in data
