# 🧪 SA News Podcast - Testing Guide

## Overview

This document describes the comprehensive testing strategy for the SA News Podcast project, following TDD principles and ensuring all functionality is properly tested.

## Test Structure

### Test Types

1. **Unit Tests** - Test individual functions and methods
2. **Integration Tests** - Test component interactions  
3. **End-to-End Tests** - Test complete workflow

### Test Files

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── test_ai_news_fetcher.py       # Unit tests for AI news fetching
├── test_transcript_generator.py  # Unit tests for transcript generation
├── test_text_sanitization.py     # Unit tests for text sanitization
├── test_apostrophe_fix.py        # Unit tests for apostrophe fixes
├── test_workflow_integration.py  # Integration tests for workflow
└── test_end_to_end.py            # End-to-end tests for complete pipeline
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Or run pytest directly
python -m pytest tests/ -v
```

### Specific Test Types

```bash
# Unit tests only
python -m pytest tests/ -k "not integration and not e2e" -v

# Integration tests only  
python -m pytest tests/ -k "integration" -v

# End-to-end tests only
python -m pytest tests/ -k "e2e" -v

# Specific test file
python -m pytest tests/test_ai_news_fetcher.py -v
```

### Test Coverage

```bash
# Install coverage tools
pip install -r requirements-test.txt

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Requirements

### Per AGENTS.md Guidelines

- ✅ **Unit tests**: Test individual functions and methods
- ✅ **Integration tests**: Test component interactions
- ✅ **End-to-end tests**: Test complete workflow
- ✅ **NO EXCEPTIONS POLICY**: All test types required
- ✅ **Real data**: Use real APIs, never mock implementations
- ✅ **Pristine output**: Test output must be clean to pass

### Test Data Strategy

- **Real API Keys**: Tests use actual API keys from `~/.config/sa-podcast/secrets.json`
- **Real Data**: Tests fetch real news data from AI APIs
- **No Mocks**: Following the "no mock mode" policy from AGENTS.md
- **Temporary Files**: Use temporary files for test data cleanup

## Test Categories

### 1. Unit Tests

#### `test_ai_news_fetcher.py`
- Tests Perplexity API integration
- Tests Claude API integration  
- Tests OpenAI API integration
- Tests concurrent API calls
- Tests error handling
- Tests file saving

#### `test_transcript_generator.py`
- Tests Claude transcript generation
- Tests transcript validation
- Tests South African timezone handling
- Tests TTS optimization
- Tests error handling

#### `test_text_sanitization.py`
- Tests apostrophe removal
- Tests contraction expansion
- Tests number formatting
- Tests special character handling
- Tests edge cases

#### `test_apostrophe_fix.py`
- Tests before/after apostrophe fixes
- Tests TTS pronunciation improvements
- Tests various apostrophe types

### 2. Integration Tests

#### `test_workflow_integration.py`
- Tests AI news fetching + transcript generation
- Tests file handling between components
- Tests error propagation
- Tests concurrent operations

### 3. End-to-End Tests

#### `test_end_to_end.py`
- Tests complete AI workflow
- Tests podcast creation with TTS
- Tests main function with --ai flag
- Tests error handling throughout pipeline
- Tests file validation and cleanup
- Tests different transcript formats

## Test Fixtures

### Shared Fixtures (conftest.py)

- `mock_secrets`: Mock secrets object for testing
- `temp_transcript_file`: Temporary transcript file
- `temp_news_digests_file`: Temporary news digests file
- `temp_output_dir`: Temporary output directory
- `setup_test_environment`: Test environment setup

## Test Configuration

### Pytest Markers

- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.slow`: Slow-running tests

### Test Environment

- Tests run in isolated temporary directories
- Automatic cleanup of test files
- Proper path handling for imports
- Mock secrets for API key testing

## Continuous Integration

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### GitHub Actions (if applicable)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: python run_tests.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project root
   cd /path/to/sa-news-podcast
   python -m pytest tests/ -v
   ```

2. **Missing Dependencies**
   ```bash
   # Install all dependencies
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **API Key Issues**
   ```bash
   # Ensure secrets.json exists
   ls ~/.config/sa-podcast/secrets.json
   ```

4. **Permission Issues**
   ```bash
   # Make test runner executable
   chmod +x run_tests.py
   ```

### Test Debugging

```bash
# Run with verbose output
python -m pytest tests/ -v -s

# Run with debug output
python -m pytest tests/ --tb=long

# Run specific test with debugging
python -m pytest tests/test_ai_news_fetcher.py::TestAINewsFetcher::test_fetch_perplexity_news -v -s
```

## Test Maintenance

### Adding New Tests

1. **Unit Tests**: Add to appropriate existing test file or create new one
2. **Integration Tests**: Add to `test_workflow_integration.py`
3. **E2E Tests**: Add to `test_end_to_end.py`

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>`

### Test Documentation

- Each test should have a docstring explaining what it tests
- Use descriptive test names
- Include comments for complex test logic
- Document any special setup requirements

## Performance Testing

### Benchmark Tests

```bash
# Install benchmark tools
pip install pytest-benchmark

# Run benchmark tests
python -m pytest tests/ --benchmark-only
```

### Load Testing

- Test concurrent API calls
- Test large transcript processing
- Test memory usage with large files

## Security Testing

### API Key Security

- Tests verify secrets are loaded from secure location
- Tests ensure no hardcoded keys in test files
- Tests validate proper error handling for missing keys

### Input Validation

- Tests verify proper input sanitization
- Tests check for injection vulnerabilities
- Tests validate file path security

## Test Metrics

### Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage  
- **E2E Tests**: 70%+ coverage
- **Overall**: 85%+ coverage

### Performance Goals

- **Unit Tests**: < 1 second per test
- **Integration Tests**: < 10 seconds per test
- **E2E Tests**: < 30 seconds per test
- **Total Suite**: < 5 minutes

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clean Setup**: Use fixtures for common setup
3. **Proper Cleanup**: Always clean up test files
4. **Real Data**: Use real APIs and data when possible
5. **Error Testing**: Test both success and failure cases
6. **Edge Cases**: Test boundary conditions and edge cases
7. **Documentation**: Keep tests well-documented
8. **Maintenance**: Keep tests up-to-date with code changes

## Conclusion

This comprehensive testing strategy ensures the SA News Podcast system is robust, reliable, and maintainable. All tests follow TDD principles and use real data as specified in the project requirements.

For questions or issues with testing, refer to the troubleshooting section or create an issue in the project repository.
