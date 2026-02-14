# Caching

Relay includes a caching system for persisting and reusing artifacts between pipeline runs.

## Overview

The caching system allows you to:

- Save files produced by pipeline steps
- Restore files in subsequent runs
- Share caches between team members (with S3 backend)
- Speed up pipelines by avoiding redundant work

## Configuration

### Local Cache (Default)

```yaml
# relay.yml
cache:
  backend: local
  local_path: ~/.relay/cache  # Optional, uses default if not set
```

### S3 Cache

```yaml
# relay.yml
cache:
  backend: s3
  s3_bucket: my-relay-cache
  s3_endpoint: https://s3.amazonaws.com  # Optional (for MinIO)
  s3_region: us-east-1
  s3_access_key: ${AWS_ACCESS_KEY_ID}
  s3_secret_key: ${AWS_SECRET_ACCESS_KEY}
  s3_prefix: relay-cache/
```

## Step-Level Caching

Configure caching for individual steps:

```yaml
steps:
  - name: install-dependencies
    agent: opencode
    prompt: "Install npm dependencies"
    cache:
      paths:
        - node_modules
        - package-lock.json
      key: npm-{{ hash('package-lock.json') }}-{{ env.NODE_VERSION }}
      action: restore-and-save  # restore, save, or restore-and-save
```

### Cache Actions

| Action | Description |
|--------|-------------|
| `restore` | Only restore from cache |
| `save` | Only save to cache |
| `restore-and-save` | Restore before step, save after (default) |

## Cache Key Templates

Cache keys support dynamic values:

```yaml
cache:
  key: deps-{{ hash('package-lock.json') }}-{{ env.NODE_VERSION }}
```

### Template Functions

| Function | Description | Example |
|----------|-------------|---------|
| `hash('path')` | SHA256 hash of file content | `{{ hash('package-lock.json') }}` |
| `env.VAR` | Environment variable | `{{ env.NODE_VERSION }}` |

### Example Keys

```yaml
# Simple static key
cache:
  key: my-static-key

# File hash
cache:
  key: deps-{{ hash('package-lock.json') }}

# Environment variable
cache:
  key: build-{{ env.GIT_COMMIT }}

# Combined
cache:
  key: v1-{{ hash('package-lock.json') }}-{{ env.NODE_VERSION }}-{{ env.OS }}
```

## CLI Commands

### List Cached Artifacts

```bash
relay cache list
```

Output:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Key                        ┃ Size    ┃ Created         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ deps-a1b2c3d4-node18       │ 45.2 MB │ 2024-01-15 10:30│
│ build-e5f6g7h8-main        │ 12.1 MB │ 2024-01-15 09:15│
└────────────────────────────┴─────────┴─────────────────┘
```

### Clear Cache

```bash
# Interactive confirmation
relay cache clear

# Skip confirmation
relay cache clear --yes
```

## Pipeline Cache Configuration

Override global cache settings per pipeline:

```yaml
name: "my-pipeline"
description: "Pipeline with custom cache"

cache:
  backend: s3
  s3_bucket: project-specific-bucket

steps:
  - name: build
    agent: opencode
    prompt: "Build the project"
    cache:
      paths:
        - dist
        - .cache
      key: build-{{ hash('src/**') }}
```

## Best Practices

### 1. Version Your Cache Keys

```yaml
# Good - version allows cache invalidation
cache:
  key: v1-npm-{{ hash('package-lock.json') }}

# Bad - can't easily invalidate
cache:
  key: npm-{{ hash('package-lock.json') }}
```

### 2. Include All Relevant Files in Hash

```yaml
# Good - captures all dependency changes
cache:
  key: deps-{{ hash('package.json') }}-{{ hash('package-lock.json') }}

# Bad - might miss package.json changes
cache:
  key: deps-{{ hash('package-lock.json') }}
```

### 3. Use Environment Variables for Per-Environment Caches

```yaml
cache:
  key: build-{{ env.NODE_ENV }}-{{ hash('src/**') }}
```

### 4. Cache Large Dependencies

```yaml
steps:
  - name: install
    agent: opencode
    prompt: "Install Python dependencies"
    cache:
      paths:
        - .venv
        - requirements.txt
      key: v1-venv-{{ hash('requirements.txt') }}-{{ env.PYTHON_VERSION }}
```

## Cache Backends

### Local Filesystem

Stores cache as compressed tar archives in a local directory.

**Pros:**
- Simple, no external dependencies
- Fast for local development

**Cons:**
- Not shared between machines
- Limited to local disk space

### S3-Compatible

Stores cache in S3-compatible storage (AWS S3, MinIO, etc.).

**Pros:**
- Shared between team members
- Virtually unlimited storage
- Works in CI/CD environments

**Cons:**
- Requires network access
- S3 credentials needed

**Requirements:**

```bash
pip install boto3
```
