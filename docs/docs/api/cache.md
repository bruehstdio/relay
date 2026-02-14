# Cache API

The `relay.cache` module provides the caching system for artifacts.

## Module Reference

::: relay.cache
    options:
      show_source: true
      show_root_heading: true

## CacheManager

Main class for managing cache operations.

```python
from relay.cache import CacheManager
from relay.models import CacheConfig

# Create from config
config = CacheConfig(backend="local", local_path=Path("~/.cache"))
manager = CacheManager.from_config(config, working_dir=Path.cwd())

# Or create directly
manager = CacheManager(working_dir=Path.cwd())
```

### Constructor

```python
CacheManager(
    backend: CacheBackend | None = None,
    working_dir: Path | None = None,
)
```

### Class Methods

#### from_config

```python
@classmethod
def from_config(
    cls,
    cache_config: CacheConfig | None,
    working_dir: Path | None = None,
) -> CacheManager
```

Create a CacheManager from configuration.

### Methods

#### resolve_key

```python
def resolve_key(self, key_template: str) -> str
```

Resolve a cache key template with variables.

```python
key = manager.resolve_key("deps-{{ hash('package-lock.json') }}")
# Result: "deps-a1b2c3d4..."
```

#### restore

```python
def restore(
    self,
    key_template: str,
    paths: list[str],
) -> tuple[bool, str]
```

Restore cache if it exists.

**Returns:** `(success, resolved_key)`

```python
success, key = manager.restore(
    "deps-{{ hash('package-lock.json') }}",
    ["node_modules"]
)
if success:
    print(f"Restored from cache: {key}")
```

#### save

```python
def save(
    self,
    key_template: str,
    paths: list[str],
) -> tuple[bool, str, CacheEntry | None]
```

Save paths to cache.

**Returns:** `(success, resolved_key, entry)`

```python
success, key, entry = manager.save(
    "deps-{{ hash('package-lock.json') }}",
    ["node_modules", "package-lock.json"]
)
if success:
    print(f"Saved to cache: {key} ({entry.size} bytes)")
```

#### list_entries

```python
def list_entries(self) -> list[CacheEntry]
```

List all cache entries.

```python
for entry in manager.list_entries():
    print(f"{entry.key}: {entry.size} bytes")
```

#### clear

```python
def clear(self) -> int
```

Clear all cache entries.

**Returns:** Number of entries deleted.

```python
count = manager.clear()
print(f"Cleared {count} cache entries")
```

#### delete

```python
def delete(self, key: str) -> bool
```

Delete a specific cache entry.

```python
if manager.delete("my-cache-key"):
    print("Cache entry deleted")
```

## CacheBackends

### LocalFilesystemBackend

```python
from relay.cache import LocalFilesystemBackend

backend = LocalFilesystemBackend(cache_dir=Path("~/.relay/cache"))
```

### S3Backend

```python
from relay.cache import S3Backend

backend = S3Backend(
    bucket="my-bucket",
    endpoint="https://s3.amazonaws.com",
    region="us-east-1",
    access_key="AKIA...",
    secret_key="...",
    prefix="relay-cache/",
)
```

**Requirements:**

```bash
pip install boto3
```

## CacheEntry

Represents a cached artifact.

```python
@dataclass
class CacheEntry:
    key: str
    path: str
    size: int
    created_at: float
    metadata: dict[str, str]
```

## CacheKeyResolver

Resolve cache key templates.

```python
from relay.cache import CacheKeyResolver

resolver = CacheKeyResolver(working_dir=Path.cwd())
key = resolver.resolve("deps-{{ hash('package.json') }}-{{ env.NODE_VERSION }}")
```

### Supported Functions

| Function | Description |
|----------|-------------|
| `{{ hash('path') }}` | SHA256 hash of file |
| `{{ env.VAR }}` | Environment variable |

## Complete Example

```python
from pathlib import Path
from relay.cache import CacheManager
from relay.models import CacheConfig, StepCacheConfig

# Setup
working_dir = Path.cwd()
config = CacheConfig(backend="local")
manager = CacheManager.from_config(config, working_dir)

# Define cache configuration
step_cache = StepCacheConfig(
    paths=["node_modules", "package-lock.json"],
    key="npm-{{ hash('package-lock.json') }}-{{ env.NODE_VERSION }}",
    action="restore-and-save"
)

# Restore before step
success, key = manager.restore(step_cache.key, step_cache.paths)
if success:
    print(f"Cache hit: {key}")
else:
    print("Cache miss, running step...")
    # ... run step ...
    
    # Save after step
    success, key, entry = manager.save(step_cache.key, step_cache.paths)
    if success:
        print(f"Cached: {key}")

# List all entries
print("\nAll cache entries:")
for entry in manager.list_entries():
    print(f"  {entry.key}: {entry.size} bytes")
```
