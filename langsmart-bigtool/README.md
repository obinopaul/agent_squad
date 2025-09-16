# langsmart-bigtool

`langsmart-bigtool` is a Python library for creating [LangGraph](https://langchain-ai.github.io/langgraph/) agents that can intelligently select and use tools from large tool registries. It uses a novel two-stage LLM-driven architecture to replace traditional RAG-based tool retrieval with intelligent tool selection.

## Features

- 🧠 **LLM-driven tool selection**: Uses a fast "selector" LLM to intelligently choose relevant tools from large registries
- 🚀 **Two-stage architecture**: Separates tool selection from execution for optimal performance
- 🧰 **Scalable tool access**: Handle hundreds or thousands of tools without overwhelming the main agent
- 🎯 **Dynamic tool binding**: Main agent only receives tools relevant to the specific query
- ⚡ **Optimized performance**: Fast tool selection using lightweight LLMs (GPT-4o-mini, Gemini Flash, etc.)

This library is built on top of [LangGraph](https://github.com/langchain-ai/langgraph), a powerful framework for building agent applications, and comes with out-of-box support for [streaming](https://langchain-ai.github.io/langgraph/how-tos/#streaming), [short-term and long-term memory](https://langchain-ai.github.io/langgraph/concepts/memory/) and [human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/).

## Installation

```bash
pip install langsmart-bigtool
```

## Architecture

The library uses a two-node architecture:

1. **Tool Selector Node**: A fast LLM analyzes the user query and selects 3-10 most relevant tools from the registry
2. **Main Agent Node**: A ReAct agent that uses only the selected tools to execute the task

This approach provides several advantages over traditional RAG-based tool retrieval:
- More nuanced understanding of tool relevance
- Better handling of complex tool relationships
- Reduced context size for the main agent
- Dynamic adaptation to query complexity

## Quickstart

We demonstrate `langsmart-bigtool` by equipping an agent with all functions from Python's built-in `math` library.

```bash
pip install langsmart-bigtool "langchain[openai]"

export OPENAI_API_KEY=<your_api_key>
```

```python
import math
import types
import uuid

from langchain.chat_models import init_chat_model

from langsmart_bigtool import create_agent
from langsmart_bigtool.utils import (
    convert_positional_only_function_to_tool
)

# Collect functions from `math` built-in
all_tools = []
for function_name in dir(math):
    function = getattr(math, function_name)
    if not isinstance(
        function, types.BuiltinFunctionType
    ):
        continue
    # This is an idiosyncrasy of the `math` library
    if tool := convert_positional_only_function_to_tool(
        function
    ):
        all_tools.append(tool)

# Create registry of tools. This is a dict mapping
# identifiers to tool instances.
tool_registry = {
    str(uuid.uuid4()): tool
    for tool in all_tools
}

# Initialize LLMs
selector_llm = init_chat_model("openai:gpt-4o-mini")  # Fast LLM for tool selection
main_llm = init_chat_model("openai:gpt-4o")          # Main LLM for execution

# Create agent with two-stage architecture
builder = create_agent(selector_llm, main_llm, tool_registry)
agent = builder.compile()
```

![Graph diagram](static/img/graph.png)

```python
query = "Use available tools to calculate arc cosine of 0.5."

# Test it out
for step in agent.stream(
    {"messages": query},
    stream_mode="updates",
):
    for _, update in step.items():
        for message in update.get("messages", []):
            message.pretty_print()
```

```
================================== Ai Message ==================================

Selected tools: ['tool_id_123']. Reasoning: Selected acos tool for arc cosine calculation

================================== Ai Message ==================================
Tool Calls:
  acos (call_ynI4zBlJqXg4jfR21fVKDTTD)
 Call ID: call_ynI4zBlJqXg4jfR21fVKDTTD
  Args:
    x: 0.5
================================= Tool Message =================================
Name: acos

1.0471975511965976
================================== Ai Message ==================================

The arc cosine of 0.5 is approximately 1.0472 radians.
```

## How It Works

### 1. Tool Selection Phase

The selector LLM receives:
- The user's query
- A structured manifest of all available tools with descriptions
- Instructions to select 3-10 most relevant tools

Example tool manifest:
```markdown
# Available Tools

## acos
- **ID**: abc-123-def
- **Description**: Return the arc cosine of x, in radians.

## sin  
- **ID**: def-456-ghi
- **Description**: Return the sine of x (measured in radians).

...
```

### 2. Main Agent Phase

The main agent:
- Receives only the selected tools (not the entire registry)
- Uses standard ReAct reasoning with the focused tool set
- Executes the user's request efficiently

## Advanced Usage

### Custom Tool Selection Logic

While the default LLM-driven selection works well, you can customize the selection process:

```python
from langsmart_bigtool.graph import ToolSelectionResponse

def custom_tool_selector(query: str, tool_registry: dict) -> ToolSelectionResponse:
    # Custom logic to select tools based on query
    if "math" in query.lower():
        math_tools = [tid for tid, tool in tool_registry.items() 
                     if hasattr(tool, 'name') and tool.name in ['sin', 'cos', 'tan']]
        return ToolSelectionResponse(
            selected_tools=math_tools[:5],
            reasoning="Selected trigonometric functions for math query"
        )
    # ... more custom logic
```

### Using Different LLMs

You can use different LLMs for different stages:

```python
# Fast, cheap LLM for tool selection
selector_llm = init_chat_model("openai:gpt-4o-mini")

# More capable LLM for main execution  
main_llm = init_chat_model("anthropic:claude-3-sonnet")

# Or use the same LLM for both stages
llm = init_chat_model("openai:gpt-4o")
builder = create_agent(llm, llm, tool_registry)
```

### Large Tool Registries

The architecture scales to handle large tool registries:

```python
# Example with 500+ tools
large_tool_registry = {}

# Add various tool categories
for category in ['math', 'string', 'file', 'network', 'data']:
    category_tools = load_tools_for_category(category)
    for i, tool in enumerate(category_tools):
        large_tool_registry[f"{category}_{i}"] = tool

# The selector will intelligently choose relevant tools
builder = create_agent(selector_llm, main_llm, large_tool_registry)
```

## Migration from RAG-based Version

If you're migrating from the previous RAG-based version:

1. **Update function signature**:
   ```python
   # Old
   builder = create_agent(llm, tool_registry, limit=5)
   
   # New  
   builder = create_agent(selector_llm, main_llm, tool_registry)
   ```

2. **Remove store setup** (no longer needed):
   ```python
   # Old - remove this
   store = InMemoryStore(index={"embed": embeddings, "dims": 1536})
   for tool_id, tool in tool_registry.items():
       store.put(("tools",), tool_id, {"description": f"{tool.name}: {tool.description}"})
   
   # New - not needed
   builder = create_agent(selector_llm, main_llm, tool_registry)
   agent = builder.compile()  # No store parameter
   ```

3. **Benefits of migration**:
   - No need to manage embeddings or vector stores
   - Better tool selection accuracy
   - Faster cold-start performance
   - Easier setup and maintenance

## Related Work

- [Toolshed: Scale Tool-Equipped Agents with Advanced RAG-Tool Fusion and Tool Knowledge Bases](https://doi.org/10.48550/arXiv.2410.14594) - Lumer, E., Subbiah, V.K., Burke, J.A., Basavaraju, P.H. & Huber, A. (2024). arXiv:2410.14594.

- [Graph RAG-Tool Fusion](https://doi.org/10.48550/arXiv.2502.07223) - Lumer, E., Basavaraju, P.H., Mason, M., Burke, J.A. & Subbiah, V.K. (2025). arXiv:2502.07223.

- https://github.com/quchangle1/LLM-Tool-Survey

- [Retrieval Models Aren't Tool-Savvy: Benchmarking Tool Retrieval for Large Language Models](https://doi.org/10.48550/arXiv.2503.01763) - Shi, Z., Wang, Y., Yan, L., Ren, P., Wang, S., Yin, D. & Ren, Z. arXiv:2503.01763.