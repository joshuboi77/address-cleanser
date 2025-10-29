# Address Cleanser - Extension Guide

## Overview

This guide provides comprehensive best practices for extending the address-cleaner project while maintaining code quality, scalability, and collaboration standards. It covers repository architecture, folder organization, testing strategies, and development workflows.

## Repository Architecture Strategy

### Current Structure Assessment

The address-cleaner project follows a **modular monorepo** approach, which is ideal for:
- Single-purpose tools with multiple components
- Shared dependencies and configurations
- Simplified CI/CD pipelines
- Easy local development and testing

### Recommended Extension Patterns

#### 1. **Modular Component Architecture**

```
address-cleaner/
├── src/                          # Core library modules
│   ├── __init__.py
│   ├── parser/                   # Address parsing components
│   │   ├── __init__.py
│   │   ├── usaddress_parser.py
│   │   ├── custom_parser.py      # Future: custom parsing logic
│   │   └── validation_rules.py
│   ├── validator/                # Validation components
│   │   ├── __init__.py
│   │   ├── zip_validator.py
│   │   ├── state_validator.py
│   │   └── completeness_validator.py
│   ├── formatter/                # Formatting components
│   │   ├── __init__.py
│   │   ├── usps_formatter.py
│   │   └── custom_formatters.py  # Future: custom formatting
│   ├── api/                      # Future: API components
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   ├── middleware/
│   │   └── serializers/
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── file_handlers.py
│       ├── logging_config.py
│       └── performance.py
├── cli/                          # CLI interface
│   ├── __init__.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── batch.py
│   │   ├── single.py
│   │   └── validate.py           # Future: validation commands
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── input_handlers.py
│   │   └── output_handlers.py
│   └── cli.py                    # Main CLI entry point
├── web/                          # Future: Web interface
│   ├── __init__.py
│   ├── app.py
│   ├── templates/
│   ├── static/
│   └── routes/
├── tests/                        # Comprehensive test suite
│   ├── __init__.py
│   ├── unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── test_parser/
│   │   ├── test_validator/
│   │   ├── test_formatter/
│   │   └── test_utils/
│   ├── integration/              # Integration tests
│   │   ├── __init__.py
│   │   ├── test_cli_integration.py
│   │   ├── test_api_integration.py
│   │   └── test_file_processing.py
│   ├── e2e/                      # End-to-end tests
│   │   ├── __init__.py
│   │   ├── test_full_workflows.py
│   │   └── test_performance.py
│   ├── fixtures/                 # Test data and fixtures
│   │   ├── sample_addresses.csv
│   │   ├── test_data.json
│   │   └── mock_responses/
│   └── conftest.py               # Pytest configuration
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   ├── user_guides/              # User documentation
│   ├── developer_guides/         # Developer documentation
│   └── examples/                 # Code examples
├── scripts/                      # Development and deployment scripts
│   ├── setup_dev.py
│   ├── generate_test_data.py
│   ├── benchmark.py
│   └── deploy.sh
├── config/                       # Configuration files
│   ├── development.yaml
│   ├── production.yaml
│   └── testing.yaml
├── docker/                       # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
└── .github/                      # GitHub workflows and templates
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

## Folder Organization Best Practices

### 1. **Separation of Concerns**

Each directory should have a single, well-defined responsibility:

- **`src/`**: Core business logic and algorithms
- **`cli/`**: Command-line interface and user interactions
- **`web/`**: Web interface and API endpoints
- **`tests/`**: All testing code organized by type
- **`docs/`**: Documentation and guides
- **`scripts/`**: Development and deployment automation
- **`config/`**: Configuration files and settings

### 2. **Test Organization Strategy**

#### Unit Tests (`tests/unit/`)
```
tests/unit/
├── test_parser/
│   ├── test_usaddress_parser.py
│   ├── test_custom_parser.py
│   └── test_validation_rules.py
├── test_validator/
│   ├── test_zip_validator.py
│   ├── test_state_validator.py
│   └── test_completeness_validator.py
├── test_formatter/
│   ├── test_usps_formatter.py
│   └── test_custom_formatters.py
└── test_utils/
    ├── test_file_handlers.py
    └── test_performance.py
```

#### Integration Tests (`tests/integration/`)
```
tests/integration/
├── test_cli_integration.py      # CLI command integration
├── test_api_integration.py      # API endpoint integration
├── test_file_processing.py      # File I/O integration
└── test_database_integration.py # Future: database integration
```

#### End-to-End Tests (`tests/e2e/`)
```
tests/e2e/
├── test_full_workflows.py       # Complete user workflows
├── test_performance.py          # Performance benchmarks
└── test_error_scenarios.py      # Error handling scenarios
```

### 3. **Configuration Management**

```
config/
├── development.yaml             # Development environment settings
├── production.yaml              # Production environment settings
├── testing.yaml                # Test environment settings
├── logging.yaml                # Logging configuration
└── validation_rules.yaml       # Custom validation rules
```

## Development Workflow Best Practices

### 1. **Branching Strategy**

Adopt **Gitflow** for feature development:

```
main                    # Production-ready code
├── develop            # Integration branch for features
├── feature/           # Feature branches
│   ├── feature/api-development
│   ├── feature/web-interface
│   └── feature/performance-optimization
├── release/           # Release preparation branches
└── hotfix/            # Critical bug fixes
```

### 2. **Commit Convention**

Use **Conventional Commits** for clear history:

```
feat: add REST API endpoints for address validation
fix: resolve memory leak in batch processing
docs: update API documentation with examples
test: add integration tests for CLI commands
refactor: extract validation logic into separate modules
perf: optimize address parsing performance
```

### 3. **Pull Request Workflow**

#### PR Template Requirements:
- [ ] **Description**: Clear explanation of changes
- [ ] **Testing**: Unit tests added/updated
- [ ] **Documentation**: README/docs updated
- [ ] **Breaking Changes**: Documented if any
- [ ] **Performance Impact**: Assessed and documented

#### Code Review Checklist:
- [ ] Code follows project style guidelines
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] No breaking changes without notice
- [ ] Performance impact is acceptable

## Testing Strategy

### 1. **Test Pyramid Implementation**

```
    /\
   /  \     E2E Tests (10%)
  /____\    - Full workflow tests
 /      \   - Performance tests
/        \  - Error scenario tests
/          \
/            \  Integration Tests (20%)
/              \ - API integration
/                \ - CLI integration
/                  \ - File processing
/                    \
/                      \  Unit Tests (70%)
/                        \ - Component testing
/                          \ - Edge case testing
/                            \ - Mock testing
```

### 2. **Test Data Management**

```
tests/fixtures/
├── addresses/
│   ├── valid_addresses.csv
│   ├── invalid_addresses.csv
│   ├── edge_cases.csv
│   └── performance_test_data.csv
├── responses/
│   ├── usps_api_responses.json
│   └── mock_geocoding_responses.json
└── configs/
    ├── test_config.yaml
    └── validation_rules_test.yaml
```

### 3. **Test Configuration**

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_addresses():
    """Load sample address data for testing."""
    data_file = Path(__file__).parent / "fixtures" / "addresses" / "valid_addresses.csv"
    return load_test_data(data_file)

@pytest.fixture
def mock_usps_api():
    """Mock USPS API responses."""
    return MockUSPSAPI()

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary directory for test outputs."""
    return tmp_path / "test_outputs"
```

## Dependency Management

### 1. **Requirements Organization**

```
requirements/
├── base.txt              # Core dependencies
├── development.txt       # Development tools
├── testing.txt           # Testing frameworks
├── production.txt        # Production dependencies
└── optional.txt          # Optional features
```

### 2. **Version Pinning Strategy**

```python
# requirements/base.txt
usaddress>=0.5.10,<0.6.0    # Pin major.minor, allow patch updates
pandas>=2.0.0,<3.0.0       # Pin major version
click>=8.1.8,<9.0.0        # Pin major version
tqdm>=4.66.1,<5.0.0        # Pin major version
psutil>=6.1.1,<7.0.0       # Pin major version
```

### 3. **Dependency Updates**

- **Automated**: Use Dependabot for security updates
- **Manual**: Monthly review of major version updates
- **Testing**: Comprehensive testing before dependency updates

## Code Quality Standards

### 1. **Linting and Formatting**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.8
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

### 2. **Type Hints and Documentation**

```python
from typing import Dict, List, Optional, Union
from pathlib import Path

def process_addresses(
    input_file: Path,
    output_file: Path,
    format_type: str = "csv",
    chunk_size: int = 1000,
    validation_rules: Optional[Dict[str, bool]] = None
) -> Dict[str, Union[int, float]]:
    """
    Process addresses from input file and write to output file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output file
        format_type: Output format ('csv', 'json', 'excel')
        chunk_size: Number of addresses to process per chunk
        validation_rules: Custom validation rules
        
    Returns:
        Dictionary with processing statistics
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If format_type is invalid
    """
    # Implementation here
    pass
```

## Performance and Scalability

### 1. **Performance Monitoring**

```python
# src/utils/performance.py
import time
import psutil
from functools import wraps
from typing import Callable, Any

def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f}s")
        logger.info(f"Memory usage: {(end_memory - start_memory) / 1024 / 1024:.2f}MB")
        
        return result
    return wrapper
```

### 2. **Caching Strategy**

```python
# src/utils/caching.py
from functools import lru_cache
from typing import Dict, Any
import json
import hashlib

class AddressCache:
    """Cache for processed addresses to avoid reprocessing."""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
    
    def get_cache_key(self, address: str) -> str:
        """Generate cache key for address."""
        return hashlib.md5(address.lower().encode()).hexdigest()
    
    def get(self, address: str) -> Optional[Dict[str, Any]]:
        """Get cached result for address."""
        key = self.get_cache_key(address)
        return self.cache.get(key)
    
    def set(self, address: str, result: Dict[str, Any]) -> None:
        """Cache result for address."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self.get_cache_key(address)
        self.cache[key] = result
```

## Security Best Practices

### 1. **Input Validation**

```python
# src/validator/input_validator.py
import re
from pathlib import Path
from typing import Union

class InputValidator:
    """Validate user inputs to prevent security issues."""
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path]) -> Path:
        """Validate file path to prevent directory traversal."""
        path = Path(file_path).resolve()
        
        # Ensure path is within allowed directories
        allowed_dirs = [Path.cwd(), Path.home()]
        
        if not any(str(path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
            raise ValueError("File path outside allowed directories")
        
        return path
    
    @staticmethod
    def validate_address_input(address: str) -> str:
        """Validate address input to prevent injection attacks."""
        # Remove potentially dangerous characters
        cleaned = re.sub(r'[<>"\']', '', address)
        
        if len(cleaned) > 1000:  # Prevent extremely long inputs
            raise ValueError("Address too long")
        
        return cleaned.strip()
```

### 2. **Secrets Management**

```python
# config/secrets.yaml (not committed to git)
api_keys:
  usps_api_key: ${USPS_API_KEY}
  google_maps_key: ${GOOGLE_MAPS_API_KEY}

database:
  connection_string: ${DATABASE_URL}
```

## Documentation Standards

### 1. **API Documentation**

```python
# src/api/endpoints/validation.py
from flask import Flask, request, jsonify
from typing import Dict, Any

app = Flask(__name__)

@app.route('/api/v1/validate', methods=['POST'])
def validate_address() -> Dict[str, Any]:
    """
    Validate a single address.
    
    ---
    tags:
      - validation
    parameters:
      - in: body
        name: address
        description: Address to validate
        required: true
        schema:
          type: object
          properties:
            address:
              type: string
              example: "123 Main St, Austin, TX 78701"
    responses:
      200:
        description: Validation result
        schema:
          type: object
          properties:
            valid:
              type: boolean
            confidence:
              type: number
            formatted_address:
              type: string
    """
    data = request.get_json()
    address = data.get('address')
    
    if not address:
        return jsonify({'error': 'Address is required'}), 400
    
    # Process address
    result = process_single_address(address)
    
    return jsonify(result)
```

### 2. **Developer Documentation**

```markdown
# docs/developer_guides/contributing.md

## Contributing to Address Cleanser

### Development Setup

1. Clone the repository
2. Create virtual environment
3. Install dependencies
4. Run tests

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 80%

### Testing Requirements

- Unit tests for all new functions
- Integration tests for API endpoints
- Performance tests for batch operations
```

## Deployment and CI/CD

### 1. **GitHub Actions Workflow**

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements/development.txt
        pip install -r requirements/testing.txt
    
    - name: Run linting
      run: |
        black --check src/ cli/ tests/
        isort --check-only src/ cli/ tests/
        flake8 src/ cli/ tests/
        mypy src/ cli/
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 2. **Docker Configuration**

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements/ requirements/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy source code
COPY src/ src/
COPY cli/ cli/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port for API
EXPOSE 8000

# Default command
CMD ["python", "-m", "cli"]
```

## Monitoring and Observability

### 1. **Logging Configuration**

```python
# src/utils/logging_config.py
import logging
import logging.config
from pathlib import Path

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': 'logs/address_cleaner.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

def setup_logging():
    """Setup logging configuration."""
    Path('logs').mkdir(exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
```

### 2. **Metrics Collection**

```python
# src/utils/metrics.py
import time
from typing import Dict, Any
from collections import defaultdict

class MetricsCollector:
    """Collect and track application metrics."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(float)
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric."""
        self.counters[name] += value
    
    def record_timing(self, name: str, duration: float):
        """Record a timing metric."""
        self.timers[name].append(duration)
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric."""
        self.gauges[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            'counters': dict(self.counters),
            'timers': {name: {
                'count': len(times),
                'avg': sum(times) / len(times) if times else 0,
                'min': min(times) if times else 0,
                'max': max(times) if times else 0
            } for name, times in self.timers.items()},
            'gauges': dict(self.gauges)
        }
```

## Extension Checklist

### Before Adding New Features

- [ ] **Define Requirements**: Clear specification of what needs to be built
- [ ] **Assess Impact**: Understand how changes affect existing functionality
- [ ] **Plan Testing**: Determine what tests need to be written/updated
- [ ] **Update Documentation**: Plan documentation updates
- [ ] **Consider Performance**: Assess performance implications
- [ ] **Security Review**: Identify potential security concerns

### During Development

- [ ] **Follow Code Standards**: Adhere to project style guidelines
- [ ] **Write Tests First**: Implement TDD approach
- [ ] **Update Documentation**: Keep docs in sync with code
- [ ] **Monitor Performance**: Track performance impact
- [ ] **Code Review**: Get peer review before merging

### After Implementation

- [ ] **Integration Testing**: Ensure new features work with existing code
- [ ] **Performance Testing**: Verify performance requirements are met
- [ ] **Documentation Review**: Ensure all docs are accurate and complete
- [ ] **User Testing**: Get feedback from end users
- [ ] **Monitoring**: Set up monitoring for new features

## Conclusion

This extension guide provides a comprehensive framework for extending the address-cleaner project while maintaining high code quality, scalability, and collaboration standards. By following these practices, developers can:

1. **Maintain Code Quality**: Through consistent standards and automated checks
2. **Ensure Scalability**: With proper architecture and performance monitoring
3. **Facilitate Collaboration**: Through clear workflows and documentation
4. **Reduce Technical Debt**: By following best practices from the start
5. **Enable Rapid Development**: With well-organized code and testing strategies

The key to successful project extension is maintaining consistency, thorough testing, and clear communication throughout the development process.
