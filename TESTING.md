# Pranthora SDK Testing Guide

This guide explains how to run and develop tests for the Pranthora SDK.

## Quick Start

### Run All Tests

```bash
# From the pranthora_sdk directory
python test_sdk.py
```

### Run with Verbose Output

```bash
python test_sdk.py -v
```

### Run Specific Test Classes

```bash
# Run only agent tests
python -m unittest test_sdk.TestAgents -v

# Run only API requestor tests
python -m unittest test_sdk.TestAPIRequestor -v

# Run only exception tests
python -m unittest test_sdk.TestExceptions -v
```

### Run Specific Test Methods

```bash
# Run a single test method
python -m unittest test_sdk.TestAgents.test_create_agent_with_all_mappings -v
```

## Test Structure

The test suite is organized into the following test classes:

### 1. `TestPranthoraClient`
Tests the main client initialization:
- Default and custom base URLs
- API key handling
- Resource initialization

### 2. `TestAgents`
Comprehensive tests for agent creation:
- ✅ All friendly name mappings (models, voices, transcribers)
- ✅ Default values
- ✅ Custom parameters
- ✅ Tools integration
- ✅ Fallback behavior for unknown names
- ✅ All LLM models, voices, and transcribers

### 3. `TestCalls`
Tests for call creation:
- ✅ Phone number handling
- ✅ Optional agent_id parameter
- ✅ Different phone number formats

### 4. `TestAPIRequestor`
Tests the API request handling:
- ✅ Successful requests
- ✅ Query parameters and JSON data
- ✅ Custom headers
- ✅ Error handling (401, 403, 404, 429, 500)
- ✅ Connection errors
- ✅ Timeout errors
- ✅ Non-JSON responses

### 5. `TestRealtimeVoiceClient`
Tests realtime voice functionality:
- ✅ Starting sessions
- ✅ Stopping sessions
- ✅ Assistant overrides
- ✅ Client reuse

### 6. `TestMappings`
Validates mapping dictionaries:
- ✅ TTS providers
- ✅ STT configurations
- ✅ LLM models
- ✅ Voices
- ✅ VAD providers

### 7. `TestExceptions`
Tests exception classes:
- ✅ All exception types
- ✅ Status codes and error bodies
- ✅ Exception hierarchy

### 8. `TestIntegration`
End-to-end integration tests:
- ✅ Complete agent creation flows

## Running Tests During Development

### Watch Mode (if you have pytest-watch installed)

```bash
# Install pytest-watch first
pip install pytest-watch

# Run tests in watch mode
ptw test_sdk.py
```

### Coverage Report

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run test_sdk.py

# Generate report
coverage report

# Generate HTML report
coverage html
# Then open htmlcov/index.html in your browser
```

## Test Best Practices

### 1. Mock External Dependencies
All tests use `unittest.mock` to mock HTTP requests and avoid making real API calls.

### 2. Test Edge Cases
- Unknown model/voice/transcriber names (fallback behavior)
- Different phone number formats
- Error responses (401, 403, 404, 429, 500)
- Connection failures

### 3. Test All Mappings
The suite includes tests that verify all mappings in `mappings.py` work correctly.

### 4. Isolated Tests
Each test is independent and doesn't rely on other tests.

## Adding New Tests

When adding new features to the SDK:

1. **Add tests to the appropriate test class** or create a new one
2. **Mock external dependencies** using `@patch` decorator
3. **Test both success and error cases**
4. **Test edge cases** and boundary conditions
5. **Update this guide** if you add new test categories

### Example: Adding a Test for a New Feature

```python
@patch("pranthora.utils.api_requestor.requests.request")
def test_new_feature(self, mock_request):
    """Test description."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_request.return_value = mock_response
    
    # Call the feature
    result = self.client.new_feature()
    
    # Assertions
    self.assertEqual(result["success"], True)
    mock_request.assert_called_once()
```

## Continuous Integration

For CI/CD pipelines, run:

```bash
python test_sdk.py
```

Exit code will be non-zero if any tests fail.

## Troubleshooting

### Import Errors
Make sure you're running tests from the `pranthora_sdk` directory and the SDK is properly installed:

```bash
pip install -e .
```

### Mock Issues
If mocks aren't working, check that you're patching the correct path:
- Use the path where the object is **used**, not where it's defined
- For example: `@patch("pranthora.utils.api_requestor.requests.request")` not `@patch("requests.request")`

### Async Tests
For testing async code (like VoiceClient), use `unittest.mock` with `AsyncMock` if needed, or test the synchronous wrapper methods.

## Test Statistics

Current test coverage:
- **8 test classes**
- **50+ test methods**
- **Covers all major SDK functionality**
- **All error cases tested**
- **All mappings validated**

## Next Steps

1. ✅ Run all tests: `python test_sdk.py`
2. ✅ Fix any failing tests
3. ✅ Add tests for new features as you develop
4. ✅ Keep test coverage high (>90%)

Happy testing! 🚀

