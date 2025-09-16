_base_ = './base.py'

# General Config
tag = "oai_deep_research-o3"
concurrency = 4
workdir = "workdir"
log_path = "log.txt"
save_path = "dra.jsonl"
use_local_proxy = True # True for local proxy, False for public proxy

use_hierarchical_agent = False

dataset = dict(
    type="gaia_dataset",
    name="2023_all",
    path="data/GAIA",
    split="test",
)

oai_deep_research_tool_config = dict(
    type="oai_deep_research_tool",
    model_id = "o3-deep-research",
)

oai_deep_research_agent_config = dict(
    type="general_agent",
    name="oai_deep_research_agent",
    model_id="gpt-4.1",
    description = "A general agent that can perform deep research using openai's deep research capabilities.",
    max_steps = 20,
    template_path = "src/agent/general_agent/prompts/general_agent.yaml",
    provide_run_summary = True,
    tools = ["oai_deep_research_tool", "deep_analyzer_tool"],
    mcp_tools = [],
)

agent_config = oai_deep_research_agent_config