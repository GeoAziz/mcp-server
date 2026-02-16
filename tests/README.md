# MCP Server Test Suite

This directory contains the automated test suite for the MCP Server using pytest and FastAPI TestClient.

## Test Coverage

The test suite covers all core functionality:

### Endpoints (`test_endpoints.py`)
- Health check endpoint (`/`)
- State endpoint (`/mcp/state`) with filtering and pagination
- Query endpoint (`/mcp/query`) for all actions
- Logs endpoint (`/mcp/logs`)
- Reset endpoint (`/mcp/reset`)

### User Operations (`test_users.py`)
- List users
- Add user
- Remove user
- Get user details
- User validation and error handling

### Task Operations (`test_tasks.py`)
- List tasks
- Add task
- Update task
- Delete task
- Search tasks
- Filter by status and assignee
- Task validation and error handling

### Configuration Operations (`test_config.py`)
- Get configuration (all and specific keys)
- Update configuration
- Various data types support
- Config validation and error handling

### Authentication (`test_auth.py`)
- Authentication disabled when MCP_API_KEY not set
- Authentication required when MCP_API_KEY is set
- Valid API key acceptance
- Invalid API key rejection
- All endpoints with authentication

### Error Handling (`test_error_handling.py`)
- Invalid actions
- Missing required parameters
- Resource not found errors
- Duplicate resource errors
- Input validation
- Response format consistency

## Running the Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run a specific test file
```bash
pytest tests/test_users.py
```

### Run a specific test function
```bash
pytest tests/test_users.py::test_add_user
```

### Run with coverage report
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run tests and show print statements
```bash
pytest tests/ -v -s
```

## Test Database

Tests use an in-memory SQLite database for:
- **Speed**: No disk I/O overhead
- **Isolation**: Each test gets a fresh database
- **Safety**: No risk of affecting production data
- **Portability**: No external database dependencies

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

- `test_db`: Provides a fresh in-memory database for each test
- `client`: TestClient with test database (no authentication)
- `client_with_auth`: TestClient with authentication enabled
- `sample_users`: Sample user data
- `sample_tasks`: Sample task data
- `sample_config`: Sample configuration data

## Test Organization

Tests are organized by functionality:
- `test_endpoints.py`: Core endpoint tests
- `test_users.py`: User management tests
- `test_tasks.py`: Task management tests
- `test_config.py`: Configuration management tests
- `test_auth.py`: Authentication and authorization tests
- `test_error_handling.py`: Error handling and edge case tests

## Continuous Integration

These tests are designed to run in CI/CD pipelines. They:
- Don't require external services
- Run quickly (< 5 seconds)
- Have no side effects
- Are deterministic and repeatable

## Adding New Tests

When adding new functionality:

1. Create test functions in the appropriate test file
2. Use descriptive test names: `test_<what>_<scenario>`
3. Follow the AAA pattern:
   - **Arrange**: Set up test data
   - **Act**: Perform the action
   - **Assert**: Verify the results
4. Use fixtures for common setup
5. Test both success and error cases

Example:
```python
def test_add_user_success(client):
    """Test adding a new user successfully"""
    # Arrange
    user_data = {"username": "testuser", "role": "admin"}
    
    # Act
    response = client.post(
        "/mcp/query",
        json={"action": "add_user", "params": user_data}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## Requirements

Tests require the following packages (installed via `requirements.txt`):
- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `httpx`: HTTP client for TestClient
- `fastapi`: FastAPI framework
- `sqlalchemy`: Database ORM

## Notes

- Rate limiting is set to a high value for tests to avoid throttling
- Authentication is disabled by default in tests unless using `client_with_auth`
- Database is reset between each test for isolation
- Tests use TestClient which runs the app without starting a server
