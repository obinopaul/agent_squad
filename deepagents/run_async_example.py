import asyncio
import os
from typing import Literal, Any
from dotenv import load_dotenv
load_dotenv()

# For a real-world scenario, you would use a library like python-dotenv
# to load your API keys from a .env file.
# from dotenv import load_dotenv
# load_dotenv()


# This async runner for deepagents examples is intended to be run from the
# home directory of the project. It demonstrates how to run agents
# asynchronously and connect to cloud tools.

async def run_tavily_example():
    """
    Demonstrates creating a deep agent with an async tool (Tavily Search).
    This agent can perform research and stream its results back.
    """
    print("\n--- Running Async Tavily Research Agent Example ---")
    os.environ['TAVILY_API_KEY'] == os.getenv('TAVILY_API_KEY')
    # Check for the required API key
    if "TAVILY_API_KEY" not in os.environ:
        print("🛑 TAVILY_API_KEY environment variable not set. Skipping this example.")
        return

    # Import here to ensure relative imports work correctly when run from the project root
    from deepagents import create_deep_agent
    from tavily import AsyncTavilyClient

    # 1. Initialize the async client for the tool
    tavily_async_client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    # 2. Define an async tool for the agent to use
    async def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
    ) -> list[dict[str, Any]]:
        """Run an async web search using Tavily."""
        print(f"\n🔎 Searching for: '{query}'...")
        return await tavily_async_client.search(
            query,
            max_results=max_results,
            search_depth="advanced",
            topic=topic,
        )

    # 3. Define the instructions for the agent
    research_instructions = """
    You are an expert researcher. Your job is to conduct a thorough web search
    on the user's query and then provide a concise, clear summary of your findings.
    """

    # 4. Create the deep agent
    agent = create_deep_agent(
        tools=[internet_search],
        instructions=research_instructions,
    )

    # 5. Invoke the agent asynchronously and stream the results
    print("\n🚀 Invoking agent and streaming results...\n")
    async for chunk in agent.astream_events(
        {"messages": [{"role": "user", "content": "What is LangGraph and how does it relate to Deep Agents?"}]},
        version="v1"
    ):
        kind = chunk["event"]
        if kind == "on_chat_model_stream":
            print(chunk["data"]["chunk"].content, end="", flush=True)   
        elif kind == "on_tool_end":
            print(f"\n✅ Tool '{chunk['name']}' finished.")
            # Optionally print tool output for debugging
            # print(chunk['data'].get('output'))
            
    print("\n\n--- Tavily Example Finished ---\n")


async def run_mcp_tool_example():
    """
    Demonstrates integrating a deep agent with tools from a live MCP server
    using the langchain-mcp-adapters library.
    """
    print("\n--- Running MCP (Model Context Protocol) Adapters Example ---")

    # This example requires a running MCP server.
    # Save the code below as `math_mcp_server.py` in the same directory and run `python math_mcp_server.py`
    #
    # --- math_mcp_server.py ---
    # from mcp.server.fastmcp import FastMCP
    # 
    # mcp = FastMCP("Math")
    # 
    # @mcp.tool()
    # def add(a: int, b: int) -> int:
    #     \"\"\"Add two numbers\"\"\"
    #     return a + b
    # 
    # @mcp.tool()
    # def multiply(a: int, b: int) -> int:
    #     \"\"\"Multiply two numbers\"\"\"
    #     return a * b
    # 
    # if __name__ == "__main__":
    #     print("Starting Math MCP server via stdio...")
    #     mcp.run(transport="stdio")
    # --------------------------

    # 1. Import necessary components
    from deepagents import create_deep_agent
    from pathlib import Path

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        print("🛑 `langchain-mcp-adapters` is not installed.")
        print("Please run `pip install langchain-mcp-adapters` to run this example.")
        return

    # 2. Configure the connection to the MCP server
    # We use an absolute path to ensure the agent can find the server script.
    math_server_script_path = os.path.abspath(Path(__file__).parent / "math_mcp_server.py")
    
    if not os.path.exists(math_server_script_path):
        print(f"🛑 MCP server script not found at: {math_server_script_path}")
        print("Please save the server code from the comments into this file to run the example.")
        return

    mcp_client = MultiServerMCPClient(
        {
            "math_server": {
                "transport": "stdio",
                "command": "python",
                "args": [math_server_script_path],
            }
        }
    )

    # mcp_client = MultiServerMCPClient(
    #     {
    #         "my_cloud_server": {
    #             "transport": "streamable_http",
    #             "url": "https://your-cloud-mcp-server.com/mcp/",
    #             "headers": {
    #                 "Authorization": "Bearer YOUR_SECRET_TOKEN",
    #                 "X-Custom-Header": "some-value"
    #             },
    #         }
    #     }
    # )

    # 3. Asynchronously fetch the tools from the MCP server.
    # The adapter automatically converts them into LangChain-compatible tools.
    print("🔌 Connecting to MCP server and fetching tools...")
    try:
        mcp_tools = await mcp_client.get_tools()
        if not mcp_tools:
            raise RuntimeError("No tools loaded from MCP server.")
        print(f"✅ Successfully loaded {len(mcp_tools)} tools: {[tool.name for tool in mcp_tools]}")
    except Exception as e:
        print(f"🛑 Failed to connect to or load tools from the MCP server: {e}")
        print("   Please ensure the `math_mcp_server.py` script is running in a separate terminal.")
        return

    # 4. Define instructions for the agent
    mcp_instructions = """
    You are a math expert. Use the provided tools to solve the user's math problem.
    Break the problem down into steps and execute the tools in order.
    """

    # 5. Create the deep agent with the MCP tools
    agent = create_deep_agent(
        tools=mcp_tools,
        instructions=mcp_instructions,
    )

    # 6. Invoke the agent and stream the results to see it use the MCP tools
    print("\n🚀 Invoking agent to solve `(3 + 5) * 12` using MCP tools...\n")
    final_answer = ""
    async for chunk in agent.astream_events(
        {"messages": [{"role": "user", "content": "what is (3 + 5) * 12?"}]},
        version="v1"
    ):
        kind = chunk["event"]
        if kind == "on_chat_model_stream":
            content = chunk["data"]["chunk"].content
            if content:
                print(content, end="", flush=True)
                final_answer += content
        elif kind == "on_tool_start":
            print(f"\n\n🛠️  Calling tool `{chunk['name']}` with args: {chunk['data']['input']['args']}")
        elif kind == "on_tool_end":
            print(f"👍 Tool `{chunk['name']}` finished. Output: {chunk['data']['output']['content']}")

    print(f"\n\nFinal Answer from Agent: {final_answer}")
    print("\n--- MCP Example Finished ---\n")


async def main():
    """Main entry point to run all asynchronous examples."""
    await run_tavily_example()
    # await run_cloud_sse_tool_example()


if __name__ == "__main__":
    print("Starting Deep Agents Async Examples...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")