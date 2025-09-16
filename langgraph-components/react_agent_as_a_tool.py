# LangChain Python ReAct Agent with Agent Tools
# This example demonstrates how to create a ReAct agent that uses other agents as tools

import os
from typing import Dict, List, Tuple, Any, Optional

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate

# Configure environment variables (use proper environment management in production)
# os.environ["OPENAI_API_KEY"] = "your-api-key"
# os.environ["ANTHROPIC_API_KEY"] = "your-api-key"
# os.environ["TAVILY_API_KEY"] = "your-api-key"

# 1. Create a base class for agent tools
class AgentTool(BaseTool):
    """Tool that uses another agent as its implementation."""
    
    name: str
    description: str
    agent: Any
    
    def _run(self, query: str) -> str:
        """Use the agent to respond to the query."""
        response = self.agent.invoke({"input": query})
        # Extract the final output from the agent's response
        if isinstance(response, dict) and "output" in response:
            return response["output"]
        return str(response)

# 2. Create a specialized agent for financial analysis
def create_financial_analysis_agent():
    """Create a ReAct agent specialized in financial analysis."""
    
    # Create a model for the financial analysis agent
    financial_model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )
    
    # Define tools for the financial analysis agent
    financial_tools = [
        TavilySearchResults(max_results=3),
    ]
    
    # Define a custom prompt for the financial specialist
    financial_prompt = PromptTemplate.from_template(
        """You are a financial analysis specialist. Use your expertise to provide detailed 
        financial insights and analysis.
        
        {format_instructions}
        
        {input}
        {agent_scratchpad}
        """
    )
    
    # Create the financial analysis agent
    financial_agent = create_react_agent(
        financial_model, 
        financial_tools, 
        checkpointer=MemorySaver()
    )
    
    return financial_agent

# 3. Create a specialized agent for technical documentation
def create_technical_docs_agent():
    """Create a ReAct agent specialized in technical documentation."""
    
    # Create a model for the technical documentation agent
    tech_docs_model = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        temperature=0,
    )
    
    # Define tools for the technical documentation agent
    tech_docs_tools = [
        TavilySearchResults(max_results=3),
    ]
    
    # Create the technical documentation agent
    tech_docs_agent = create_react_agent(
        tech_docs_model, 
        tech_docs_tools, 
        checkpointer=MemorySaver()
    )
    
    return tech_docs_agent

# 4. Create the main agent that will use the specialist agents as tools
def create_main_agent():
    """Create the main ReAct agent that uses specialist agents as tools."""
    
    # Create a model for the main agent
    main_model = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
    )
    
    # Create the specialist agents
    financial_agent = create_financial_analysis_agent()
    tech_docs_agent = create_technical_docs_agent()
    
    # Create tools from the specialist agents
    financial_tool = AgentTool(
        name="financial_analysis",
        description="Useful for financial analysis, investment advice, market trends, and economic forecasts. Use this when you need detailed financial expertise.",
        agent=financial_agent
    )
    
    tech_docs_tool = AgentTool(
        name="technical_documentation",
        description="Useful for technical documentation, programming guidance, API usage, and technology explanations. Use this when you need technical expertise.",
        agent=tech_docs_agent
    )
    
    # Add a general search tool
    search_tool = TavilySearchResults(max_results=3)
    
    # Define all tools for the main agent
    main_tools = [financial_tool, tech_docs_tool, search_tool]
    
    # Create the main agent with the specialist agent tools
    main_agent = create_react_agent(
        main_model, 
        main_tools, 
        checkpointer=MemorySaver()
    )
    
    return main_agent

# 5. Create a custom tool that can perform mathematical calculations
@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

# 6. Usage examples
def run_example():
    """Run example queries through the main agent."""
    
    # Create the main agent
    main_agent = create_main_agent()
    
    # Example queries
    queries = [
        "What are the current trends in renewable energy investments?",
        "Explain how to implement WebSockets in Node.js",
        "Compare the pros and cons of using React vs Angular for a financial dashboard"
    ]
    
    # Process each query
    for query in queries:
        print(f"\nProcessing query: {query}")
        
        # Configure thread ID for conversation persistence
        thread_config = {"configurable": {"thread_id": "1"}}
        
        # FIXED: Create a proper message structure
        # Option 1: Use messages format
        messages = [HumanMessage(content=query)]
        result = main_agent.invoke({"messages": messages}, config=thread_config)
        
        # If the above still causes an error, try option 2:
        # result = main_agent.invoke(input={"input": query}, config=thread_config)
        
        # Print the result
        print("\nResult:")
        if isinstance(result, dict):
            if "output" in result:
                print(result["output"])
            elif "messages" in result:
                # Get the last message, which should be the response
                last_message = result["messages"][-1]
                print(last_message.content)
            else:
                print(result)
        else:
            print(result)

# Alternative approach for a more robust solution
def run_example_alternative():
    """Run example queries with better error handling."""
    
    # Create the main agent
    main_agent = create_main_agent()
    
    # Example query
    query = "What are the current trends in renewable energy investments?"
    print(f"\nProcessing query: {query}")
    
    # Configure thread ID
    thread_config = {"configurable": {"thread_id": "1"}}
    
    try:
        # First try with messages
        messages = [HumanMessage(content=query)]
        result = main_agent.invoke({"messages": messages}, config=thread_config)
        print("\nSuccess with messages format!")
    except Exception as e1:
        print(f"Error with messages format: {str(e1)}")
        try:
            # If that fails, try with input
            result = main_agent.invoke({"input": query}, config=thread_config)
            print("\nSuccess with input format!")
        except Exception as e2:
            print(f"Error with input format: {str(e2)}")
            # If both fail, try without config
            try:
                result = main_agent.invoke({"input": query})
                print("\nSuccess without config!")
            except Exception as e3:
                print(f"Error without config: {str(e3)}")
                result = {"error": "All invoke methods failed"}
    
    # Print the result
    print("\nResult:")
    if isinstance(result, dict):
        if "output" in result:
            print(result["output"])
        elif "messages" in result:
            # Get the last message, which should be the response
            last_message = result["messages"][-1]
            print(last_message.content)
        else:
            print(result)
    else:
        print(result)



# Run the example if this script is executed directly
if __name__ == "__main__":
    # Choose which example to run
    run_example()
    # run_example_alternative()  # This will try multiple approaches