"""Artifact caching system for Relay.

Supports local filesystem and S3-compatible storage backends.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from relay.models import CacheConfig


class CacheAction(str, Enum):
    """Cache action types."""

    RESTORE = "restore"
    SAVE = "save"
    RESTORE_AND_SAVE = "restore-and-save"


@dataclass
class CacheEntry:
    """Represents a cached artifact entry."""

    key: str
    path: str  # Storage path/key
    size: int
    created_at: float
    metadata: dict[str, str]


class CacheBackend(ABC):
    """Abstract base class for cache storage backends."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a cache entry exists."""
        pass

    @abstractmethod
    def get(self, key: str, dest_dir: Path) -> bool:
        """Restore cache entry to destination directory."""
        pass

    @abstractmethod
    def put(self, key: str, source_paths: list[Path], working_dir: Path) -> CacheEntry:
        """Save paths to cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        pass

    @abstractmethod
    def list_entries(self) -> list[CacheEntry]:
        """List all cache entries."""
        pass

    @abstractmethod
    def clear(self) -> int:
        """Clear all cache entries. Returns count of deleted entries."""
        pass


class LocalFilesystemBackend(CacheBackend):
    """Local filesystem cache backend."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".relay" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"

    def _get_archive_path(self, key: str) -> Path:
        """Get the archive path for a cache key."""
        # Sanitize key for filesystem
        safe_key = re.sub(r'[^a-zA-Z0-9_-]', '_', key)
        return self.cache_dir / f"{safe_key}.tar.gz"

    def _load_metadata(self) -> dict[str, dict]:
        """Load cache metadata."""
        if self.metadata_file.exists():
            return json.loads(self.metadata_file.read_text())
        return {}

    def _save_metadata(self, metadata: dict[str, dict]) -> None:
        """Save cache metadata."""
        self.metadata_file.write_text(json.dumps(metadata, indent=2))

    def exists(self, key: str) -> bool:
        """Check if cache entry exists."""
        archive_path = self._get_archive_path(key)
        return archive_path.exists()

    def get(self, key: str, dest_dir: Path) -> bool:
        """Restore cache entry to destination."""
        archive_path = self._get_archive_path(key)
        if not archive_path.exists():
            return False

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # Use filter='data' for security (Python 3.12+)
                import sys
                if sys.version_info >= (3, 12):
                    tar.extractall(dest_dir, filter='data')
                else:
                    tar.extractall(dest_dir)
            return True
        except Exception:
            return False

    def put(self, key: str, source_paths: list[Path], working_dir: Path) -> CacheEntry:
        """Save paths to cache."""
        archive_path = self._get_archive_path(key)

        # Create tar archive
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in source_paths:
                full_path = working_dir / path
                if full_path.exists():
                    # Store relative to working directory
                    arcname = str(path)
                    tar.add(full_path, arcname=arcname)

        # Get size
        size = archive_path.stat().st_size
        created_at = archive_path.stat().st_mtime

        # Update metadata
        metadata = self._load_metadata()
        entry_metadata = {
            "paths": [str(p) for p in source_paths],
            "working_dir": str(working_dir),
        }
        metadata[key] = entry_metadata
        self._save_metadata(metadata)

        return CacheEntry(
            key=key,
            path=str(archive_path),
            size=size,
            created_at=created_at,
            metadata=entry_metadata,
        )

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        archive_path = self._get_archive_path(key)
        if archive_path.exists():
            archive_path.unlink()

            # Update metadata
            metadata = self._load_metadata()
            if key in metadata:
                del metadata[key]
                self._save_metadata(metadata)
            return True
        return False

    def list_entries(self) -> list[CacheEntry]:
        """List all cache entries."""
        metadata = self._load_metadata()
        entries = []

        for key, meta in metadata.items():
            archive_path = self._get_archive_path(key)
            if archive_path.exists():
                stat = archive_path.stat()
                entries.append(
                    CacheEntry(
                        key=key,
                        path=str(archive_path),
                        size=stat.st_size,
                        created_at=stat.st_mtime,
                        metadata=meta,
                    )
                )

        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def clear(self) -> int:
        """Clear all cache entries."""
        entries = self.list_entries()
        count = 0

        for entry in entries:
            archive_path = Path(entry.path)
            if archive_path.exists():
                archive_path.unlink()
                count += 1

        # Clear metadata
        if self.metadata_file.exists():
            self.metadata_file.unlink()

        return count


class S3Backend(CacheBackend):
    """S3-compatible cache backend (MinIO, AWS S3, etc.)."""

    def __init__(
        self,
        bucket: str,
        endpoint: str | None = None,
        region: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        prefix: str = "relay-cache/",
    ) -> None:
        self.bucket = bucket
        self.endpoint = endpoint
        self.region = region or "us-east-1"
        self.access_key = access_key or os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.prefix = prefix

        # Try to import boto3
        try:
            import boto3
            from botocore.config import Config

            self._boto3 = boto3
            self._Config = Config
        except ImportError:
            raise ImportError(
                "S3 backend requires 'boto3'. Install with: pip install boto3"
            )

        # Initialize S3 client
        session = boto3.session.Session()
        config = Config(region_name=self.region)

        kwargs = {
            "config": config,
        }

        if self.endpoint:
            kwargs["endpoint_url"] = self.endpoint
        if self.access_key and self.secret_key:
            kwargs["aws_access_key_id"] = self.access_key
            kwargs["aws_secret_access_key"] = self.secret_key

        self.s3 = session.client("s3", **kwargs)

    def _get_object_key(self, key: str) -> str:
        """Get the S3 object key for a cache key."""
        safe_key = re.sub(r'[^a-zA-Z0-9_-]', '_', key)
        return f"{self.prefix}{safe_key}.tar.gz"

    def _get_metadata_key(self) -> str:
        """Get the S3 metadata object key."""
        return f"{self.prefix}metadata.json"

    def _load_metadata(self) -> dict[str, dict]:
        """Load cache metadata from S3."""
        try:
            response = self.s3.get_object(
                Bucket=self.bucket, Key=self._get_metadata_key()
            )
            return json.loads(response["Body"].read().decode("utf-8"))
        except Exception:
            return {}

    def _save_metadata(self, metadata: dict[str, dict]) -> None:
        """Save cache metadata to S3."""
        self.s3.put_object(
            Bucket=self.bucket,
            Key=self._get_metadata_key(),
            Body=json.dumps(metadata, indent=2).encode("utf-8"),
            ContentType="application/json",
        )

    def exists(self, key: str) -> bool:
        """Check if cache entry exists."""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=self._get_object_key(key))
            return True
        except Exception:
            return False

    def get(self, key: str, dest_dir: Path) -> bool:
        """Restore cache entry to destination."""
        object_key = self._get_object_key(key)

        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp:
                self.s3.download_fileobj(self.bucket, object_key, tmp)
                tmp_path = tmp.name

            # Extract
            with tarfile.open(tmp_path, "r:gz") as tar:
                import sys
                if sys.version_info >= (3, 12):
                    tar.extractall(dest_dir, filter='data')
                else:
                    tar.extractall(dest_dir)

            # Cleanup
            os.unlink(tmp_path)
            return True
        except Exception:
            return False

    def put(self, key: str, source_paths: list[Path], working_dir: Path) -> CacheEntry:
        """Save paths to cache."""
        object_key = self._get_object_key(key)

        # Create tar archive in temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp:
            tmp_path = tmp.name
            with tarfile.open(tmp_path, "w:gz") as tar:
                for path in source_paths:
                    full_path = working_dir / path
                    if full_path.exists():
                        arcname = str(path)
                        tar.add(full_path, arcname=arcname)

        # Upload to S3
        self.s3.upload_file(tmp_path, self.bucket, object_key)

        # Get file info
        size = os.path.getsize(tmp_path)
        created_at = os.path.getmtime(tmp_path)

        # Cleanup
        os.unlink(tmp_path)

        # Update metadata
        metadata = self._load_metadata()
        entry_metadata = {
            "paths": [str(p) for p in source_paths],
            "working_dir": str(working_dir),
        }
        metadata[key] = entry_metadata
        self._save_metadata(metadata)

        return CacheEntry(
            key=key,
            path=f"s3://{self.bucket}/{object_key}",
            size=size,
            created_at=created_at,
            metadata=entry_metadata,
        )

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        object_key = self._get_object_key(key)

        try:
            self.s3.delete_object(Bucket=self.bucket, Key=object_key)

            # Update metadata
            metadata = self._load_metadata()
            if key in metadata:
                del metadata[key]
                self._save_metadata(metadata)
            return True
        except Exception:
            return False

    def list_entries(self) -> list[CacheEntry]:
        """List all cache entries."""
        metadata = self._load_metadata()
        entries = []

        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket, Prefix=self.prefix
            )

            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key == self._get_metadata_key():
                    continue

                # Extract cache key from object key
                cache_key = key[len(self.prefix) :].replace(".tar.gz", "")

                # Find metadata
                entry_metadata = metadata.get(cache_key, {})

                entries.append(
                    CacheEntry(
                        key=cache_key,
                        path=f"s3://{self.bucket}/{key}",
                        size=obj["Size"],
                        created_at=obj["LastModified"].timestamp(),
                        metadata=entry_metadata,
                    )
                )
        except Exception:
            pass

        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def clear(self) -> int:
        """Clear all cache entries."""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket, Prefix=self.prefix
            )

            keys = [obj["Key"] for obj in response.get("Contents", [])]

            if keys:
                self.s3.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": [{"Key": k} for k in keys]},
                )

            return len(keys)
        except Exception:
            return 0


class CacheKeyResolver:
    """Resolves cache keys with template variables."""

    def __init__(self, working_dir: Path, env: dict[str, str] | None = None) -> None:
        self.working_dir = working_dir
        self.env = env or dict(os.environ)

    def resolve(self, key_template: str) -> str:
        """Resolve a cache key template.

        Supports:
        - Static strings
        - {{ hash('path/to/file') }} - SHA256 hash of file content
        - {{ env.VAR_NAME }} - Environment variable
        - Combinations: npm-{{ hash('package-lock.json') }}-{{ env.NODE_VERSION }}
        """
        result = key_template

        # Replace hash() functions
        hash_pattern = r"\{\{\s*hash\(['\"](.+?)['\"]\)\s*\}\}"
        for match in re.finditer(hash_pattern, result):
            file_path = match.group(1)
            hash_value = self._compute_hash(file_path)
            result = result.replace(match.group(0), hash_value)

        # Replace env.VAR references
        env_pattern = r"\{\{\s*env\.(\w+)\s*\}\}"
        for match in re.finditer(env_pattern, result):
            var_name = match.group(1)
            env_value = self.env.get(var_name, "")
            result = result.replace(match.group(0), env_value)

        return result

    def _compute_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file content."""
        full_path = self.working_dir / file_path
        if not full_path.exists():
            return ""

        try:
            content = full_path.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return ""


class CacheManager:
    """Manages artifact caching for pipeline steps."""

    def __init__(
        self,
        backend: CacheBackend | None = None,
        working_dir: Path | None = None,
    ) -> None:
        self.backend = backend or LocalFilesystemBackend()
        self.working_dir = working_dir or Path.cwd()
        self._resolver = CacheKeyResolver(self.working_dir)

    @classmethod
    def from_config(
        cls,
        cache_config: CacheConfig | None,
        working_dir: Path | None = None,
    ) -> CacheManager:
        """Create a CacheManager from configuration."""
        if cache_config is None:
            return cls(working_dir=working_dir)

        backend: CacheBackend

        if cache_config.backend == "s3":
            backend = S3Backend(
                bucket=cache_config.s3_bucket or "relay-cache",
                endpoint=cache_config.s3_endpoint,
                region=cache_config.s3_region,
                access_key=cache_config.s3_access_key,
                secret_key=cache_config.s3_secret_key,
                prefix=cache_config.s3_prefix or "relay-cache/",
            )
        else:
            backend = LocalFilesystemBackend(
                cache_dir=cache_config.local_path,
            )

        return cls(backend=backend, working_dir=working_dir)

    def resolve_key(self, key_template: str) -> str:
        """Resolve a cache key template."""
        return self._resolver.resolve(key_template)

    def restore(
        self,
        key_template: str,
        paths: list[str],
    ) -> tuple[bool, str]:
        """Restore cache if it exists.

        Returns (success, resolved_key)
        """
        key = self.resolve_key(key_template)

        if not self.backend.exists(key):
            return False, key

        success = self.backend.get(key, self.working_dir)
        return success, key

    def save(
        self,
        key_template: str,
        paths: list[str],
    ) -> tuple[bool, str, CacheEntry | None]:
        """Save paths to cache.

        Returns (success, resolved_key, entry)
        """
        key = self.resolve_key(key_template)

        path_objs = [Path(p) for p in paths]

        # Check if any paths exist
        existing = [p for p in path_objs if (self.working_dir / p).exists()]
        if not existing:
            return False, key, None

        entry = self.backend.put(key, existing, self.working_dir)
        return True, key, entry

    def list_entries(self) -> list[CacheEntry]:
        """List all cache entries."""
        return self.backend.list_entries()

    def clear(self) -> int:
        """Clear all cache entries."""
        return self.backend.clear()

    def delete(self, key: str) -> bool:
        """Delete a specific cache entry."""
        return self.backend.delete(key)
