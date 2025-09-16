import argparse
import os
import sys
import asyncio
from pathlib import Path
from mmengine import DictAction
import base64

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.logger import logger
from src.config import config
from src.models import model_manager, ChatMessage

def parse_args():
    parser = argparse.ArgumentParser(description='main')
    parser.add_argument("--config", default=os.path.join(root, "configs", "config_general.py"), help="config file path")

    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        help='override some settings in the used config, the key-value pair '
        'in xxx=yyy format will be merged into config file. If the value to '
        'be overwritten is a list, it should be like key="[a,b]" or key=a,b '
        'It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" '
        'Note that the quotation marks are necessary and that no white space '
        'is allowed.')
    args = parser.parse_args()
    return args


async def video_generation():
    # Video Generation with Veo3: Step1: Veo3 Predict, Step2: Veo3 Fetch

    # Veo3 Predict
    response = model_manager.registed_models["veo3-predict"](
        prompt="Please generate a video of a dancing girl.",
    )
    name = response
    logger.info(f"Veo3 Predict operation name: {name}.")

    video_data = None
    while video_data is None:
        try:
            # Veo3 Fetch
            response = model_manager.registed_models["veo3-fetch"](
                # name="projects/veo-ai-video-463310/locations/us-central1/publishers/google/models/veo-3.0-generate-preview/operations/7ed511e2-7aef-4714-952f-e03467db1d4d",
                name=name,
            )
            video_data = base64.b64decode(response)
        except Exception as e:
            logger.warning("Failed to fetch video data. Retrying in 60 seconds...")
            await asyncio.sleep(60)  # Wait for 60 seconds before retrying

    with open("test_case_video.mp4", "wb") as f:
        f.write(video_data)
    logger.info("Video saved as test_case_video.mp4")

if __name__ == "__main__":

    # Parse command line arguments
    args = parse_args()

    # Initialize the configuration
    config.init_config(args.config, args)

    # Initialize the logger
    logger.init_logger(log_path=config.log_path)
    logger.info(f"| Logger initialized at: {config.log_path}")
    logger.info(f"| Config:\n{config.pretty_text}")

    # Registed models
    model_manager.init_models(use_local_proxy=True)
    logger.info("Registed models: %s", ", ".join(model_manager.registed_models.keys()))

    # Test video generation
    # asyncio.run(video_generation())
    #
    # response = model_manager.registed_models["imagen"](
    #     prompt="Generate an image of a futuristic city skyline at sunset.",
    # )
    # img_data = base64.b64decode(response)
    # with open("test_case_image.png", "wb") as f:
    #     f.write(img_data)
    # logger.info("Image saved as test_case_image.png")

    messages = [
        ChatMessage(role="user", content="Riddle solution: 200 coins, 30 face-up, must divide into two piles with equal face-down coins, unable to distinguish coin sides in darkness. Picks 30 coins, flips all, rest 170 untouched. Larger pile has 14 face-down coins. What is the outcome for the adventurer? Number of coins won or if he died."),
    ]

    response = asyncio.run(model_manager.registed_models["o3-deep-research"](
        messages=messages,
    ))
    print(response)
    exit()

    response = asyncio.run(model_manager.registed_models["deepseek-chat"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["deepseek-reasoner"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["o3"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["gpt-4.1"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["claude37-sonnet"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["claude-3.7-sonnet-thinking"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["claude-4-sonnet"](
        messages=messages,
    ))
    print(response)

    response = asyncio.run(model_manager.registed_models["gemini-2.5-pro"](
        messages=messages,
    ))
    print(response)

    # test langchain models
    model = model_manager.registed_models["langchain-gpt-4.1"]
    response = asyncio.run(model.ainvoke("What is the capital of France?"))
    print(response)
