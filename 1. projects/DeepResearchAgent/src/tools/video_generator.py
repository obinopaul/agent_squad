import json5
from typing import Tuple, Optional
import base64
import os
from PIL import Image
import asyncio

from src.tools import AsyncTool, ToolResult
from src.models import ChatMessage, model_manager
from src.logger import logger
from src.registry import TOOL
from src.config import config


OPTIMIZE_PROMPT_INSTRUCTION = """
You are an expert in generating optimized prompts for video generation tasks.
Your task is to take a given prompt and an image reference and generate an optimized version of it that is more suitable for video generation.
Use your imagination and provide as detailed a description as possible. Be sure not to miss any details.

Original prompt: {prompt}

Provide the optimized prompt text as a string without any additional text or formatting.
"""

_GENEATOR_DESCRIPTION = """
You are an advanced video generation model capable of creating high-quality videos based on textual prompts and images.
"""

class OptimizedPromptTool(AsyncTool):
    """Tool for generating optimized search queries."""
    name: str = "optimize_prompt_tool"
    description: str = """Generates an optimized prompt for video generation based on a given prompt and an image."""

    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The original prompt for video generation.",
            },
            "optimized_prompt": {
                "type": "string",
                "description": "The optimized prompt generated for video generation.",
            },
            "image_path": {
                "type": "string",
                "description": "(Optional) Absolute path of the image that be used as a reference for video generation. If not provided, the tool will only use the prompt.",
                "nullable": True,
            },
        },
        "required": ["prompt", "optimized_prompt"],
        "additionalProperties": False,
    }
    output_type = "any"

    async def forward(self, prompt: str, optimized_prompt: str, image_path: Optional[str] = None) -> str:
        """Generate an optimized prompt for video generation."""
        return optimized_prompt

@TOOL.register_module(name="video_generator_tool")
class VideoGeneratorTool(AsyncTool):
    name: str = "video_generator_tool"
    description: str = "This tool generates a video based on a provided prompt and an image reference."

    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The provided prompt for video generation. This should be a detailed description of the video you want to create.",
            },
            "save_name": {
                "type": "string",
                "description": "The name to save the generated video file as. If not provided, a default name will be used.",
                "default": "generated_video.mp4",
            },
            "image_path": {
                "type": "string",
                "description": "(Optional) Absolute path of the image that be used as a reference for video generation. If not provided, the tool will only use the prompt.",
                "nullable": True,
            },
        },
        "required": ["prompt", "save_name"],
    }
    output_type = "any"

    def __init__(self,
                 *args,
                 analyzer_model_id: Optional[str] = None,
                 predict_model_id: Optional[str] = None,
                 fetch_model_id: Optional[str] = None,
                 **kwargs):

        super(VideoGeneratorTool, self).__init__()

        self.analyzer_model_id = analyzer_model_id
        self.predict_model_id = predict_model_id
        self.fecth_model_id = fetch_model_id
        self.analyzer_model = model_manager.registed_models[self.analyzer_model_id]
        self.predict_model = model_manager.registed_models[self.predict_model_id]
        self.fetch_model = model_manager.registed_models[self.fecth_model_id]

    async def forward(self,
                      prompt: str,
                      save_name,
                      image_path: Optional[str] = None, ) -> ToolResult:
        """Generate a video based on the provided prompt and image."""

        if not prompt:
            raise ValueError("Prompt is required for video generation.")

        # Generate an optimized prompt using the analyzer model
        optimized_prompt = await self._generate_optimized_prompt(prompt, image_path)

        if not optimized_prompt:
            logger.warning("Failed to generate an optimized prompt, using the original prompt.")
            optimized_prompt = prompt

        # Generate the image using the generator model
        result = await self._generate_video(optimized_prompt, save_name, image_path)
        return result

    async def _generate_optimized_prompt(self, prompt: str, image_path: Optional[str] = None) -> str:
        try:
            prompt = OPTIMIZE_PROMPT_INSTRUCTION.format(prompt=prompt)

            content = [
                {"type": "text", "text": prompt},
            ]

            if image_path is not None:
                content.append(
                    {
                        "type": "image",
                        "image": Image.open(image_path),
                    }
                )

            messages = [
                {"role": "user", "content": content}
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
                res = f"VideoGeneratorTool failed to generate an optimized prompt: {response}"
                logger.warning(res)
                return prompt

            if not optimized_prompt:
                res = f"VideoGeneratorTool returned an empty optimized prompt."
                logger.warning(res)
                return prompt

            logger.info(f"VideoGeneratorTool generated optimized query: {optimized_prompt}")

            return optimized_prompt
        except Exception as e:
            res = f"VideoGeneratorTool failed to generate an optimized prompt: {e}"
            logger.error(res)
            return prompt

    async def _generate_video(self,
                              prompt: str,
                              save_name: str = "generated_video.mp4",
                              image_path = None) -> ToolResult:

        prompt = _GENEATOR_DESCRIPTION + "\n" + prompt

        # Use the generator model to create the image
        try:
            # Veo3 Predict
            response = self.predict_model(
                prompt=prompt,
                image=image_path,  # Optional image reference
            )
            name = response
            logger.info(f"Veo3 Predict operation name: {name}.")

            video_data = None
            while video_data is None:
                try:
                    # Veo3 Fetch
                    response = model_manager.registed_models["veo3-fetch"](
                        name=name,
                    )
                    video_data = base64.b64decode(response)
                except Exception as e:
                    logger.warning(f"Failed to fetch video data: {e}, retrying in 60 seconds...")
                    await asyncio.sleep(60)  # Wait for 60 seconds before retrying

            if video_data:
                save_path = os.path.join(config.exp_path, save_name)
                with open(save_path, "wb") as f:
                    f.write(video_data)
                output = f"Video generated successfully and saved as {save_path}."
                return ToolResult(output=output, error=None)
            else:
                error_message = "Video generation returned no response."
                logger.error(error_message)
                return ToolResult(output=None, error=error_message)

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return ToolResult(output=None, error=str(e))