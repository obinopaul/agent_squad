from src.tools import AsyncTool, ToolResult
from src.models import Model
from src.tools.markdown.mdconvert import MarkitdownConverter
from src.registry import TOOL



_FILE_READER_DESCRIPTION = """Call this tool to read a file as markdown.
This tool handles the following file extensions: [".html", ".htm", ".xlsx", ".pptx", ".wav", ".mp3", ".m4a", ".flac", ".pdf", ".docx", ".pdb", '.zip'], and all other types of files.
* The file_path should be a valid absolute path to the file or a web url you want to read.
* If the file is an image, use the `deep_analyzer` tool instead!
"""

@TOOL.register_module(name="file_reader_tool", force=True)
class FileReaderTool(AsyncTool):
    name: str = "file_reader_tool"
    description: str = _FILE_READER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file you want to read as text. Must be a '.obj' file, like '.pdf'.",
            },
        },
        "required": ["file_path"],
        "additionalProperties": False,
    }
    output_type = "any"

    def __init__(self, text_limit: int = 50000):
        super().__init__()
        self.text_limit = text_limit

        self.converter: MarkitdownConverter = MarkitdownConverter(
            use_llm=False,
            model_id="gpt-4.1",
            timeout = 30
        )

    async def forward(self,
                file_path: str) -> ToolResult:
        """Read a file and return its content as text."""

        try:
            result = self.converter.convert(file_path)
        except Exception as e:
            return ToolResult(
                output=None,
                error=f"Error reading file {file_path}: {str(e)}"
            )

        result = ToolResult(
            output=result.text_content,
            error=None
        )

        return result