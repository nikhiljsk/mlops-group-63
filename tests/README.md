# Testing Guide

This directory contains the test suite for the Iris Classification API, following MLOps best practices for comprehensive testing.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_api.py                 # API endpoint unit tests
├── test_models.py              # Pydantic model validation tests
├── test_prediction_service.py  # Prediction service unit tests
├── test_logging_service.py     # Logging service unit tests
├── integration/                # Integration tests
│   ├── __init__.py
│   └── test_api_integration.py # End-to-end API tests
└── README.md                   # This file
```

## Test Categories

### Unit Tests
- **API Tests** (`test_api.py`): Test individual API endpoints with mocked dependencies
- **Model Tests** (`test_models.py`): Test Pydantic model validation and serialization
- **Service Tests** (`test_prediction_service.py`, `test_logging_service.py`): Test business logic components

### Integration Tests
- **API Integration** (`test_api_integration.py`): End-to-end tests with real API server
- **Database Integration**: Tests with real database connections
- **MLflow Integration**: Tests with MLflow tracking and model registry

## Running Tests

### Local Development

```bash
# Install development dependencies
make install-dev

# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run tests with coverage report
pytest tests/ -v --cov=api --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test method
pytest tests/test_api.py::TestAPIEndpoints::test_predict_endpoint_success -v
```

### Docker Environment

```bash
# Run tests in Docker container
make test-docker

# Run tests with docker-compose
docker-compose run --rm iris-api python -m pytest tests/ -v
```

### CI/CD Pipeline

The GitHub Actions workflow automatically runs:
1. **Linting**: Code quality checks with flake8
2. **Formatting**: Code style checks with black and isort
3. **Unit Tests**: All unit tests with coverage reporting
4. **Integration Tests**: End-to-end API testing
5. **Docker Tests**: Container build and functionality tests
6. **Security Scanning**: Vulnerability scanning with Trivy

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Coverage settings
- Marker definitions
- Warning filters

### Fixtures (`conftest.py`)
- **test_settings**: Mock configuration for testing
- **client**: FastAPI test client
- **sample_prediction_request**: Sample API request data
- **sample_batch_request**: Sample batch request data

## Writing New Tests

### Unit Test Example

```python
import pytest
from unittest.mock import patch, MagicMock

class TestNewFeature:
    """Test class for new feature"""
    
    @patch('api.main.some_service')
    def test_new_endpoint(self, mock_service):
        """Test new API endpoint"""
        # Arrange
        mock_service.method.return_value = {"result": "success"}
        
        # Act
        with TestClient(app) as client:
            response = client.get("/new-endpoint")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["result"] == "success"
```

### Integration Test Example

```python
def test_new_feature_integration(self, api_server):
    """Test new feature end-to-end"""
    try:
        response = requests.get(f"{api_server}/new-endpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert "expected_field" in data
        
    except requests.exceptions.RequestException as e:
        pytest.skip(f"API server not available: {e}")
```

## Test Data

### Mock Data Creation
Tests use dynamically generated mock data to avoid dependencies on external files:

```python
# Create dummy model for testing
model = LogisticRegression(random_state=42)
scaler = StandardScaler()

X_dummy = np.random.RandomState(42).rand(100, 4)
y_dummy = np.random.RandomState(42).choice(['setosa', 'versicolor', 'virginica'], 100)

X_scaled = scaler.fit_transform(X_dummy)
model.fit(X_scaled, y_dummy)
```

### Test Database
- Uses temporary SQLite databases for isolation
- Each test gets a fresh database instance
- Automatic cleanup after test completion

## Coverage Requirements

- **Minimum Coverage**: 80% for all modules
- **Critical Paths**: 95% coverage for prediction and API endpoints
- **Coverage Reports**: Generated in XML and HTML formats
- **CI Integration**: Coverage reports uploaded to Codecov

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Mock External Dependencies**: Use mocks for external services (MLflow, databases)
3. **Descriptive Names**: Test names should clearly describe what is being tested
4. **Arrange-Act-Assert**: Follow the AAA pattern for test structure
5. **Edge Cases**: Test both happy path and error conditions
6. **Performance**: Include basic performance assertions for critical endpoints

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH=.` is set
2. **Model Loading**: Check that test artifacts are created properly
3. **Port Conflicts**: Use different ports for integration tests
4. **Database Locks**: Ensure proper cleanup of database connections

### Debug Mode

```bash
# Run tests with verbose output and no capture
pytest tests/ -v -s

# Run tests with pdb debugger
pytest tests/ --pdb

# Run specific test with maximum verbosity
pytest tests/test_api.py::TestAPIEndpoints::test_predict_endpoint_success -vvv
```

## Continuous Integration

The test suite is integrated with GitHub Actions and runs on:
- **Push to main/develop**: Full test suite
- **Pull Requests**: Full test suite with coverage reporting
- **Scheduled**: Nightly integration tests

Test results and coverage reports are available in the GitHub Actions interface and integrated with external services for monitoring and reporting.