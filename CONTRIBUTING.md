# Contributing Guidelines

Thank you for considering contributing to this project! This document describes how to propose changes and get them merged.

## Before you start
- Check existing issues and pull requests to avoid duplication
- For non-trivial changes, please open an issue to discuss first
- Security vulnerabilities: DO NOT open a public issue — see SECURITY.md

## Development workflow
1. Fork the repository and create your feature branch
   - git checkout -b feat/short-description
2. Make your changes with clear, focused commits
   - Use conventional commits when possible (e.g., feat:, fix:, docs:, chore:)
3. Run tests/linters locally (if available) and ensure they pass
4. Rebase your branch on the latest main before opening a PR
5. Open a pull request with:
   - A clear description of the problem and solution
   - Screenshots or logs when relevant
   - Linked issues (e.g., Closes #123)

## Code style
- Follow existing code style and structure
- Include docstrings and comments where helpful
- Avoid committing secrets or environment-specific configs

## Commit message format
- feat: add QR code export to PNG
- fix: correct auth token validation
- docs: update deployment steps
- chore: bump dependencies

## Review process
- Maintainers review PRs for correctness, clarity, and scope
- Please be responsive to review comments and keep PRs focused

## License
By contributing, you agree that your contributions will be licensed under the Apache-2.0 license.
