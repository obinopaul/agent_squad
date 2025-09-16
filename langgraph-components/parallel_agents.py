import asyncio
import operator
from typing import Annotated, Any, Dict, List, Sequence, TypedDict

# Assuming necessary imports from langchain, etc. are available
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

# Make sure utils.py is accessible with these functions/constants
# from utils import CRITIC_PROMPT, RESEARCHER_PROMPT, WRITER_PROMPT, create_agent_prompt, get_common_tools, get_model
# <<< --- Placeholder for utils for demonstration if needed --- >>>
# Define placeholders if utils.py is not available in this context
def get_model():
    from langchain_openai import ChatOpenAI
    # Ensure OPENAI_API_KEY is set in environment
    return ChatOpenAI(model="gpt-4o", temperature=0)

def get_common_tools():
    # Define some dummy tools or actual tools
    from langchain_core.tools import tool
    @tool
    def dummy_search(query: str) -> str:
        """Simulates searching for information."""
        return f"Search results for: {query}"
    return [dummy_search]

RESEARCHER_PROMPT = "You are a Researcher agent. Your goal is to find and summarize information."
WRITER_PROMPT = "You are a Writer agent. Your goal is to compose text based on information."
CRITIC_PROMPT = "You are a Critic agent. Your goal is to evaluate information and provide critiques."
# <<< --- End Placeholder --- >>>


# For visualization - ensure necessary libraries are installed
from IPython.display import Image, display
# from langgraph.graph.visualization import MermaidDrawMethod # Newer versions might change this import

# --- State Definition ---
class ParallelAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sub_tasks: List[Dict[str, str]]
    results: Annotated[dict, operator.ior]


# --- Node Functions ---

async def split_task(state: ParallelAgentState) -> Dict[str, Any]:
    """Split the input task and assign agents to each sub-task."""
    llm = get_model()
    query = state["messages"][-1].content

    prompt = PromptTemplate(
        template="""You are a task decomposition specialist.
        Given a complex query, break it down into exactly 3 specific sub-tasks that can be executed in parallel by different specialist agents (Researcher, Writer, Critic).
        Each sub-task should be independent and focused on a different aspect suitable for one of the agents.

        Format your response as a comma-separated list of sub-tasks. Ensure each item is distinct and clearly assignable. Example: Task 1, Task 2, Task 3

        Query: {query}
        """,
        input_variables=["query"]
    )

    chain = prompt | llm
    response = await chain.ainvoke({"query": query})
    response_content = response.content.strip()

    # Improved parsing: handle potential numbering, quotes, etc.
    sub_task_strings = [task.strip().strip("'\" .-") for task in response_content.split(',') if task.strip()]

    if len(sub_task_strings) < 3:
         print(f"Warning: LLM returned fewer than 3 tasks ({len(sub_task_strings)}). Raw response: '{response_content}'. Adjusting...")
         # Fallback: Try splitting by newline if comma fails, or use placeholders
         sub_task_strings = [task.strip().strip("'\" .-") for task in response_content.split('\n') if task.strip()]
         if len(sub_task_strings) < 3:
            # Pad with generic tasks if still not enough
            placeholders = [
                f"Generic Task {i+1} based on query: {query}" for i in range(3 - len(sub_task_strings))
            ]
            sub_task_strings.extend(placeholders)

    # Ensure exactly 3 tasks
    sub_task_strings = sub_task_strings[:3]


    agents = ["researcher", "writer", "critic"]
    sub_task_dicts = []
    for i, task_str in enumerate(sub_task_strings):
         sub_task_dicts.append({
             "task": task_str,
             "agent": agents[i % len(agents)] # Assign cyclically
         })


    print(f"--- Split Tasks ---")
    for sub_task in sub_task_dicts:
        print(f"- Task: {sub_task['task']} (Agent: {sub_task['agent']})")
    print("--------------------")


    return {
        "sub_tasks": sub_task_dicts,
        "results": {} # Initialize results dict
    }

# ***************************************************************
# ************ CORE CHANGE IS IN THIS FUNCTION ******************
# ***************************************************************
async def run_agent_for_task(agent_name: str, agent_prompt: str, task: str, initial_messages: Sequence[BaseMessage]) -> Dict[str, Any]:
    """Runs a specific agent for a single task."""
    print(f"--- Running Agent {agent_name.capitalize()} for task: {task} ---")
    tools = get_common_tools()
    llm = get_model()

    # Define the prompt structure for the agent
    # System prompt sets the role and tool usage guidelines
    # MessagesPlaceholder will hold the conversation history/input
    
    agent_prompt_template = ChatPromptTemplate.from_messages([
         SystemMessage(content="""{agent_prompt}
        
        AVAILABLE TOOLS:
        {tools}
        
        TOOL USAGE PROTOCOL:
        - You have access to the following tools: [{tool_names}]
        - BEFORE using any tool, EXPLICITLY state:
        1. WHY you are using this tool
        2. WHAT specific information you hope to retrieve
        3. HOW this information will help solve the task
        
        """),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
    ])
    
    # Create the ReAct agent runnable
    agent_runnable = create_react_agent(llm, tools, prompt=agent_prompt_template)

    # **** THIS IS THE KEY CHANGE ****
    # Construct the input as a list of messages.
    # The main task is provided as the latest HumanMessage.
    # You could include the original query for context if needed, perhaps as an earlier message or part of the system prompt.
    agent_input_messages = [
        # Optional: Include original query for context if helpful
        # HumanMessage(content=f"Original User Query (for context): {initial_messages[0].content}"),
        HumanMessage(content=f"Your specific task is: {task}")
    ]

    # Invoke the agent with the structured input under the 'messages' key
    # 'agent_scratchpad' is handled internally by the ReAct executor
    response = await agent_runnable.ainvoke({'messages': agent_input_messages})
    # ********************************

    agent_output = response.get("output", f"Agent {agent_name} did not produce output.")
    print(f"--- Agent {agent_name.capitalize()} completed task: {task} ---")
    # Optional: Print the actual response content for debugging
    # print(f"--- Agent {agent_name.capitalize()} Response: {agent_output[:200]}... ---") # Print snippet

    return {
        "response": agent_output,
        "agent": agent_name,
        "task": task
    }


async def run_specific_agent_node(state: ParallelAgentState, agent_name: str, agent_prompt: str) -> Dict[str, Any]:
    """Node function for a specific agent type. Runs all tasks assigned to this agent."""
    agent_tasks = [st for st in state['sub_tasks'] if st['agent'] == agent_name]
    if not agent_tasks:
        print(f"--- No tasks for {agent_name.capitalize()} ---")
        return {"results": {}} # Return empty results dict

    initial_messages = state['messages']
    # Run tasks concurrently if multiple are assigned to the same agent node
    tasks_to_run = [
        run_agent_for_task(agent_name, agent_prompt, sub_task['task'], initial_messages)
        for sub_task in agent_tasks
    ]
    results = await asyncio.gather(*tasks_to_run)

    # Prepare results for merging into the main state's 'results' dict
    agent_results = {res["task"]: {"agent": res["agent"], "response": res["response"]} for res in results}

    return {"results": agent_results} # This will be merged using operator.ior


# --- Specific Agent Nodes ---
async def run_researcher_node(state: ParallelAgentState) -> Dict[str, Any]:
    return await run_specific_agent_node(state, "researcher", RESEARCHER_PROMPT)

async def run_writer_node(state: ParallelAgentState) -> Dict[str, Any]:
    return await run_specific_agent_node(state, "writer", WRITER_PROMPT)

async def run_critic_node(state: ParallelAgentState) -> Dict[str, Any]:
    return await run_specific_agent_node(state, "critic", CRITIC_PROMPT)


# --- Join Node ---
async def collect_results(state: ParallelAgentState) -> Dict[str, Any]:
    """Collects results after parallel execution. State merging handles aggregation."""
    print("--- Collecting Results ---")
    # Filter out any tasks that might not have results (shouldn't happen with current logic but good practice)
    valid_results = {task: res for task, res in state.get('results', {}).items() if res and res.get('response')}
    print(f"Aggregated results so far: {valid_results}") # Print the merged results
    print("-------------------------")
    # Update state with only valid results if necessary, though ior should handle merging correctly
    # state['results'] = valid_results # Usually not needed due to ior, but explicit for clarity
    return {} # Return empty dict as state is already merged


# --- Combine Results Node ---
async def combine_results(state: ParallelAgentState) -> Dict[str, List[BaseMessage]]:
    """Combine results from all agents into a final response."""
    llm = get_model()
    original_query = ""
    # Find the first HumanMessage for the original query
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            original_query = msg.content
            break

    if not original_query:
         print("Error: Could not find original query in messages.")
         return {"messages": state["messages"] + [AIMessage(content="Error: Could not reconstruct original query.")]}


    results_summary = "\n\n".join(
        f"--- Sub-Task: {task} ---\nAgent: {result.get('agent', 'N/A')}\nResult:\n{result.get('response', 'No response collected')}"
        for task, result in state.get("results", {}).items()
    )

    print("--- Combining Results ---")
    print(f"Original Query: {original_query}")
    print(f"Results Summary:\n{results_summary}")
    print("-------------------------")


    prompt = PromptTemplate(
        template="""You are a synthesis expert. Combine the findings from different agents to provide a comprehensive and cohesive final answer to the user's original query. Integrate the information logically and address all parts of the initial request. Ensure the final answer is well-structured and directly answers the query.

Original query: {original_query}

Findings from parallel agents:
{results_summary}

Synthesized Answer:""",
        input_variables=["original_query", "results_summary"]
    )

    chain = prompt | llm
    response = await chain.ainvoke({
        "original_query": original_query,
        "results_summary": results_summary
    })

    final_message = AIMessage(content=response.content)

    # Return only the original query and the final synthesized answer for cleaner state
    # Or keep history if needed: return {"messages": state["messages"] + [final_message]}
    original_human_message = next(msg for msg in state["messages"] if isinstance(msg, HumanMessage))
    return {"messages": [original_human_message, final_message]}


# --- Workflow Definition ---
def create_parallel_agent_workflow():
    """Create and return the parallel agent workflow graph."""
    workflow = StateGraph(ParallelAgentState)

    workflow.add_node("split_task", split_task)
    workflow.add_node("researcher", run_researcher_node)
    workflow.add_node("writer", run_writer_node)
    workflow.add_node("critic", run_critic_node)
    workflow.add_node("collect_results", collect_results)
    workflow.add_node("combine_results", combine_results)

    workflow.add_edge(START, "split_task")
    workflow.add_edge("split_task", "researcher")
    workflow.add_edge("split_task", "writer")
    workflow.add_edge("split_task", "critic")
    workflow.add_edge("researcher", "collect_results")
    workflow.add_edge("writer", "collect_results")
    workflow.add_edge("critic", "collect_results")
    workflow.add_edge("collect_results", "combine_results")
    workflow.add_edge("combine_results", END)

    return workflow.compile(checkpointer=MemorySaver())


# --- Example Usage ---
async def run_parallel_example(query: str):
    """Run an example query through the parallel agent workflow."""
    workflow = create_parallel_agent_workflow()

    print("--- Workflow Graph ---")
    try:
        img_data = workflow.get_graph().draw_mermaid_png()
        display(Image(img_data))
    except Exception as e:
        print(f"Could not draw graph: {e}. Ensure graphviz/pydot or mermaid renderer is available.")
    print("----------------------")

    initial_state = {
        "messages": [HumanMessage(content=query)],
    }
    config = {"configurable": {"thread_id": "parallel-thread-example"}} # Use unique ID per run if needed

    print(f"\n--- Running Workflow for Query: '{query}' ---")
    final_state = None
    async for event in workflow.astream(initial_state, config=config):
        # You can inspect events here if needed
        # print(event)
        if event.get('event') == 'on_chain_end' and event.get('name') == 'LangGraph':
            final_state = event.get('data', {}).get('output')
            
    # Fallback if streaming doesn't capture final state as expected
    if not final_state:
        final_state = await workflow.ainvoke(initial_state, config)
        
    print("--- Workflow Execution Complete ---")


    if final_state and "messages" in final_state and len(final_state["messages"]) > 1:
         return final_state["messages"][-1].content # Return the last message (AIMessage)
    elif final_state and "messages" in final_state:
         return f"Workflow finished, but final message structure might be unexpected: {final_state['messages']}"
    else:
        return "Workflow finished, but no final state or messages found."


# --- Main Execution Block ---
if __name__ == "__main__":
    # Example query
    query = "Analyze the potential impact of quantum computing on cybersecurity over the next decade. Discuss threats, opportunities, and mitigation strategies."

    # Run the example using asyncio
    response = asyncio.run(run_parallel_example(query))

    print("\n--- Final Synthesized Response ---")
    print(response)
    print("---------------------------------")