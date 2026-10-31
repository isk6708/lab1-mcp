#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Module 2: Local AI API & Ingestion Handling Verification
Component: Dynamic Terminal User Input Interface
"""

import sys
from openai import OpenAI
from openai import APIConnectionError

def run_dynamic_assistant():
    try:
        # Initialize the client package targeting the local hardware framework bus
        client = OpenAI(
            base_url="http://localhost:11434/v1",  # Local Ollama port endpoint
            api_key="ollama"                       # Bypasses authentication checks
        )

        print("=" * 60)
        print("         DYNAMIC LOCAL AI ASSISTANT RUNTIME ACTIVE          ")
        print("=" * 60)
        print("[*] Engine Status: Llama3.2 pipeline active offline.")
        print("[*] Instructions: Type your question below and press Enter.")
        print("[*] To close the application, press Ctrl+C or type 'exit'.\n")

        # Capture dynamic natural language intent from the terminal user prompt
        user_query = input("What would you like to ask the AI? ").strip()

        # Graceful exit handling if user explicitly wants to quit
        if user_query.lower() == 'exit' or not user_query:
            print("[*] Deactivating assistant session cycle. Goodbye.")
            return

        print("\n[*] Processing token payloads through local inference tracks...")

        # Execute the dynamic completion loop matching Chapter 1 schema
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional enterprise database and integration assistant."
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.8,
        )

        # Safely extract and parse the nested text response array out to the user
        ai_reply = response.choices[0].message.content

        print("\n" + "=" * 60)
        print("                      ASSISTANT RESPONSE                          ")
        print("=" * 60)
        print(ai_reply)
        print("=" * 60)
        print("[PASS] Dynamic interaction loop executed successfully.\n")

    except APIConnectionError:
        print("\n[FAIL] Connection Error: Ollama is not running. Verify the application is active in your system tray.", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n\n[WAKE HALT] Execution interrupted by trainer command signal. Exiting.")
    except Exception as err:
        print(f"\n[FAIL] Pipeline Execution Exception: {err}", file=sys.stderr)

if __name__ == "__main__":
    run_dynamic_assistant()
