from pranthora import Pranthora

client = Pranthora(api_key="a967a994b2ee02c0b4578e5e02bba7d3", base_url="http://localhost:5050/api/v1")

# # Create an agent with default configurations
# agent = client.agents.create(
#     name="Raj's Assistant",
#     description="Raj's voice assistant",
#     model="gemini-2.5-flash-lite",
#     voice="priya",
#     transcriber="deepgram_flux",
#     first_response_message="Hello! I am Raj",
#     system_prompt="You are RAJ a helpful assistant that can answer questions and help with tasks."
# )

# print(f"Created agent: {agent}")


# # Get all agents for the current user
# agents = client.agents.list()

# for agent in agents:
#     agent_data = agent.get('agent', {})
#     print(f"Name: {agent_data.get('name')}, ID: {agent_data.get('id')}")



# # Get a specific agent by ID
# agent = client.agents.get(agent_id="71f6a4be-7131-4b0e-8a4d-dae6db40850a")

# print(f"Agent: {agent}")


# # Update with configuration changes
# updated_agent = client.agents.update(
#     agent_id="71f6a4be-7131-4b0e-8a4d-dae6db40850a",
#     name="its anuj",
#     voice="apollo",
#     temperature=0.8,
#     model="gemini-2.5-flash-lite",
#     system_prompt="You are a AAANUJJJ helpful customer support agent."
# )

# print(f"Updated agent: {updated_agent}")



# # Or explicitly set force_delete
# client.agents.delete(agent_id="71f6a4be-7131-4b0e-8a4d-dae6db40850a", force_delete=True)

# Real-time voice: start outbound call (uses your attached Twilio number to call to_phone_number with the given agent)
# Replace +1234567890 with the number to call
result = client.start(
    agent_id="13de9c15-bba1-4c81-afee-9ce44aea2bfe",
    to_phone_number="+919408393005",
)
print(f"Call started: {result}")

# Optional: stop the call (use call_sid and from_phone_number from start() response, or leave blank to use last call)
# client.stop()