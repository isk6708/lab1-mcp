import json
import ollama

# Ensure you have the library installed: pip install ollama
MODEL_NAME = "llama3"  # Or mistral, qwen2.5, etc.

# =====================================================================
# 1. DEMO: Prompt Structure, System Prompts, and User Prompts
# =====================================================================
print("--- 1. Basic Structured Chat ---")

response = ollama.chat(
    model=MODEL_NAME,
    messages=[
        {
            "role": "system",
            "content": "You are a sarcastic AI assistant building a ChatGPT clone. Keep answers brief.",
        },
        {"role": "user", "content": "Why should I learn prompt engineering?"},
    ],
)

print(response["message"]["content"])
print("\n" + "=" * 50 + "\n")


# =====================================================================
# 2. DEMO: Structured Outputs & JSON Mode
# =====================================================================
print("--- 2. Structured Output (JSON Mode) ---")
# This forces the model to return a valid JSON object instead of raw text.

json_prompt = (
    "Analyze the sentiment of this user comment: 'I love this new chat clone, but it crashes sometimes.' "
    "Return a JSON object with two keys: 'sentiment' (string) and 'score' (float between -1 and 1)."
)

json_response = ollama.chat(
    model=MODEL_NAME,
    format="json",  # Enforces JSON mode in Ollama
    messages=[
        {
            "role": "system",
            "content": "You are a data extraction API. You only output valid JSON.",
        },
        {"role": "user", "content": json_prompt},
    ],
)

# Parse and pretty print the result
parsed_json = json.loads(json_response["message"]["content"])
print(json.dumps(parsed_json, indent=2))
print("\n" + "=" * 50 + "\n")


# =====================================================================
# 3. DEMO: Function Calling (Tools)
# =====================================================================
print("--- 3. Tool / Function Calling Structure ---")


# Define a mock Python function the model can "call"
def get_flight_status(flight_number: str):
    if flight_number == "MH370":
        return {"status": "delayed by 2 hours"}
    return {"status": "on time"}


# Define the tool schema so the model knows it exists
flight_tool = {
    "type": "function",
    "function": {
        "name": "get_flight_status",
        "description": "Get the current flight status given a flight number",
        "parameters": {
            "type": "object",
            "properties": {
                "flight_number": {
                    "type": "string",
                    "description": "The flight number, e.g., MH370",
                }
            },
            "required": ["flight_number"],
        },
    },
}

tool_response = ollama.chat(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": "Is flight MH370 on time?"}],
    tools=[flight_tool],  # Pass the tool schema to the model
)

# Check if the model decided it needs to call a function
if "tool_calls" in tool_response["message"]:
    for call in tool_response["message"]["tool_calls"]:
        func_name = call["function"]["name"]
        arguments = call["function"]["arguments"]

        print(f"Model wants to call function: '{func_name}'")
        print(f"With arguments: {arguments}")

        # Execute the actual python function based on LLM decision
        if func_name == "get_flight_status":
            result = get_flight_status(arguments["flight_number"])
            print(f"Executed Function Result: {result}")
else:
    print("Model did not call a function.")
    print(tool_response["message"]["content"])
