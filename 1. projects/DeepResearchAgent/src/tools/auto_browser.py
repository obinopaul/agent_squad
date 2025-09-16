import os
import subprocess
import atexit
import signal
from dotenv import load_dotenv
load_dotenv(verbose=True)

from browser_use import Agent

from src.tools import AsyncTool, ToolResult
from src.tools.browser import Controller
from src.utils import assemble_project_path
from src.registry import TOOL
from src.models import model_manager

@TOOL.register_module(name="auto_browser_use_tool", force=True)
class AutoBrowserUseTool(AsyncTool):
    name = "auto_browser_use_tool"
    description = "A powerful browser automation tool that allows interaction with web pages through various actions. Automatically browse the web and extract information based on a given task."
    parameters = {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The task to perform"
            },
        },
        "required": ["task"],
    }
    output_type = "any"

    def __init__(self,
                 model_id: str = "gpt-4.1",
                 ):

        super(AutoBrowserUseTool, self).__init__()

        self.model_id = model_id
        self.http_server_path = assemble_project_path("src/tools/browser/http_server")
        self.http_save_path = assemble_project_path("src/tools/browser/http_server/local")
        os.makedirs(self.http_save_path, exist_ok=True)

        self._init_pdf_server()

    def _init_pdf_server(self):

        server_proc = subprocess.Popen(
            ["python3", "-m", "http.server", "8080"],
            cwd=self.http_server_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=None
        )

        @atexit.register
        def shutdown_server():
            print("Shutting down http.server...")
            try:
                server_proc.send_signal(signal.SIGTERM)
                server_proc.wait(timeout=5)
            except Exception as e:
                print("Force killing server...")
                server_proc.kill()

    async def _browser_task(self, task):
        controller = Controller(http_save_path=self.http_save_path)

        assert self.model_id in ['gpt-4.1'], f"Model should be in [gpt-4.1, ], but got {self.model_id}. Please check your config file."

        if "langchain" not in self.model_id:
            model_id = f"langchain-{self.model_id}"
        else:
            model_id = self.model_id

        model = model_manager.registed_models[model_id]

        browser_agent = Agent(
            task=task,
            llm=model,
            enable_memory=False,
            controller=controller,
            page_extraction_llm=model,
        )

        history = await browser_agent.run(max_steps=50)
        contents = history.extracted_content()
        return "\n".join(contents)

    async def forward(self, task: str) -> ToolResult:
        """
        Automatically browse the web and extract information based on a given task.

        Args:
            task: The task to perform
        Returns:
            ToolResult with the task result
        """
        result = await self._browser_task(task)
        return ToolResult(output=result, error=None)