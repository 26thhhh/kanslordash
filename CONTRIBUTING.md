# Contributing to KANSLORDASH

Thank you for your interest in contributing to KANSLORDASH!

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a virtual environment and install dependencies: `pip install -e ".[dev]"`
4. Run tests: `pytest`

## Guidelines

### Security First
- **Maintain read-only design** — Never add features that modify remote systems
- **No credential storage** — Don't add password/key storage functionality
- **Validate inputs** — All user inputs must be validated
- **Use safe subprocess calls** — Always use `create_subprocess_exec` with argument lists, never `shell=True` with user input

### Code Style
- Follow existing code patterns
- Use type hints where appropriate
- Keep line length reasonable (120 chars per ruff config)
- Add tests for new functionality
- Update documentation as needed

### Pull Request Process
1. Create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Add/update tests as appropriate
4. Ensure all tests pass: `pytest`
5. Update README.md if adding features
6. Submit a pull request with a clear description

### What to Contribute
- Bug fixes
- Documentation improvements
- Test coverage improvements
- Platform compatibility fixes
- UI/UX enhancements that maintain existing patterns
- Performance improvements

### What to Avoid
- Features that execute arbitrary commands on remote hosts
- Credential storage mechanisms
- Dependencies with known security issues
- Breaking changes to the registry format without migration path
- Hardcoded personal/environment-specific values

## Testing

Run the test suite:
```bash
pytest -v
```

All tests must pass before submitting a PR.

## Questions

Feel free to open an issue for discussion before starting work on major changes.
