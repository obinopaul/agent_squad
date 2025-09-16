import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import asyncio
from dotenv import load_dotenv
load_dotenv(verbose=True)

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.tools.auto_browser import AutoBrowserUseTool
from src.models import model_manager
from src.logger import logger
from src.config import config
from src.utils import assemble_project_path

if __name__ == "__main__":
    # Init config and logger
    config.init_config(config_path=assemble_project_path("configs/config_general.toml"))
    logger.init_logger(config.log_path)
    logger.info(f"Initializing logger: {config.log_path}")
    logger.info(f"Load config: {config}")

    # Registed models
    model_manager.init_models(use_local_proxy=True)
    logger.info("Registed models: %s", ", ".join(model_manager.registed_models.keys()))
    
    tool = AutoBrowserUseTool()

    loop = asyncio.get_event_loop()

    # task1 = "Find the minimum perigee value (closest approach distance) between the Earth and the Moon on the Wikipedia page for the Moon."
    # res = loop.run_until_complete(tool.forward(task=task1))
    # print(res)
    #
    # task2 = "Eliud Kipchoge's marathon world record time and pace"
    # res = loop.run_until_complete(tool.forward(task=task2))
    # print(res)

    task3 = "Open the pdf https://arxiv.org/abs/2506.12508, then extract the first paragraph of the page 3."
    res = loop.run_until_complete(tool.forward(task=task3))
    print(res)