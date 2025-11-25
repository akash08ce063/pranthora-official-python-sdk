# Pranthora Python SDK

The official Python SDK for the Pranthora Voice Assistant Platform.

## Installation

```bash
pip install pranthora
```

## Usage

```python
from pranthora import Pranthora

client = Pranthora(api_key="YOUR_API_KEY")

# Create an agent
agent = client.agents.create(
    name="My Assistant",
    description="A helpful assistant"
)

print(f"Created agent: {agent.id}")
```

## Testing

The SDK includes a comprehensive test suite. To run tests:

```bash
# Run all tests
python test_sdk.py

# Run with verbose output
python test_sdk.py -v

# Run specific test class
python -m unittest test_sdk.TestAgents -v
```

For detailed testing documentation, see [TESTING.md](TESTING.md).

## Documentation

For full documentation, visit [https://docs.firstpeak.ai](https://docs.firstpeak.ai).
