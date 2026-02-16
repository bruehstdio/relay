"""Tests for Relay artifact caching system."""

from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from relay.cache import (
    CacheAction,
    CacheBackend,
    CacheEntry,
    CacheKeyResolver,
    CacheManager,
    LocalFilesystemBackend,
)
from relay.models import CacheConfig, StepCacheConfig


class TestCacheKeyResolver:
    """Test cache key resolution."""

    def test_resolve_static_string(self, tmp_path: Path) -> None:
        """Resolve a static cache key."""
        resolver = CacheKeyResolver(tmp_path)
        result = resolver.resolve("my-static-key")
        assert result == "my-static-key"

    def test_resolve_with_hash(self, tmp_path: Path) -> None:
        """Resolve key with file hash."""
        # Create a file to hash
        test_file = tmp_path / "package-lock.json"
        test_content = b'{"name": "test"}'
        test_file.write_bytes(test_content)

        resolver = CacheKeyResolver(tmp_path)
        result = resolver.resolve("npm-{{ hash('package-lock.json') }}")

        expected_hash = hashlib.sha256(test_content).hexdigest()[:16]
        assert result == f"npm-{expected_hash}"

    def test_resolve_with_env(self, tmp_path: Path) -> None:
        """Resolve key with environment variable."""
        env = {"NODE_VERSION": "18"}
        resolver = CacheKeyResolver(tmp_path, env=env)
        result = resolver.resolve("node-{{ env.NODE_VERSION }}")
        assert result == "node-18"

    def test_resolve_combined(self, tmp_path: Path) -> None:
        """Resolve key with hash and env combined."""
        # Create a file to hash
        test_file = tmp_path / "package-lock.json"
        test_content = b'{"name": "test"}'
        test_file.write_bytes(test_content)

        env = {"NODE_VERSION": "18"}
        resolver = CacheKeyResolver(tmp_path, env=env)
        result = resolver.resolve(
            "npm-{{ hash('package-lock.json') }}-{{ env.NODE_VERSION }}"
        )

        expected_hash = hashlib.sha256(test_content).hexdigest()[:16]
        assert result == f"npm-{expected_hash}-18"

    def test_resolve_missing_file(self, tmp_path: Path) -> None:
        """Resolve key with missing file returns empty hash."""
        resolver = CacheKeyResolver(tmp_path)
        result = resolver.resolve("npm-{{ hash('missing.json') }}")
        assert result == "npm-"

    def test_resolve_missing_env(self, tmp_path: Path) -> None:
        """Resolve key with missing env var returns empty string."""
        resolver = CacheKeyResolver(tmp_path, env={})
        result = resolver.resolve("node-{{ env.MISSING_VAR }}")
        assert result == "node-"


class TestLocalFilesystemBackend:
    """Test local filesystem cache backend."""

    def test_exists_nonexistent(self, tmp_path: Path) -> None:
        """Check non-existent cache entry."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        assert not backend.exists("nonexistent-key")

    def test_put_and_get(self, tmp_path: Path) -> None:
        """Save and retrieve cache entry."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        working_dir = tmp_path / "workspace"
        working_dir.mkdir()

        # Create files to cache
        (working_dir / "file1.txt").write_text("content1")
        (working_dir / "dir").mkdir()
        (working_dir / "dir" / "file2.txt").write_text("content2")

        # Save to cache
        entry = backend.put(
            "test-key",
            [Path("file1.txt"), Path("dir/file2.txt")],
            working_dir,
        )

        assert entry.key == "test-key"
        assert entry.size > 0
        assert backend.exists("test-key")

        # Restore to new directory
        restore_dir = tmp_path / "restore"
        restore_dir.mkdir()
        success = backend.get("test-key", restore_dir)

        assert success
        assert (restore_dir / "file1.txt").read_text() == "content1"
        assert (restore_dir / "dir" / "file2.txt").read_text() == "content2"

    def test_put_missing_paths(self, tmp_path: Path) -> None:
        """Save with missing paths still creates entry for existing files."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        working_dir = tmp_path / "workspace"
        working_dir.mkdir()

        # Create only one file
        (working_dir / "exists.txt").write_text("content")

        # Try to cache existing and non-existing
        entry = backend.put(
            "test-key",
            [Path("exists.txt"), Path("missing.txt")],
            working_dir,
        )

        assert entry.key == "test-key"
        assert backend.exists("test-key")

    def test_delete(self, tmp_path: Path) -> None:
        """Delete cache entry."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        working_dir = tmp_path / "workspace"
        working_dir.mkdir()

        (working_dir / "file.txt").write_text("content")
        backend.put("test-key", [Path("file.txt")], working_dir)

        assert backend.exists("test-key")
        assert backend.delete("test-key")
        assert not backend.exists("test-key")

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        """Delete non-existent cache entry returns False."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        assert not backend.delete("nonexistent")

    def test_list_entries(self, tmp_path: Path) -> None:
        """List cache entries."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        working_dir = tmp_path / "workspace"
        working_dir.mkdir()

        # Create multiple entries
        (working_dir / "file1.txt").write_text("content1")
        (working_dir / "file2.txt").write_text("content2")

        backend.put("key1", [Path("file1.txt")], working_dir)
        backend.put("key2", [Path("file2.txt")], working_dir)

        entries = backend.list_entries()
        assert len(entries) == 2
        keys = [e.key for e in entries]
        assert "key1" in keys
        assert "key2" in keys

    def test_clear(self, tmp_path: Path) -> None:
        """Clear all cache entries."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        working_dir = tmp_path / "workspace"
        working_dir.mkdir()

        (working_dir / "file.txt").write_text("content")
        backend.put("key1", [Path("file.txt")], working_dir)
        backend.put("key2", [Path("file.txt")], working_dir)

        count = backend.clear()
        assert count == 2
        assert len(backend.list_entries()) == 0


class TestCacheManager:
    """Test CacheManager."""

    def test_from_config_local(self, tmp_path: Path) -> None:
        """Create manager from local config."""
        config = CacheConfig(backend="local", local_path=tmp_path / "cache")
        manager = CacheManager.from_config(config, working_dir=tmp_path)

        assert manager.backend is not None
        assert isinstance(manager.backend, LocalFilesystemBackend)

    def test_resolve_key(self, tmp_path: Path) -> None:
        """Resolve cache key through manager."""
        manager = CacheManager(working_dir=tmp_path)
        result = manager.resolve_key("static-key")
        assert result == "static-key"

    def test_restore_and_save(self, tmp_path: Path) -> None:
        """Restore and save cache through manager."""
        manager = CacheManager(working_dir=tmp_path)

        # Create files
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.json").write_text("{}")

        # Save
        saved, key, entry = manager.save("test-key", ["node_modules"])
        assert saved
        assert entry is not None

        # Remove files
        import shutil
        shutil.rmtree(tmp_path / "node_modules")

        # Restore
        restored, rkey = manager.restore("test-key", ["node_modules"])
        assert restored
        assert (tmp_path / "node_modules" / "package.json").exists()

    def test_save_no_existing_paths(self, tmp_path: Path) -> None:
        """Save with no existing paths fails gracefully."""
        manager = CacheManager(working_dir=tmp_path)

        saved, key, entry = manager.save("test-key", ["nonexistent"])
        assert not saved
        assert entry is None


class TestCacheModels:
    """Test cache-related models."""

    def test_cache_action_enum(self) -> None:
        """Test CacheAction enum values."""
        assert CacheAction.RESTORE == "restore"
        assert CacheAction.SAVE == "save"
        assert CacheAction.RESTORE_AND_SAVE == "restore-and-save"

    def test_step_cache_config_defaults(self) -> None:
        """Test StepCacheConfig defaults."""
        config = StepCacheConfig()
        assert config.paths == []
        assert config.key == ""
        assert config.action == CacheAction.RESTORE_AND_SAVE

    def test_cache_config_defaults(self) -> None:
        """Test CacheConfig defaults."""
        config = CacheConfig()
        assert config.backend == "local"
        assert config.s3_prefix == "relay-cache/"

    def test_cache_config_s3(self) -> None:
        """Test S3 cache config."""
        config = CacheConfig(
            backend="s3",
            s3_bucket="my-bucket",
            s3_endpoint="http://localhost:9000",
            s3_region="us-west-2",
            s3_prefix="my-cache/",
        )
        assert config.backend == "s3"
        assert config.s3_bucket == "my-bucket"
        assert config.s3_endpoint == "http://localhost:9000"


class TestCacheIntegration:
    """Integration tests for caching."""

    def test_full_cache_workflow(self, tmp_path: Path) -> None:
        """Test complete cache workflow."""
        cache_dir = tmp_path / "cache"
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create CacheManager
        backend = LocalFilesystemBackend(cache_dir=cache_dir)
        manager = CacheManager(backend=backend, working_dir=workspace)

        # Create some files
        (workspace / "dist").mkdir()
        (workspace / "dist" / "app.js").write_text("console.log('hello')")
        (workspace / "dist" / "app.css").write_text("body { color: red }")

        # Save cache
        saved, key, entry = manager.save("build-cache", ["dist"])
        assert saved
        assert entry is not None

        # Remove files
        import shutil
        shutil.rmtree(workspace / "dist")

        # Restore cache
        restored, rkey = manager.restore("build-cache", ["dist"])
        assert restored
        assert (workspace / "dist" / "app.js").exists()
        assert (workspace / "dist" / "app.css").exists()

        # List entries
        entries = manager.list_entries()
        assert len(entries) == 1
        assert entries[0].key == "build-cache"

        # Clear
        count = manager.clear()
        assert count == 1


class TestCacheKeySanitization:
    """Test key sanitization for filesystem compatibility."""

    def test_special_characters_sanitized(self, tmp_path: Path) -> None:
        """Special characters in keys are sanitized."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        (workspace / "file.txt").write_text("content")

        # Key with special characters
        key = "npm:package@1.0.0 (test)"
        backend.put(key, [Path("file.txt")], workspace)

        # Should still be retrievable
        assert backend.exists(key)

    def test_slashes_sanitized(self, tmp_path: Path) -> None:
        """Slashes in keys are sanitized."""
        backend = LocalFilesystemBackend(cache_dir=tmp_path)
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        (workspace / "file.txt").write_text("content")

        # Key with path-like structure
        key = "path/to/cache/key"
        backend.put(key, [Path("file.txt")], workspace)

        assert backend.exists(key)
