
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
You are an AI assistant connected to the JPPH document search system.

You can search the authenticated JPPH production application
using the MCP tool search_documents.

Instructions:

1. Use search_documents when the user asks to find JPPH documents.
2. Do not invent document titles, categories or dates.
3. Base your answers on the actual search results.
4. Report the number of matching records returned by JPPH.
5. Present document titles, filenames, categories and dates clearly.
6. If no records are found, explain that no matching results were returned.
7. Do not claim that no records were found merely because
   the extracted document list is empty.
8. Check the returned status and total_results.
   If total_results is null, explain that the search result
   could not be verified.
9. If total_results is zero, report that JPPH returned
   zero matching records.
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

    for attempt in range(5):

        response = await asyncio.to_thread(
            ollama.chat,
            model=MODEL,
            messages=messages,
            tools=tools
        )

        assistant_message = response.message

        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:

            print("\n========== LLAMA RESPONSE ==========\n")
            print(assistant_message.content)
            return

        for tool_call in tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"\nCalling MCP tool: {tool_name}")
            print("Arguments:", arguments)

            if tool_name != "search_documents":
                tool_output = {
                    "status": "error",
                    "message": "Tool not authorised by this client."
                }

            else:

                try:
                    result = await session.call_tool(
                        tool_name,
                        arguments
                    )

                    tool_output = extract_tool_text(result)
                    print("\n========== RAW MCP TOOL RESULT ==========\n")
                    print(tool_output)
                    print("\n=========================================\n")
                    

                    if result.isError:
                        tool_output = {
                            "status": "error",
                            "message": tool_output
                        }

                except Exception as error:

                    tool_output = {
                        "status": "error",
                        "message": str(error)
                    }

            if not isinstance(tool_output, str):
                tool_output = json.dumps(
                    tool_output,
                    ensure_ascii=False
                )

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": tool_output
            })

    print("Maximum tool-calling iterations reached.")


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
