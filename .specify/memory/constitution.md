<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0 (minor version - new principle added)
Modified principles: N/A
Added sections:
  - Principle VI: Phased Pull Requests (new workflow principle)
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ compatible (no changes needed)
  - .specify/templates/spec-template.md: ✅ compatible (no changes needed)
  - .specify/templates/tasks-template.md: ✅ compatible (phase structure already defined)
Follow-up TODOs: None
-->

# computer-onboarding Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development is mandatory for all feature work:

- Tests MUST be written before implementation code
- Tests MUST fail before implementation begins (Red phase)
- Implementation MUST make tests pass with minimal code (Green phase)
- Code MUST be refactored only after tests pass (Refactor phase)
- No feature is complete until tests verify all acceptance criteria

**Rationale**: TDD ensures code correctness, prevents regression, and produces
testable designs. Writing tests first forces clear requirements and prevents
untested code paths.

### II. Simplicity First

Prefer the simplest solution that solves the current problem:

- YAGNI: Do not build features until they are needed
- Avoid premature abstraction; three similar implementations before extracting
- Minimize dependencies; justify each external dependency
- No speculative generalization or "future-proofing"
- Code MUST be deletable without breaking unrelated functionality

**Rationale**: Complexity is the enemy of reliability. Simple code is easier to
understand, test, maintain, and debug. Every abstraction has a cost.

### III. Unix Philosophy

Design for composability and interoperability:

- Each command MUST do one thing well
- Output MUST be usable as input to other programs (text streams)
- Support both human-readable and machine-parseable output (JSON flag)
- stdin for input, stdout for results, stderr for errors
- Exit codes MUST be meaningful (0 = success, non-zero = specific error)

**Rationale**: CLI tools that follow Unix conventions integrate naturally with
existing workflows, scripts, and toolchains. Composability multiplies utility.

### IV. Error Handling Excellence

Errors MUST be helpful, not cryptic:

- Error messages MUST state what went wrong in plain language
- Error messages MUST suggest how to fix the problem when possible
- Errors MUST include relevant context (file paths, values, etc.)
- Fatal errors MUST exit with appropriate non-zero codes
- Recoverable errors MUST allow graceful degradation where sensible

**Rationale**: Good error messages reduce debugging time and improve user
experience. Errors are documentation for failure modes.

### V. Documentation Required

All user-facing features MUST be documented:

- CLI commands MUST have --help output covering all options
- README MUST include quickstart instructions
- Non-obvious behavior MUST be explained in comments or docs
- Examples MUST accompany complex features
- Breaking changes MUST be documented in changelogs

**Rationale**: Undocumented features do not exist to users. Documentation is
part of the feature, not an afterthought.

### VI. Phased Pull Requests

Feature implementation MUST proceed through discrete phases with independent PRs:

- Each phase defined in tasks.md MUST result in a separate pull request
- PRs MUST be created in phase order (Setup → Foundational → User Story phases)
- Each PR MUST be reviewed and merged before the next phase begins
- PR title MUST reference the phase (e.g., "Phase 1: Setup for [feature]")
- Each phase PR MUST be independently reviewable and testable
- Foundation phases (Setup, Foundational) MUST complete before user story work

**Rationale**: Phased PRs enable incremental review, reduce change risk, allow
early feedback, and create logical rollback points. Large monolithic PRs are
harder to review, riskier to merge, and provide no incremental value delivery.

## Additional Constraints

### Security Standards

- All user input MUST be validated before processing
- No secrets, credentials, or API keys in source code
- File operations MUST validate paths to prevent traversal attacks
- External commands MUST be executed with minimal privileges
- Dependencies MUST be audited for known vulnerabilities before adoption

### Performance Standards

- CLI commands MUST respond within 500ms for local operations
- Memory usage MUST remain under 100MB for typical operations
- Long-running operations MUST show progress indicators
- Operations MUST be cancellable via SIGINT (Ctrl+C)
- Resource cleanup MUST occur on exit (normal or interrupted)

## Development Workflow

### Code Review Requirements

- All changes MUST be reviewed before merging
- Reviews MUST verify compliance with this constitution
- Tests MUST pass before review approval
- Documentation MUST be included for user-facing changes

### Quality Gates

- Linting MUST pass with zero warnings
- All tests MUST pass
- Code coverage MUST not decrease (maintain or improve)
- No new security vulnerabilities introduced

## Governance

This constitution establishes the non-negotiable standards for the
computer-onboarding project. All development work MUST comply.

### Amendment Process

1. Propose changes with rationale in writing
2. Review period of at least 48 hours
3. Amendments require documented approval
4. Migration plan required for breaking changes to existing code
5. Update version number according to semantic versioning

### Versioning Policy

- **MAJOR**: Backward-incompatible changes (principle removal/redefinition)
- **MINOR**: New principles or materially expanded guidance
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance

- All PRs MUST be checked against these principles
- Violations MUST be documented and justified in Complexity Tracking
- Constitution supersedes informal practices or preferences

**Version**: 1.1.0 | **Ratified**: 2026-01-31 | **Last Amended**: 2026-02-01
