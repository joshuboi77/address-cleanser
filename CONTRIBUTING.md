# Contributing to Address Cleanser

Thank you for your interest in contributing to Address Cleanser! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Installation

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/address-cleaner.git
   cd address-cleaner
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
   
   Or install as an editable package with dev extras:
   ```bash
   pip install -e ".[dev]"
   ```

## Code Style Guidelines

### Python Style

We follow PEP 8 style guidelines. Use `black` for automatic formatting:

```bash
black src/ tests/ cli.py
```

### Type Hints

All functions should include type hints:

```python
def parse_address(raw_address: str) -> Dict[str, Any]:
    """Parse a raw address string into structured components."""
    # Implementation here
```

### Docstrings

Use Google-style docstrings for all functions and classes:

```python
def validate_zip_code(zip_code: str) -> Tuple[bool, str]:
    """
    Validate ZIP code format (5-digit or ZIP+4).
    
    Args:
        zip_code: ZIP code string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
```

## Testing

### Running Tests

Run the full test suite:
```bash
python -m pytest tests/ -v
```

Run tests with coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Include edge cases and error conditions

Example test structure:
```python
def test_parse_standard_address(self):
    """Test parsing a standard street address."""
    address = "123 Main Street, Austin, TX 78701"
    result = parse_address(address)
    
    assert result['original'] == address
    assert result['confidence'] > 0
    assert result['error'] is None
```

### Test Coverage

- Maintain test coverage above 80%
- New features should include comprehensive tests
- Bug fixes should include regression tests

## Submitting Changes

### Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

3. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request on GitHub

### Commit Message Format

Use clear, descriptive commit messages:

- `Add: new feature description`
- `Fix: bug description`
- `Update: change description`
- `Remove: removal description`
- `Docs: documentation changes`

### Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Ensure all tests pass
- Update documentation if needed
- Keep PRs focused on a single feature/fix

## Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Detailed steps to reproduce the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: Python version, OS, etc.
6. **Sample data**: If applicable, include sample addresses or files

## Feature Requests

For feature requests, please include:

1. **Description**: Clear description of the proposed feature
2. **Use case**: Why this feature would be useful
3. **Implementation ideas**: Any thoughts on how to implement it
4. **Alternatives**: Other ways to solve the same problem

## Code Review Process

All code changes require review before merging:

1. **Automated checks**: CI/CD pipeline runs tests and linting
2. **Peer review**: At least one team member reviews the code
3. **Testing**: Reviewer tests the changes locally
4. **Approval**: Reviewer approves the changes

### Review Guidelines

When reviewing code:

- Check for correctness and edge cases
- Verify tests are comprehensive
- Ensure code follows style guidelines
- Look for potential security issues
- Consider performance implications

## Release Process

Releases are managed by the maintainers:

1. Update version in `src/__init__.py`
2. Update `CHANGELOG.md`
3. Create a release tag
4. Build and publish packages

## Questions?

If you have questions about contributing:

- Open an issue for discussion
- Check existing issues and pull requests
- Review the codebase and documentation

Thank you for contributing to Address Cleanser!
