_base_ = './base.py'

# General Config
tag = "main"
concurrency = 1
workdir = "workdir"
log_path = "log.txt"
save_path = "dra.jsonl"
use_local_proxy = False # True for local proxy, False for public proxy

use_hierarchical_agent = True

deep_researcher_agent_config = dict(
    type="deep_researcher_agent",
    name="deep_researcher_agent",
    model_id="claude-3.7-sonnet-thinking",
    description = "A deep researcher agent that can conduct extensive web searches.",
    max_steps = 3,
    template_path = "src/agent/deep_researcher_agent/prompts/deep_researcher_agent.yaml",
    provide_run_summary = True,
    tools = ["deep_researcher_tool", "python_interpreter_tool"],
)

deep_analyzer_agent_config = dict(
    type="deep_analyzer_agent",
    name="deep_analyzer_agent",
    model_id="claude-3.7-sonnet-thinking",
    description = "A deep analyzer agent that can perform systematic, step-by-step analysis.",
    max_steps = 3,
    template_path = "src/agent/deep_analyzer_agent/prompts/deep_analyzer_agent.yaml",
    provide_run_summary = True,
    tools = ["deep_analyzer_tool", "python_interpreter_tool"],
)

browser_use_agent_config = dict(
    type="browser_use_agent",
    name="browser_use_agent",
    model_id="gpt-4.1",
    description = "A browser use agent that can search relevant web pages and interact with them.",
    max_steps = 5,
    template_path = "src/agent/browser_use_agent/prompts/browser_use_agent.yaml",
    provide_run_summary = True,
    tools = ["auto_browser_use_tool", "python_interpreter_tool"],
)

planning_agent_config = dict(
    type="planning_agent",
    name="planning_agent",
    model_id="claude-3.7-sonnet-thinking",
    description = "A planning agent that can plan the steps to complete the task.",
    max_steps = 20,
    template_path = "src/agent/planning_agent/prompts/planning_agent.yaml",
    provide_run_summary = True,
    tools = ["planning_tool"],
    managed_agents = ["deep_analyzer_agent", "browser_use_agent", "deep_researcher_agent"]
)

agent_config = planning_agent_config