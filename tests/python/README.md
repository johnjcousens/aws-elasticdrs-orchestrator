# Execution Engine Tests

Comprehensive test suite for the AWS DRS Orchestration Execution Engine.

## Test Structure

```
tests/python/
├── unit/           # Unit tests with mocked AWS services (fast)
├── integration/    # Integration tests with real AWS services
├── e2e/            # End-to-end tests with real DRS servers
├── fixtures/       # Test data fixtures
├── mocks/          # Mock AWS service implementations
├── utils/          # Test utilities and helpers
├── conftest.py     # Pytest configuration and shared fixtures
├── pytest.ini      # Pytest settings
└── requirements.txt # Python dependencies
```

## Setup

### Install Dependencies

```bash
cd tests/python
pip install -r requirements.txt
```

### Configure AWS Credentials (for integration/e2e tests)

```bash
# For integration tests
export AWS_PROFILE=drs-orchestration-test
export AWS_REGION=us-east-1

# Or use aws configure
aws configure --profile drs-orchestration-test
```

## Running Tests

### Run All Unit Tests (fast, no AWS credentials needed)

```bash
pytest unit/ -m unit
```

### Run Specific Test File

```bash
pytest unit/test_wave_orchestration.py -v
```

### Run Property-Based Tests Only

```bash
pytest -m property
```

### Run Integration Tests (requires AWS credentials)

```bash
pytest integration/ -m integration
```

### Run E2E Tests (requires real DRS servers, slow)

```bash
pytest e2e/ -m e2e --slow
```

### Run All Tests with Coverage

```bash
pytest --cov=../../lambda --cov-report=html
```

## Test Markers

- `@pytest.mark.unit` - Unit tests (mocked AWS, fast)
- `@pytest.mark.integration` - Integration tests (real AWS services)
- `@pytest.mark.e2e` - End-to-end tests (real DRS servers)
- `@pytest.mark.slow` - Tests taking >5 seconds
- `@pytest.mark.property` - Property-based tests (Hypothesis)

## Writing Tests

### Unit Test Example

```python
import pytest
from mocks.mock_drs_client import MockDRSClient

@pytest.mark.unit
def test_wave_sequential_execution(recovery_plans_table):
    """Test that waves execute in sequential order."""
    # Arrange
    plan = create_test_plan(waves=3)
    mock_drs = MockDRSClient()
    
    # Act
    result = execute_recovery_plan(plan, drs_client=mock_drs)
    
    # Assert
    assert result.wave_order == [1, 2, 3]
```

### Property-Based Test Example

```python
from hypothesis import given, strategies as st

@pytest.mark.property
@given(wave_count=st.integers(min_value=1, max_value=10))
def test_wave_execution_order_property(wave_count):
    """Property: Waves always execute in order."""
    plan = generate_recovery_plan(waves=wave_count)
    result = execute_with_mocks(plan)
    
    wave_times = [w.start_time for w in result.waves]
    assert wave_times == sorted(wave_times)
```

## Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: Critical paths validated
- **E2E Tests**: Key user scenarios validated

## CI/CD Integration

Tests run automatically on:
- Every commit: Unit tests
- Pull requests: Unit + Integration tests
- Main branch: All tests including E2E

## Troubleshooting

### Moto Errors

If you see moto-related errors, ensure you're using the correct version:
```bash
pip install moto[all]==4.2.9
```

### AWS Credentials

Unit tests don't need real AWS credentials (moto provides mocks).
Integration/E2E tests require valid AWS credentials with DRS permissions.

### Test Isolation

Each test runs in isolation with fresh mocked AWS services.
DynamoDB tables are created/destroyed for each test automatically.
