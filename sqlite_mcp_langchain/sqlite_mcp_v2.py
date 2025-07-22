import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt.chat_agent_executor import create_tool_calling_executor
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv('D:/mcp/langchain-mcpadapter-sqlite/sqlite_mcp_langchain/.env')
print("Environment variables loaded from .env file")

# Initialize model and server parameters
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.environ["GOOGLE_API_KEY"])
server_params = StdioServerParameters(
    command="uv",
    args=[
        "--directory",
        "D:/mcp/mcp-sqlite-server/servers-archived/src/sqlite",
        "run",
        "mcp-server-sqlite",
        "--db-path",
        "D:/mcp/mcp-sqlite-server/database.db",
    ],
)

async def process_query(agent_executor, query):
    result = await agent_executor.ainvoke({"messages": [{"role": "user", "content": query}]})

    # If the result is an AIMessage object, return its content
    if hasattr(result, "content"):
        return result.content

    # If it's a dict with 'messages', try to extract the last one
    if isinstance(result, dict) and "messages" in result:
        messages = result["messages"]
        if isinstance(messages, list) and messages and hasattr(messages[-1], "content"):
            return messages[-1].content

    # Fallback
    return str(result)
  # AIMessage object has a `.content` attribute


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            # Correct function call from langgraph.prebuilt
            agent_executor = create_tool_calling_executor(model=model, tools=tools)

            print("SQLite Database Assistant (type 'exit' to quit)")

            while True:
                query = input("\nEnter your query: ").strip()
                if query.lower() == 'exit':
                    break
                if not query:
                    continue

                print("\nProcessing...\n")
                try:
                    response = await process_query(agent_executor, query)
                    print(f"\nAnswer: {response}")
                except Exception as e:
                    print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())