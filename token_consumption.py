
#!/usr/bin/env python3
"""
Course: Building AI Applications Through API and MCP Integration
Module 2: AI APIs & JSON Handling
Lab: Dynamic Terminal User Interaction Loops targeting OpenAI Cloud Endpoints

Features:
- Secure API key retrieval from .env
- Continuous terminal interaction
- Token consumption tracking
- Estimated USD cost calculation
- Persistent local spending tracker
- Local spending threshold of USD 4.50
"""

import os
import sys
import json
from openai import OpenAI
from openai import RateLimitError, APIConnectionError, AuthenticationError
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Configuration
MODEL = "gpt-4o-mini"
SPENDING_LIMIT = 4.50

# Standard GPT-4o-mini text token prices per 1 million tokens
INPUT_PRICE = 0.15
OUTPUT_PRICE = 0.60

USAGE_FILE = "api_usage.json"


def load_usage():
    """Retrieve previously recorded local expenditure."""

    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            print("[WARNING] Usage file unavailable. Starting a new tracker.")

    return {
        "total_cost": 0.0,
        "total_tokens": 0
    }


def save_usage(usage):
    """Persist usage information locally."""

    with open(USAGE_FILE, "w") as file:
        json.dump(usage, file, indent=4)


def calculate_cost(input_tokens, output_tokens):
    """Calculate estimated model consumption cost."""

    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE

    return input_cost + output_cost


def execute_dynamic_cloud_assistant():

    # Retrieve API credentials
    api_key_env = os.getenv("AI_PROVIDER_API_KEY")

    if not api_key_env or api_key_env.startswith(
        "sk-proj-InsertYourActual"
    ):
        print(
            "\n[FAIL] Configuration Exception: "
            "Valid AI_PROVIDER_API_KEY missing from .env.",
            file=sys.stderr
        )
        sys.exit(1)

    # Load persistent expenditure
    usage = load_usage()

    try:

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key_env)

        print("=" * 65)
        print("       OPENAI CLOUD INTEGRATION ACTIVE [DYNAMIC INTERFACE]")
        print("=" * 65)
        print(f"[*] Target Endpoint: OpenAI API")
        print(f"[*] Computational Engine: {MODEL}")
        print(f"[*] Local Spending Threshold: USD {SPENDING_LIMIT:.2f}")
        print(f"[*] Previously Recorded Cost: USD {usage['total_cost']:.6f}")
        print("[*] Type 'exit' to terminate the session.\n")

        # Continuous interaction loop
        while True:

            # Check local spending threshold
            if usage["total_cost"] >= SPENDING_LIMIT:

                print("\n" + "!" * 65)
                print("[HALT] LOCAL SPENDING THRESHOLD REACHED.")
                print(f"Recorded expenditure: USD {usage['total_cost']:.6f}")
                print("Further API requests have been disabled.")
                print("!" * 65)
                break

            # Capture user input
            user_query = input(
                "\nWhat would you like to ask ChatGPT? "
            ).strip()

            if not user_query or user_query.lower() == "exit":
                print("\n[*] Closing active session. Goodbye.")
                break

            print("\n[*] Dispatching API request...")

            # Execute API request
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional logistics and "
                            "geographical data synthesis assistant."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_query
                    }
                ],
                temperature=0.8,
                max_completion_tokens=1000
            )

            # Extract response
            ai_reply = response.choices[0].message.content

            # Extract token metrics
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Calculate estimated expenditure
            request_cost = calculate_cost(
                input_tokens,
                output_tokens
            )

            # Update cumulative expenditure
            usage["total_tokens"] += total_tokens
            usage["total_cost"] += request_cost

            # Persist expenditure
            save_usage(usage)

            # Display response
            print("\n" + "=" * 65)
            print("                  CHATGPT SYSTEM RESPONSE")
            print("=" * 65)
            print(ai_reply)
            print("=" * 65)

            # Display audit logs
            print("[*] AUDIT LOGS")
            print(f"Input Tokens       : {input_tokens}")
            print(f"Output Tokens      : {output_tokens}")
            print(f"Total Tokens       : {total_tokens}")
            print(f"Request Cost       : USD {request_cost:.8f}")
            print("-" * 65)
            print(f"Cumulative Tokens  : {usage['total_tokens']}")
            print(f"Cumulative Cost    : USD {usage['total_cost']:.8f}")
            print(f"Remaining Budget   : USD {max(0, SPENDING_LIMIT - usage['total_cost']):.6f}")
            print("=" * 65)

            if usage["total_cost"] >= SPENDING_LIMIT:
                print("\n[HALT] Local spending threshold reached.")
                break

            print("\n[PASS] Operational cloud workflow completed.")
            # print(f"Raw Response       : {response}")
            print(
                json.dumps(
                    response.model_dump(),
                    indent=4,
                    ensure_ascii=False,
                    default=str
                )
            )

    except RateLimitError as rate_err:
        print(
            f"\n[FAIL] API rate limit or quota error: {rate_err}",
            file=sys.stderr
        )
        print(
            "Check API usage, billing and rate limits.",
            file=sys.stderr
        )

    except AuthenticationError:
        print(
            "\n[FAIL] Authentication Error: Verify your API key.",
            file=sys.stderr
        )

    except APIConnectionError:
        print(
            "\n[FAIL] Network Failure: Check internet connectivity.",
            file=sys.stderr
        )

    except KeyboardInterrupt:
        print("\n\n[HALT] Session interrupted by user.")

    except Exception as err:
        print(
            f"\n[FAIL] Unexpected system error: {err}",
            file=sys.stderr
        )


if __name__ == "__main__":
    execute_dynamic_cloud_assistant()
