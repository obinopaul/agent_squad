web_fetcher_tool_config = dict(
    type="web_fetcher_tool",
)

web_searcher_tool_config = dict(
    type="web_searcher_tool",
    engine="Firecrawl",  # Options: "Firecrawl", "Google", "Bing", "DuckDuckGo", "Baidu"
    retry_delay = 10,
    max_retries = 3,
    lang = "en",
    country = "us",
    num_results = 5,
    fetch_content = True,
    max_length = 4096,
)

deep_researcher_tool_config  = dict(
    type="deep_researcher_tool",
    model_id = "gpt-4.1",
    max_depth = 2,
    max_insights = 20,
    time_limit_seconds = 60,
    max_follow_ups = 3,
)

auto_browser_use_tool_config  = dict(
    type="auto_browser_use_tool",
    model_id="gpt-4.1"
)

deep_analyzer_tool_config  = dict(
    type="deep_analyzer_tool",
    analyzer_model_ids = ["gemini-2.5-pro"],
    summarizer_model_id = "gemini-2.5-pro",
)

# mcp_tools_config = {
#     "mcpServers" :  {
#         # Local stdio server
#         "LocalMCP": {
#             "command": "python",
#             "args": ["src/mcp/server.py"],
#             "env": {"DEBUG": "true"}
#         },
#         # Remote server
#         # "calendar": {
#         #     "url": "https://calendar-api.example.com/mcp",
#         #     "transport": "streamable-http"
#         # }
#     }
# }

mcp_tools_config = dict(
    mcpServers=dict(
        LocalMCP=dict(
            args=[
                'C:/Users/pault/.../server.py',
            ],
            # Use the full, explicit path to the Python executable
            command='C:/Users/pault/anaconda3/envs/app_project/python.exe', # <--- THIS IS THE FIX
            env=dict(DEBUG='true')
        )
    )
)

image_generator_tool_config = dict(
    type="image_generator_tool",
    analyzer_model_id = "o3",
    generator_model_id = "imagen",
)

video_generator_tool_config = dict(
    type="video_generator_tool",
    analyzer_model_id = "o3",
    predict_model_id = "veo3-predict",
    fetch_model_id = "veo3-fetch",
)

file_reader_tool_config = dict(
    type="file_reader_tool"
)

oai_deep_research_tool_config = dict(
    type="oai_deep_research_tool",
    model_id = "o3-deep-research",
)