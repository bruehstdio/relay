# Deployment Example

A deployment pipeline with conditional steps based on test results and environment.

## Pipeline

```yaml
name: "deployment-pipeline"
description: "Test, build, and deploy with conditional steps"

steps:
  - name: lint
    agent: opencode
    prompt: |
      Run linting checks on the codebase:
      - Check code style
      - Run static analysis
      - Verify type hints (if applicable)
      
      Report any issues found. Continue even if issues exist
      (they will be addressed later).
    continue_on_error: true
    output: lint-report.txt

  - name: test
    agent: claude-code
    prompt: |
      Run the test suite:
      - Unit tests
      - Integration tests (if applicable)
      - Check test coverage
      
      Report test results and coverage metrics.
      Fail if any tests fail.
    output: test-report.txt

  - name: security-scan
    agent: opencode
    prompt: |
      Run security checks:
      - Check for known vulnerabilities in dependencies
      - Scan for secrets/credentials in code
      - Check for security anti-patterns
      
      This is informational for now.
    continue_on_error: true
    output: security-report.txt

  - name: build
    agent: claude-code
    prompt: |
      Build the project:
      - Compile/bundle code
      - Optimize assets
      - Generate build artifacts
      
      Ensure the build succeeds before proceeding.
    needs:
      - test
    if: "steps.test.success"
    output: build.log

  - name: deploy-staging
    agent: opencode
    prompt: |
      Deploy to the staging environment:
      - Upload build artifacts
      - Run database migrations (if any)
      - Verify deployment health
      - Run smoke tests
      
      Report deployment status.
    needs:
      - build
    if: "steps.build.success and env.DEPLOY_ENV in ('staging', 'all')"
    output: staging-deploy.log

  - name: staging-tests
    agent: claude-code
    prompt: |
      Run tests against staging:
      - API health checks
      - End-to-end tests
      - Verify critical user flows
      
      Report any staging issues.
    needs:
      - deploy-staging
    if: "steps.deploy-staging.success"
    output: staging-tests.log

  - name: deploy-production
    agent: claude-code
    prompt: |
      Deploy to production environment:
      - Upload build artifacts
      - Run database migrations (if any)
      - Update load balancer/configs
      - Verify deployment health
      
      ⚠️ This is production - be careful!
    needs:
      - staging-tests
    if: "steps.staging-tests.success and env.DEPLOY_ENV in ('production', 'all')"
    output: production-deploy.log

  - name: notify-success
    agent: opencode
    prompt: |
      Create a deployment success notification:
      - Summarize what was deployed
      - List any new features or fixes
      - Include relevant commit hashes/versions
      - Note any manual verification steps
      
      Format as a brief message suitable for Slack/email.
    if: "steps.deploy-production.success or steps.deploy-staging.success"
    output: success-notification.txt

  - name: notify-failure
    agent: claude-code
    prompt: |
      Create a deployment failure notification:
      - Identify which step failed
      - Summarize the error
      - Suggest rollback steps if applicable
      - List who to contact for help
      
      Format as an urgent alert.
    if: "steps.test.failed or steps.build.failed or steps.deploy-production.failed"
    output: failure-notification.txt
```

## How It Works

1. **Quality Checks** — Linting, tests, and security scan run in sequence
   - `lint` and `security-scan` use `continue_on_error` to not block deployment

2. **Build** — Only runs if tests pass
   - Uses `needs` to ensure test step completes
   - Uses `if` condition to check test results

3. **Staging Deployment** — Deploys to staging first
   - Only deploys if build succeeded
   - Can be skipped with `DEPLOY_ENV=production`

4. **Staging Tests** — Validates staging deployment
   - Runs smoke tests and health checks

5. **Production Deployment** — Deploys to production
   - Only after staging tests pass
   - Can be skipped with `DEPLOY_ENV=staging`

6. **Notifications** — Sends appropriate notifications
   - Success notification on successful deploy
   - Failure notification if anything goes wrong

## Usage

```bash
# Deploy to staging only
DEPLOY_ENV=staging relay run --config deploy.yml

# Deploy to production (includes staging)
DEPLOY_ENV=all relay run --config deploy.yml

# Skip tests (not recommended)
SKIP_TESTS=true DEPLOY_ENV=production relay run --config deploy.yml
```

## Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `DEPLOY_ENV` | `staging`, `production`, `all` | Target environment |
| `SKIP_TESTS` | `true`, `false` | Skip test step (dangerous) |

## Customization

### Add Rollback Step

```yaml
- name: rollback
  agent: claude-code
  prompt: |
    Execute rollback procedure:
    - Revert to previous version
    - Restore database if needed
    - Verify rollback success
  if: "steps.deploy-production.failed"
```

### Add Approval Gate

```yaml
- name: approval-check
  agent: opencode
  prompt: |
    Check if deployment is approved:
    - Verify approval status in system
    - Check if it's during allowed hours
    - Confirm no deployment freezes
  if: "env.REQUIRE_APPROVAL == 'true'"
  output: approval-status.txt
```

## Expected Output

```
╭────── Pipeline: deployment-pipeline ──────╮
│ Test, build, and deploy with conditional steps│
╰───────────────────────────────────────────────╯

✓ Step 1: lint (2341ms)
✓ Step 2: test (8934ms)
✓ Step 3: security-scan (1234ms)
✓ Step 4: build (5678ms)
✓ Step 5: deploy-staging (3456ms)
✓ Step 6: staging-tests (4567ms)
✓ Step 7: deploy-production (5678ms)
✓ Step 8: notify-success (890ms)

Pipeline complete: 8/8 steps succeeded
Total time: 32778ms
```
