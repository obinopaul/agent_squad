import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.tools.deep_analyzer import DeepAnalyzerTool
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
    
    deep_analyzer = DeepAnalyzerTool()

    task = """
    Please give a detailed analysis of the following image.
    """

    response = asyncio.run(deep_analyzer.forward(task=task,
                                                 source=os.path.join(root, "data/GAIA/2023/validation/b2c257e0-3ad7-4f05-b8e3-d9da973be36e.jpg")))
    
    print(response)