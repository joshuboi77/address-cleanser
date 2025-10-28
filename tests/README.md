# Testing Guide

This directory contains the test suite for the Address Cleanser tool.

## Test Organization

### Test Files

- `test_parser.py` - Tests for address parsing functionality
- `test_validator.py` - Tests for address validation functionality  
- `test_integration.py` - End-to-end integration tests
- `test_cli.py` - CLI command-line interface tests
- `test_performance.py` - Performance and benchmark tests

### Test Categories

#### Unit Tests
- Individual function testing
- Edge case handling
- Error condition testing
- Input validation

#### Integration Tests
- Complete pipeline testing
- Cross-module functionality
- Real-world scenarios

#### CLI Tests
- Command execution testing
- Output format validation
- Error handling
- Configuration options

#### Performance Tests
- Processing speed benchmarks
- Memory usage profiling
- Scalability testing
- Different address types

## Running Tests

### Basic Test Execution

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_parser.py -v

# Run specific test class
python -m pytest tests/test_parser.py::TestParseAddress -v

# Run specific test method
python -m pytest tests/test_parser.py::TestParseAddress::test_parse_standard_address -v
```

### Coverage Testing

```bash
# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run tests with coverage and terminal report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Generate coverage report
python -m pytest tests/ --cov=src --cov-report=html --cov-report=xml
```

### Performance Testing

```bash
# Run performance tests
python -m pytest tests/test_performance.py -v -s

# Run with performance output
python -m pytest tests/test_performance.py -v -s --tb=short
```

## Coverage Requirements

### Minimum Coverage
- **Overall**: 80% minimum
- **Core modules**: 90% minimum
- **New features**: 95% minimum

### Coverage Exclusions
- Test files themselves
- Virtual environment files
- Abstract methods and protocols
- Debug code paths

## Adding New Tests

### Test Naming Convention

```python
def test_function_name_scenario(self):
    """Test description of what this test validates."""
    # Test implementation
```

### Test Structure

```python
class TestClassName:
    """Test cases for specific functionality."""
    
    def test_success_case(self):
        """Test normal operation."""
        # Arrange
        input_data = "test input"
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result.expected_property == expected_value
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            function_under_test(invalid_input)
    
    def test_edge_case(self):
        """Test edge cases."""
        result = function_under_test(edge_case_input)
        assert result is not None
```

### Test Data

- Use realistic test data
- Include edge cases and error conditions
- Test both valid and invalid inputs
- Use descriptive variable names

### Performance Test Guidelines

```python
def test_performance_benchmark(self):
    """Test performance requirements."""
    start_time = time.time()
    
    # Perform operations
    for _ in range(iterations):
        function_under_test()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / iterations
    
    # Assert performance requirements
    assert avg_time < max_allowed_time
```

## Test Dependencies

### Required Packages
- `pytest` - Test framework
- `pytest-cov` - Coverage testing
- `pandas` - Data manipulation for CSV tests
- `psutil` - Memory profiling for performance tests

### Optional Packages
- `black` - Code formatting
- `flake8` - Linting

## Continuous Integration

Tests are automatically run on:
- Pull request creation
- Code push to main branch
- Release preparation

### CI Requirements
- All tests must pass
- Coverage must meet minimum requirements
- Performance tests must pass benchmarks
- No linting errors

## Debugging Tests

### Verbose Output
```bash
python -m pytest tests/ -v -s
```

### Debug Specific Test
```bash
python -m pytest tests/test_parser.py::TestParseAddress::test_parse_standard_address -v -s --pdb
```

### Coverage Debugging
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Realistic Data**: Use real-world test data when possible
4. **Error Testing**: Test both success and failure cases
5. **Performance Awareness**: Monitor test execution time
6. **Documentation**: Document complex test scenarios
7. **Maintenance**: Keep tests updated with code changes
