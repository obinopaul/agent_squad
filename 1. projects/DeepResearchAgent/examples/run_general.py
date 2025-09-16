import argparse
import os
import sys
import asyncio
from pathlib import Path
from mmengine import DictAction

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.logger import logger
from src.config import config
from src.models import model_manager
from src.agent import create_agent

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


async def main():
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
    logger.info("| Registed models: %s", ", ".join(model_manager.registed_models.keys()))

    # Create agent
    agent = await create_agent(config)
    logger.visualize_agent_tree(agent)

    # Run example
    # task = "Use the python interpreter tool to calculate 2 + 3 and return the result."
    # task = "Please generate an image of a futuristic city skyline at sunset, with flying cars and neon lights."
    # task = "Please generate a video of a cat playing with a ball of yarn, with a playful and energetic atmosphere."
    task = "Find the 2023 last revision of 'English Wikipedia' with url 'https://en.wikipedia.org/wiki/English_Wikipedia' and return the result."
    res = await agent.run(task)
    logger.info(f"| Result: {res}")

if __name__ == '__main__':
    asyncio.run(main())