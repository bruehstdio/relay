# GitHub Integration Example

Automate GitHub workflows with Relay — from issue analysis to pull request creation.

## Overview

This example shows how to integrate Relay with GitHub for:
- Issue analysis and triage
- Automated code review
- Pull request creation
- Release note generation

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- `GITHUB_TOKEN` environment variable set (or `gh` logged in)

## Pipeline: Issue to PR

Automatically analyze a GitHub issue and create a pull request.

```yaml
name: "github-issue-to-pr"
description: "Analyze GitHub issue and create implementation PR"

steps:
  # Step 1: Fetch and analyze issue
  - name: analyze-issue
    agent: claude-code
    prompt: |
      Fetch and analyze GitHub issue #${ISSUE_NUMBER}.
      
      Run: gh issue view ${ISSUE_NUMBER} --json number,title,body,labels
      
      Based on the issue:
      1. Summarize the requirements
      2. Identify affected code areas
      3. Propose implementation approach
      4. Estimate complexity
      
      Write analysis to issue-analysis.md.
    output: issue-analysis.md

  # Step 2: Create implementation plan
  - name: plan-implementation
    agent: opencode
    prompt: |
      Create a detailed implementation plan based on issue-analysis.md.
      
      Include:
      - Files to modify/create
      - Functions/classes to implement
      - Test cases needed
      - Potential edge cases
      
      Write plan to implementation-plan.md.
    input: issue-analysis.md
    output: implementation-plan.md

  # Step 3: Create feature branch
  - name: create-branch
    agent: opencode
    prompt: |
      Create a new Git branch for this feature.
      
      Branch name: feature/issue-${ISSUE_NUMBER}-$(date +%s)
      
      Run:
      1. git checkout -b feature/issue-${ISSUE_NUMBER}
      2. Push branch to origin
      
      Document the branch name in branch-info.txt.
    output: branch-info.txt

  # Step 4: Implement changes
  - name: implement
    agent: aider
    prompt: |
      Implement the changes according to implementation-plan.md.
      
      Requirements:
      - Follow existing code style
      - Add/update tests
      - Update documentation if needed
      - Ensure code compiles/passes basic checks
    input: implementation-plan.md
    output: implementation-summary.md

  # Step 5: Run tests
  - name: run-tests
    agent: opencode
    prompt: |
      Run the test suite to verify implementation.
      
      Execute:
      - Unit tests
      - Linting checks
      - Type checking (if applicable)
      
      Report results in test-results.md.
    output: test-results.md

  # Step 6: Create PR description
  - name: generate-pr-description
    agent: claude-code
    prompt: |
      Create a pull request description based on:
      - issue-analysis.md (original issue)
      - implementation-plan.md (what was planned)
      - implementation-summary.md (what was done)
      - test-results.md (verification)
      
      Include:
      - Summary of changes
      - Link to issue #${ISSUE_NUMBER}
      - Testing performed
      - Screenshots (if applicable)
      
      Write to pr-description.md.
    input: |
      issue-analysis.md
      implementation-plan.md
      implementation-summary.md
      test-results.md
    output: pr-description.md

  # Step 7: Create pull request
  - name: create-pr
    agent: opencode
    prompt: |
      Create a pull request using gh CLI.
      
      Use:
      - Branch from branch-info.txt
      - Title: "Fix #${ISSUE_NUMBER}: [Issue title]"
      - Body from pr-description.md
      - Labels from original issue (if applicable)
      
      Run: gh pr create --title "..." --body-file pr-description.md
      
      Report the PR URL in pr-url.txt.
    input: |
      branch-info.txt
      pr-description.md
    output: pr-url.txt
```

## Usage

```bash
# Set the issue number
export ISSUE_NUMBER=42

# Run the pipeline
relay run --config github-issue-to-pr.yml
```

## Pipeline: Automated Code Review

Review pull requests automatically with multiple AI agents.

```yaml
name: "github-auto-review"
description: "Automated multi-agent PR review"

steps:
  # Step 1: Fetch PR information
  - name: fetch-pr
    agent: opencode
    prompt: |
      Fetch PR #${PR_NUMBER} details.
      
      Run: gh pr view ${PR_NUMBER} --json number,title,body,author,files
      
      Also fetch the diff:
      gh pr diff ${PR_NUMBER} > pr-diff.patch
      
      Document PR info in pr-info.md.
    output: pr-info.md

  # Step 2: Multi-aspect review (parallel)
  - name: review-aspects
    parallel:
      - name: security-review
        agent: claude-code
        prompt: |
          Review pr-diff.patch for security issues:
          - SQL injection
          - XSS vulnerabilities
          - Hardcoded secrets
          - Authentication bypasses
          Write findings to security-review.md.
        input: pr-diff.patch
        output: security-review.md

      - name: performance-review
        agent: opencode
        prompt: |
          Review pr-diff.patch for performance issues:
          - N+1 queries
          - Unnecessary computations
          - Memory leaks
          - Caching opportunities
          Write findings to performance-review.md.
        input: pr-diff.patch
        output: performance-review.md

      - name: style-review
        agent: claude-code
        prompt: |
          Review pr-diff.patch for code style:
          - Consistency with codebase
          - Naming conventions
          - Documentation
          - Type hints
          Write findings to style-review.md.
        input: pr-diff.patch
        output: style-review.md

      - name: logic-review
        agent: opencode
        prompt: |
          Review pr-diff.patch for logic issues:
          - Correctness
          - Edge cases
          - Error handling
          - Test coverage
          Write findings to logic-review.md.
        input: pr-diff.patch
        output: logic-review.md
    
    parallel_strategy: concat
    output: combined-reviews.md

  # Step 3: Synthesize review
  - name: synthesize-review
    agent: claude-code
    prompt: |
      Create a comprehensive PR review from combined-reviews.md.
      
      Format as GitHub PR comment:
      ## Summary
      [Overall assessment]
      
      ## Security
      [Security findings]
      
      ## Performance
      [Performance findings]
      
      ## Style
      [Style findings]
      
      ## Logic
      [Logic findings]
      
      ## Recommendations
      [Actionable items]
      
      Write to final-review.md.
    input: combined-reviews.md
    output: final-review.md

  # Step 4: Post review comment
  - name: post-review
    agent: opencode
    prompt: |
      Post the review as a PR comment.
      
      Run: gh pr comment ${PR_NUMBER} --body-file final-review.md
      
      Also determine if we should approve/request changes:
      - Check for critical issues in final-review.md
      - If none, approve: gh pr review ${PR_NUMBER} --approve
      - If critical issues: gh pr review ${PR_NUMBER} --request-changes --body "..."
      
      Document action taken in review-action.txt.
    input: final-review.md
    output: review-action.txt
```

## Usage

```bash
export PR_NUMBER=123
relay run --config github-auto-review.yml
```

## Pipeline: Release Notes Generation

Automatically generate release notes from merged PRs.

```yaml
name: "github-release-notes"
description: "Generate release notes from merged PRs"

steps:
  # Step 1: Fetch merged PRs since last tag
  - name: fetch-changes
    agent: opencode
    prompt: |
      Get all merged PRs since the last release tag.
      
      Run:
      1. Get last tag: git describe --tags --abbrev=0
      2. List PRs: gh pr list --state merged --search "merged:>[DATE]"
      
      Save PR list to merged-prs.json.
    output: merged-prs.json

  # Step 2: Categorize changes
  - name: categorize
    agent: claude-code
    prompt: |
      Categorize merged PRs from merged-prs.json.
      
      Categories:
      - 🚀 Features
      - 🐛 Bug Fixes
      - 📝 Documentation
      - 🔧 Maintenance
      - ⚡ Performance
      - 🔒 Security
      
      Write categorized notes to categorized-changes.md.
    input: merged-prs.json
    output: categorized-changes.md

  # Step 3: Generate release notes
  - name: generate-notes
    agent: opencode
    prompt: |
      Create formatted release notes from categorized-changes.md.
      
      Include:
      - Version header
      - Summary statistics
      - Categorized changes
      - Contributors list
      - Upgrade notes (if breaking changes)
      
      Format for GitHub releases.
      Write to release-notes.md.
    input: categorized-changes.md
    output: release-notes.md

  # Step 4: Create GitHub release
  - name: create-release
    agent: opencode
    prompt: |
      Create a GitHub release with the generated notes.
      
      Run: gh release create v${VERSION} --notes-file release-notes.md
      
      Or draft release if preferred:
      gh release create v${VERSION} --draft --notes-file release-notes.md
      
      Report result in release-result.txt.
    input: release-notes.md
    output: release-result.txt
```

## Usage

```bash
export VERSION=1.2.3
relay run --config github-release-notes.yml
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token |
| `ISSUE_NUMBER` | Target issue number |
| `PR_NUMBER` | Target PR number |
| `VERSION` | Release version |

## Tips for GitHub Integration

1. **Authenticate First** — Run `gh auth login` before using these pipelines
2. **Rate Limits** — Be mindful of GitHub API rate limits
3. **Permissions** — Ensure your token has appropriate permissions
4. **Dry Run** — Test with `--dry-run` first to preview actions
5. **Branch Protection** — Consider branch protection rules when auto-creating PRs
