#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Module 2: AI APIs & Ingestion Handling Verification
Component: Dynamic Terminal User Interaction for DeepSeek Cloud Endpoint
"""

import os
import sys
from openai import OpenAI
from openai import RateLimitError, APIConnectionError, AuthenticationError
from dotenv import load_dotenv

# Quietly read local infrastructure secrets out of your workspace .env file
load_dotenv()

def execute_dynamic_deepseek_assistant():
    # Retrieve credentials securely from operating system runtime variables
    api_key_env = os.getenv("DEEPSEEK_API_KEY")

    # === DEBUGGING SUITE FOR API KEY VERIFICATION ===
    print("\n" + "[DEBUG]" * 5)
    print(f"Data Type detected : {type(api_key_env)}")
    print(f"Raw Variable Value : {repr(api_key_env)}") # repr() reveals hidden spaces or newlines
    
    if api_key_env is not None:
        print(f"Total Character Count: {len(api_key_env)} characters")
        print(f"Starts with 'sk-'    : {api_key_env.startswith('sk-')}")
    else:
        print("CRITICAL: The variable is None. Python cannot find your .env file or the key name inside it.")
    print("[DEBUG]" * 5 + "\n")
    # ===============================================


    # Intercept runtime execution if environment variables are missing
    if not api_key_env:
        print("\n[FAIL] Configuration Exception: 'DEEPSEEK_API_KEY' missing from your local .env file.", file=sys.stderr)
        print("       Please ensure the student has populated their .env configuration file.", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize the client targeting the correct, official DeepSeek server endpoint bus
        client = OpenAI(
            base_url="https://deepseek.com",  # [CORRECTED] Swapped from public site to API gateway
            api_key=api_key_env
        )

        print("=" * 65)
        print("         DEEPSEEK CLOUD INTEGRATION ACTIVE [DYNAMIC INTERFACE]     ")
        print("=" * 65)
        print("[*] Target Deployment Endpoint: https://deepseek.com")
        print("[*] Target Computational Engine: deepseek-flash")
        print("[*] Instructions: Type your question below and press Enter.")
        print("[*] Operations: Type 'exit' to terminate the current execution loop.\n")

        # Capture dynamic natural language intent or content from the terminal prompt
        user_query = input("What would you like to ask DeepSeek? ").strip()

        # Graceful validation check to avoid passing blank payloads across the network perimeter
        if not user_query or user_query.lower() == 'exit':
            print("[*] Deactivating active session connection loop. Goodbye.")
            return

        print("\n[*] Packing token structures and dispatching secure HTTP POST payload...")

        # Fire synchronous cloud completion request loops using DeepSeek's optimized engine
        response = client.chat.completions.create(
            model="deepseek-flash",  # Active model string
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional logistics and system integration assistant."
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.8,
        )

        # Parse the structured JSON response dictionary down to the text choice array
        ai_reply = response.choices[0].message.content

        print("\n" + "=" * 65)
        print("                        DEEPSEEK SYSTEM RESPONSE                  ")
        print("=" * 65)
        print(ai_reply)
        print("=" * 65)
        print("[PASS] Dynamic cloud workflow verified successfully.\n")

    except RateLimitError:
        print("\n[FAIL] Gateway Exception: 429 - Your free 5 million token promotional trial balance has been exhausted.", file=sys.stderr)
    except AuthenticationError:
        print("\n[FAIL] Security Clearance Exception: Key rejected by validation gates. Double-check your copied string.", file=sys.stderr)
    except APIConnectionError:
        print("\n[FAIL] Network Failure: Infrastructure unreachable. Verify your base_url configuration and internet status.", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n\n[WAKE HALT] Loop interrupted by trainer cancel command. Closing session cleanly.")
    except Exception as err:
        print(f"\n[FAIL] System Error: Unexpected pipeline break: {err}", file=sys.stderr)

if __name__ == "__main__":
    execute_dynamic_deepseek_assistant()
