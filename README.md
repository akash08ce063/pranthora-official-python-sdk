# Pranthora Python SDK

The official Python SDK for the Pranthora Voice Assistant Platform.

## Installation

```bash
pip install pranthora
```

## Usage

### Initialize Client

```python
from pranthora import Pranthora

client = Pranthora(api_key="YOUR_API_KEY", base_url="http://localhost:5050")
```

### Agents

#### Create an Agent

```python
# Create an agent with default configurations
agent = client.agents.create(
    name="My Assistant",
    description="A helpful voice assistant",
    model="gpt-4.1-mini",
    voice="thalia",
    transcriber="deepgram_nova_3",
    first_response_message="Hello! How can I help you today?"
)

print(f"Created agent: {agent['agent']['id']}")
```

#### List All Agents

```python
# Get all agents for the current user
agents = client.agents.list()

for agent in agents:
    agent_data = agent.get('agent', {})
    print(f"Name: {agent_data.get('name')}, ID: {agent_data.get('id')}")
```

#### Get Agent by ID

```python
# Get a specific agent by ID
agent = client.agents.get(agent_id="YOUR_AGENT_ID")

print(f"Agent Name: {agent['agent']['name']}")
print(f"Status: {'Active' if agent['agent']['is_active'] else 'Inactive'}")
```

#### Update an Agent

```python
# Update agent name and description
updated_agent = client.agents.update(
    agent_id="YOUR_AGENT_ID",
    name="Updated Agent Name",
    description="Updated description"
)

# Update with configuration changes
updated_agent = client.agents.update(
    agent_id="YOUR_AGENT_ID",
    name="New Name",
    voice="darla",
    temperature=0.8,
    system_prompt="You are a helpful customer support agent."
)
```

#### Delete an Agent

```python
# Delete an agent (force_delete=True by default)
client.agents.delete(agent_id="YOUR_AGENT_ID")

# Or explicitly set force_delete
client.agents.delete(agent_id="YOUR_AGENT_ID", force_delete=True)
```

### Real-time Voice Calls

#### Start a Call

```python
# Start a call with an existing agent
client.start(agent_id="YOUR_AGENT_ID")

# Or start with overrides
assistant_overrides = {
    "variableValues": {
        "name": "John"
    }
}
client.start(agent_id="YOUR_AGENT_ID", assistant_overrides=assistant_overrides)
```

#### Stop a Call

```python
client.stop()
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
