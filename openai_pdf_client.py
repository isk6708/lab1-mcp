
import os
import sys
import json
import asyncio

from dotenv import load_dotenv
from openai import OpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ==================================================
# 1. LOAD CONFIGURATION
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("AI_PROVIDER_API_KEY")

if not API_KEY:
    raise ValueError(
        "AI_PROVIDER_API_KEY is missing from the .env file."
    )

MODEL = "gpt-4o-mini"

openai_client = OpenAI(api_key=API_KEY)


# ==================================================
# 2. CONFIGURE PDF MCP SERVER
# ==================================================

PDF_SERVER_PATH = os.path.join(
    BASE_DIR,
    "pdf_mcp_server.py"
)

if not os.path.isfile(PDF_SERVER_PATH):
    raise FileNotFoundError(
        f"PDF MCP Server not found: {PDF_SERVER_PATH}"
    )

server_parameters = StdioServerParameters(
    command=sys.executable,
    args=[PDF_SERVER_PATH],
    env=os.environ.copy()
)


# ==================================================
# 3. CONVERT MCP TOOLS TO OPENAI FUNCTION TOOLS
# ==================================================

def convert_mcp_tools_to_openai(mcp_tools):

    openai_tools = []

    for tool in mcp_tools:

        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema
            }
        })

    return openai_tools


# ==================================================
# 4. SYSTEM INSTRUCTIONS
# ==================================================


SYSTEM_PROMPT = """
You are an intelligent PDF document research assistant.

Your answers must be based on the actual contents of the PDF.

FOLLOW THIS WORKFLOW:

STEP 1 - SEARCH

When a user asks a question about the book, use
search_pdf_by_keyword to locate relevant pages.

For questions about the intended audience, search using:
"Who this book is for"

STEP 2 - READ

When the search tool identifies relevant pages, you MUST
call read_pdf_page using the page number returned by the search.

Do not answer based only on a matching heading.

STEP 3 - ANALYSE

Read the retrieved page content carefully.

Identify the information that directly answers the question.

If the section continues onto another page, search for
additional relevant pages and retrieve them as necessary.

STEP 4 - ANSWER

Provide a clear and informative answer.

Include:
- The intended audience.
- Existing knowledge or prerequisites.
- What readers will learn.
- Relevant page references.

Only include information supported by the PDF.

Do not invent information or make assumptions.

Do not reproduce lengthy passages from the book.
Summarize the information in your own words.

If the document does not contain sufficient information,
explain the limitation clearly.
"""



# ==================================================
# 5. PROCESS USER QUESTIONS
# ==================================================

async def process_question(session, openai_tools, question):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # Allow multiple tool-call rounds.
    for round_number in range(5):

        print(
            f"\n[OPENAI] Processing round "
            f"{round_number + 1}..."
        )

        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=1000
        )

        assistant_message = response.choices[0].message

        # ------------------------------------------
        # No tool call: display final AI response
        # ------------------------------------------

        if not assistant_message.tool_calls:

            print("\n" + "=" * 55)
            print("AI ASSISTANT RESPONSE")
            print("=" * 55)

            print(assistant_message.content or "")

            print("=" * 55)

            return

        # Preserve assistant tool-call message.
        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        # ------------------------------------------
        # Execute requested MCP tools
        # ------------------------------------------

        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            try:

                arguments = json.loads(
                    tool_call.function.arguments or "{}"
                )

                # Diagnostic output.
                print("\n[OPENAI TOOL CALL]")
                print(f"Tool: {tool_name}")
                print(
                    "Arguments:",
                    json.dumps(arguments, indent=2)
                )

                # Execute MCP tool.
                tool_result = await session.call_tool(
                    tool_name,
                    arguments=arguments
                )

                if tool_result.is_error:

                    result_text = (
                        "The PDF MCP tool returned an error."
                    )

                else:

                    result_text = "\n".join(
                        item.text
                        for item in tool_result.content
                        if hasattr(item, "text")
                    )

                    if not result_text:
                        result_text = (
                            "The PDF MCP tool returned no text."
                        )

                # Diagnostic output.
                print("\n[PDF SEARCH RESULT]")
                print(result_text)
                print("\n[END PDF SEARCH RESULT]")

            except Exception as error:

                print(
                    f"\n[TOOL EXECUTION ERROR] {error}",
                    file=sys.stderr
                )

                result_text = (
                    "Unable to execute the PDF search tool: "
                    + str(error)
                )

            # Return MCP result to OpenAI.
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_text
            })

    print(
        "\n[WARNING] Maximum tool-call rounds reached."
    )


# ==================================================
# 6. MAIN APPLICATION
# ==================================================

async def main():

    print("=" * 55)
    print(" PDF AI ASSISTANT")
    print(" OpenAI API + MCP Integration")
    print("=" * 55)

    print(f"\n[*] AI Model: {MODEL}")

    print("\n[*] Starting PDF MCP Server...")

    async with stdio_client(server_parameters) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("[PASS] PDF MCP Server connected.")

            # --------------------------------------
            # Discover available MCP tools
            # --------------------------------------

            mcp_response = await session.list_tools()

            print(
                f"[PASS] {len(mcp_response.tools)} "
                "MCP tool(s) discovered."
            )

            for tool in mcp_response.tools:

                print(f"       - {tool.name}")

            openai_tools = convert_mcp_tools_to_openai(
                mcp_response.tools
            )

            if not openai_tools:
                print("[ERROR] No MCP tools discovered.")
                return

            print("\n[*] OpenAI Assistant is ready.")
            print("Type 'exit' to stop the application.\n")

            # --------------------------------------
            # Interactive conversation
            # --------------------------------------

            while True:

                question = input("You: ").strip()

                if question.lower() in ("exit", "quit"):

                    print("\n[*] Closing PDF AI Assistant.")
                    break

                if not question:
                    continue

                try:

                    await process_question(
                        session,
                        openai_tools,
                        question
                    )

                except Exception as error:

                    print(f"\n[ERROR] {error}")

                print()


# ==================================================
# 7. APPLICATION ENTRY POINT
# ==================================================

if __name__ == "__main__":

    asyncio.run(main())
