import json5
from typing import Tuple, Optional
import base64
import os

from src.tools import AsyncTool, ToolResult
from src.models import ChatMessage, model_manager
from src.logger import logger
from src.registry import TOOL
from src.config import config

OPTIMIZE_PROMPT_INSTRUCTION = """
You are an expert in generating optimized prompts for image generation tasks. 
Your task is to take a given prompt and generate an optimized version of it that is more suitable for image generation.
Use your imagination and provide as detailed a description as possible. Be sure not to miss any details.

Original prompt: {prompt}

Provide the optimized prompt text as a string without any additional text or formatting.
"""

_GENEATOR_DESCRIPTION = """
You are an advanced image generation model. Please generate an image based on the provided prompt.
"""

class OptimizedPromptTool(AsyncTool):
    """Tool for generating optimized search queries."""
    name: str = "optimize_prompt_tool"
    description: str = """Generates an prompt for image generation based on a given query."""

    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The original prompt for image generation.",
            },
            "optimized_prompt": {
                "type": "string",
                "description": "The optimized prompt generated for image generation.",
            },
        },
        "required": ["prompt", "optimized_prompt"],
        "additionalProperties": False,
    }
    output_type = "any"

    async def forward(self, prompt: str, optimized_prompt: str) -> str:
        """Generate an optimized prompt for image generation."""
        return optimized_prompt

@TOOL.register_module(name="image_generator_tool")
class ImageGeneratorTool(AsyncTool):
    name: str = "image_generator_tool"
    description: str = "This tool generates an image based on a given prompt."

    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The provided prompt for image generation.",
            },
            "save_name":{
                "type": "string",
                "description": "The name to save the generated image as. If not provided, a default name will be used.",
                "default": "generated_image.png"
            }
        },
        "required": ["prompt", "save_name"],
    }
    output_type = "any"

    def __init__(self,
                 *args,
                 analyzer_model_id: Optional[str] = None,
                 generator_model_id: Optional[str] = None,
                 **kwargs):

        super(ImageGeneratorTool, self).__init__()

        self.analyzer_model_id = analyzer_model_id
        self.generator_model_id = generator_model_id
        self.analyzer_model = model_manager.registed_models[self.analyzer_model_id]
        self.generator_model = model_manager.registed_models[self.generator_model_id]

    async def forward(self, prompt, save_name) -> ToolResult:
        """Generate an image based on the provided prompt."""
        if not prompt:
            raise ValueError("Prompt is required for image generation.")

        # Generate an optimized prompt using the analyzer model
        optimized_prompt = await self._generate_optimized_prompt(prompt)

        if not optimized_prompt:
            logger.warning("Failed to generate an optimized prompt, using the original prompt.")
            optimized_prompt = prompt

        # Generate the image using the generator model
        result = await self._generate_image(optimized_prompt, save_name)
        return result

    async def _generate_optimized_prompt(self, prompt: str) -> str:
        try:
            prompt = OPTIMIZE_PROMPT_INSTRUCTION.format(prompt=prompt)

            messages = [
                {"role": "user", "content": prompt}
            ]
            messages = [ChatMessage.from_dict(m) for m in messages]  # Convert to ChatMessage format
            tools = [
                OptimizedPromptTool()
            ]

            response = await self.analyzer_model(
                messages=messages,
                tools_to_call_from=tools
            )

            # Extract the query from the tool_call response
            if response and response.tool_calls and len(response.tool_calls) > 0:
                arguments = json5.loads(response.tool_calls[0].function.arguments)
                optimized_prompt = arguments.get("optimized_prompt", "")
            else:
                res = f"ImageGeneratorTool failed to generate an optimized prompt: {response}"
                logger.warning(res)
                return prompt

            if not optimized_prompt:
                res = f"ImageGeneratorTool returned an empty optimized prompt."
                logger.warning(res)
                return prompt

            logger.info(f"ImageGeneratorTool generated optimized query: {optimized_prompt}")

            return optimized_prompt
        except Exception as e:
            res = f"ImageGeneratorTool failed to generate an optimized prompt: {e}"
            logger.error(res)
            return prompt

    async def _generate_image(self, prompt: str, save_name: str = "generated_image.png") -> ToolResult:

        prompt = _GENEATOR_DESCRIPTION + "\n" + prompt

        # Use the generator model to create the image
        try:
            response = self.generator_model(prompt)
            if response:
                image_data = base64.b64decode(response)
                save_path = os.path.join(config.exp_path, save_name)
                with open(save_path, "wb") as f:
                    f.write(image_data)
                output = f"Image generated successfully and saved as {save_path}."
                return ToolResult(output=output, error=None)
            else:
                error_message = "Image generation returned no response."
                logger.error(error_message)
                return ToolResult(output=None, error=error_message)

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return ToolResult(output=None, error=str(e))