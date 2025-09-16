from src.tools import AsyncTool, ToolResult
from src.models import model_manager
from src.registry import TOOL
from src.models import ChatMessage, MessageRole

_OAI_DEEP_RESEARCH_DESCRIPTION = """Call this tool to perform deep research using OpenAI's deep research capabilities.
This tool is designed to handle complex queries and provide detailed insights based on the provided query.
"""

@TOOL.register_module(name="oai_deep_research_tool", force=True)
class OAIDeepResearchTool(AsyncTool):
    name: str = "oai_deep_research_tool"
    description: str = _OAI_DEEP_RESEARCH_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query you want to research. This should be a clear and concise question or topic.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }
    output_type = "any"

    def __init__(self, model_id):
        super().__init__()
        self.model = model_manager.registed_models[model_id]

    async def forward(self,
                query: str) -> ToolResult:
        """Perform deep research based on the provided query."""
        try:
            # Use the model to perform deep research

            messages = [
                {
                    "role": MessageRole.USER,
                    "content": query,
                }
            ]
            messages = [ChatMessage(**msg) for msg in messages]

            response = await self.model(messages=messages)
            content = response.content

        except Exception as e:
            return ToolResult(
                output=None,
                error=f"Error performing deep research for query '{query}': {str(e)}"
            )
        result = ToolResult(
            output=content,
            error=None
        )
        return result