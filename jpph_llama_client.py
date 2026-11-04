
import asyncio
import json
import sys
from pathlib import Path

import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


BASE_DIR = Path(__file__).resolve().parent.parent

SERVER_PATH = BASE_DIR / "lab1" / "jpph_mcp_server.py"

MODEL = "llama3.2"


SYSTEM_PROMPT = """
You are a JPPH Document Search Assistant.

You help users search documents using the JPPH MCP tools.

IMPORTANT RULES:

1. Use MCP tool results as the only source of document information.
2. Never invent document titles, dates, filenames or categories.
3. Never claim that a successful search failed.
4. Never claim zero results if documents are returned.
5. If total_results is greater than zero, acknowledge the matching records.
6. If a field is null, do not guess its value.
7. Keep responses concise and clear.

The application independently validates MCP results.
Do not override the actual MCP result.
"""


def extract_tool_text(result):

    output = []

    for item in result.content:

        if hasattr(item, "text"):
            output.append(item.text)

    return "\n".join(output)


def convert_mcp_tools(mcp_tools):

    ollama_tools = []

    for tool in mcp_tools:

        ollama_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema
            }
        })

    return ollama_tools


def parse_search_result(raw_text):

    try:
        data = json.loads(raw_text)

        if not isinstance(data, dict):
            raise ValueError("Unexpected MCP response format.")

        return data

    except (json.JSONDecodeError, ValueError) as error:

        return {
            "status": "error",
            "message": f"Unable to parse MCP response: {error}",
            "raw_response": raw_text
        }


def display_search_result(data):

    print("\n========== JPPH SEARCH RESULTS ==========\n")

    status = data.get("status")

    if status != "success":

        print("Search could not be completed.")
        print("Status:", status)
        print("Message:", data.get("message", "No additional information."))
        return

    total = data.get("total_results")
    extracted = data.get("extracted_results", 0)
    documents = data.get("documents", [])

    if not isinstance(documents, list):
        documents = []

    if total == 0:

        print("No matching JPPH records were found.")
        return

    if not isinstance(total, int) or total < 0:

        print("The search result count could not be verified.")
        return

    print(f"Search query       : {data.get('query', '')}")
    print(f"Total records      : {total}")
    print(f"Records extracted  : {extracted}")

    if not documents:

        print("\nNo document details were extracted.")
        return

    print("\nMatching documents:\n")

    for index, document in enumerate(documents, start=1):

        print(f"{index}. {document.get('title') or 'Untitled document'}")
        print(f"   Filename : {document.get('filename') or 'Not available'}")
        print(f"   Category : {document.get('category') or 'Not available'}")
        print(f"   Date     : {document.get('date') or 'Not available'}")

        if document.get("document_path"):
            print(f"   Document : {document['document_path']}")

        print()

    if total > len(documents):

        print(
            f"Note: Showing {len(documents)} extracted documents "
            f"out of {total} matching records."
        )

    print("\n=========================================\n")


async def ask_llama(session, tools, question):

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

    response = await asyncio.to_thread(
        ollama.chat,
        model=MODEL,
        messages=messages,
        tools=tools
    )

    assistant_message = response.message

    tool_calls = assistant_message.tool_calls or []

    if not tool_calls:

        print("\n========== LLAMA RESPONSE ==========\n")
        print(assistant_message.content or "No response from the model.")
        return

    for tool_call in tool_calls:

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        print(f"\nCalling MCP tool: {tool_name}")
        print("Arguments:", arguments)

        if tool_name != "search_documents":

            print("This client only permits the search_documents tool.")
            continue

        try:

            result = await session.call_tool(
                tool_name,
                arguments
            )

            raw_output = extract_tool_text(result)

            print("\n========== RAW MCP TOOL RESULT ==========\n")
            print(raw_output)
            print("\n=========================================\n")

            # Check MCP execution status
            if result.is_error:

                print("MCP reported an execution error.")
                print(raw_output)
                continue

            # Parse JSON returned by MCP
            search_data = parse_search_result(raw_output)

            # Display actual JPPH results
            display_search_result(search_data)

        except Exception as error:

            print("\nMCP execution error:")
            print(str(error))


async def main():

    if not SERVER_PATH.exists():

        print("MCP server file not found:", SERVER_PATH)
        return

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=None
    )

    print("Starting JPPH MCP client...")
    print("Model:", MODEL)

    async with stdio_client(server_parameters) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            available_tools = await session.list_tools()

            tools = convert_mcp_tools(
                available_tools.tools
            )

            print("\nConnected to JPPH MCP server.")

            print("\nAvailable MCP tools:")

            for tool in available_tools.tools:
                print("-", tool.name)

            print("\nJPPH AI Assistant is ready.")
            print("Type 'exit' to stop.")

            while True:

                question = input("\nYou: ").strip()

                if question.lower() in ["exit", "quit"]:
                    break

                if not question:
                    continue

                await ask_llama(
                    session,
                    tools,
                    question
                )


if __name__ == "__main__":
    asyncio.run(main())
