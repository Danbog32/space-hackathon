# Contributing to Astro-Zoom

Thank you for your interest in contributing to Astro-Zoom! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork
3. Run the setup script: `./infra/setup.sh`
4. Create a feature branch: `git checkout -b feature/my-feature`

## Code Style

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow ESLint rules (enforced by CI)
- Use Prettier for formatting

### Python

- Follow PEP 8 style guide
- Use type hints where possible
- Run `ruff` and `mypy` before committing

## Commit Messages

Follow conventional commits format:

- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `refactor: improve code structure`
- `test: add tests`

## Pull Request Process

1. Update documentation if needed
2. Ensure all tests pass: `pnpm lint && pnpm typecheck`
3. Add a clear description of changes
4. Link any related issues
5. Request review from maintainers

## Testing

- Write unit tests for new features
- Ensure existing tests pass
- Test in both development and production modes

## Questions?

Open an issue for discussion before starting major changes.
