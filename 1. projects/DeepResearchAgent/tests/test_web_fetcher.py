import argparse
import os
import asyncio
import sys
from pathlib import Path
from mmengine import DictAction

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.logger import logger
from src.config import config
from src.registry import TOOL

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

if __name__ == "__main__":

    # Parse command line arguments
    args = parse_args()

    # Initialize the configuration
    config.init_config(args.config, args)

    # Initialize the logger
    logger.init_logger(log_path=config.log_path)
    logger.info(f"| Logger initialized at: {config.log_path}")
    logger.info(f"| Config:\n{config.pretty_text}")

    # Registed tools
    logger.info(f"| {TOOL}")

    web_fetcher_tool_config = config.web_fetcher_tool_config
    web_fetcher_tool = TOOL.build(web_fetcher_tool_config)

    url = "https://www.quora.com/If-Eliud-Kipchoge-can-maintain-such-a-fast-pace-over-26-2-miles-why-can-t-he-manage-to-break-the-single-mile-world-record"

    content = asyncio.run(web_fetcher_tool.forward(url))
    print(content)