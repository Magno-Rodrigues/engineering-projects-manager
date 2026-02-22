# Contributing to Engineering Projects Manager

Thank you for your interest in contributing! Please follow these guidelines.

## Code of Conduct

Be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes following the guidelines below
4. Run the tests: `pytest`
5. Submit a pull request

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
- Use type hints for function signatures
- Write docstrings for all public functions, classes, and modules
- Keep lines under 120 characters

## Commit Messages

Use conventional commits format:

```
feat: add task priority filter
fix: correct date formatting in helpers
docs: update README setup instructions
test: add tests for project service
refactor: simplify auth service logic
```

## Pull Request Guidelines

- Include a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Add tests for new functionality
- Update documentation as needed

## Project Structure

- **models/**: SQLAlchemy models — one file per entity
- **routes/**: Flask Blueprints — keep route handlers thin
- **services/**: Business logic — services are called by routes
- **utils/**: Shared utilities — decorators and helpers
- **tests/**: One test file per module

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_auth.py
```
