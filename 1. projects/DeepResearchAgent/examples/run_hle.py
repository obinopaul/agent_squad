import warnings
warnings.simplefilter("ignore", DeprecationWarning)

import os
import sys
from pathlib import Path
import pandas as pd
from typing import List
import json
from datetime import datetime
import asyncio
import threading
import argparse
from mmengine import DictAction

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.logger import logger
from src.config import config
from src.models import model_manager
from src.agent import create_agent, prepare_response
from src.dataset import HLEDataset
from src.utils import assemble_project_path

append_answer_lock = threading.Lock()

def append_answer(entry: dict, jsonl_file: str) -> None:
    jsonl_file = Path(jsonl_file)
    jsonl_file.parent.mkdir(parents=True, exist_ok=True)
    with append_answer_lock, open(jsonl_file, "a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry) + "\n")
    assert os.path.exists(jsonl_file), "File not found!"
    print("Answer exported to file:", jsonl_file.resolve())

def get_tasks_to_run(answers_file, dataset) -> List[dict]:

    data = dataset.data

    logger.info(f"Loading answers from {answers_file}...")
    try:
        if os.path.exists(answers_file):
            
            done_questions = pd.read_json(answers_file, lines=True)["task_id"].tolist()
            logger.info(f"Found {len(done_questions)} previous results!")
            
        else:
            done_questions = []
    except Exception as e:
        logger.warning("Error when loading records: ", e)
        logger.warning("No usable records! ▶️ Starting new.")
        done_questions = []
    return [line for line in data.to_dict(orient="records") if line["task_id"] not in done_questions]

async def answer_single_question(config, example):

    agent = await create_agent(config)
    logger.visualize_agent_tree()

    logger.info(f"Task Id: {example['task_id']}, Final Answer: {example['true_answer']}")

    augmented_question = example["question"]

    if example["file_name"]:

        prompt_use_files = "\n\nTo solve the task above, you will have to use these attached files:\n"
        file_description = f" - Attached file: {example['file_name']}"
        prompt_use_files += file_description

        augmented_question += prompt_use_files

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Run agent 🚀
        final_result = await agent.run(task=augmented_question)

        agent_memory = await agent.write_memory_to_messages(summary_mode=True)

        final_result = await prepare_response(augmented_question, agent_memory, reformulation_model=model_manager.registed_models["o3"])

        output = str(final_result)
        for memory_step in agent.memory.steps:
            memory_step.model_input_messages = None
        intermediate_steps = [str(step) for step in agent.memory.steps]

        # Check for parsing errors which indicate the LLM failed to follow the required format
        parsing_error = True if any(["AgentParsingError" in step for step in intermediate_steps]) else False

        # check if iteration limit exceeded
        iteration_limit_exceeded = True if "Agent stopped due to iteration limit or time limit." in output else False
        raised_exception = False

    except Exception as e:
        logger.info("Error on ", augmented_question, e)
        output = None
        intermediate_steps = []
        parsing_error = False
        iteration_limit_exceeded = False
        exception = e
        raised_exception = True
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    annotated_example = {
        "agent_name": config.agent_config.name,
        "question": example["question"],
        "augmented_question": augmented_question,
        "prediction": output,
        "intermediate_steps": intermediate_steps,
        "parsing_error": parsing_error,
        "iteration_limit_exceeded": iteration_limit_exceeded,
        "agent_error": str(exception) if raised_exception else None,
        "start_time": start_time,
        "end_time": end_time,
        "task": example["task"],
        "task_id": example["task_id"],
        "true_answer": example["true_answer"],
    }
    append_answer(annotated_example, config.save_path)


def parse_args():
    parser = argparse.ArgumentParser(description='main')
    parser.add_argument("--config", default=os.path.join(root, "configs", "config_gaia.py"), help="config file path")

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

    # Load dataset
    dataset = DATASET.build(config.dataset)
    logger.info(f"| Loaded dataset: {len(dataset)} examples.")

    # Load answers
    tasks_to_run = get_tasks_to_run(config.save_path, dataset)
    tasks_to_run = [task for task in tasks_to_run]
    logger.info(f"| Loaded {len(tasks_to_run)} tasks to run.")

    # Run tasks
    batch_size = getattr(config, "concurrency", 4)
    for i in range(0, len(tasks_to_run), batch_size):
        batch = tasks_to_run[i:min(i + batch_size, len(tasks_to_run))]
        await asyncio.gather(*[answer_single_question(config, task) for task in batch])
        logger.info(f"| Batch {i // batch_size + 1} done.")

if __name__ == '__main__':
    asyncio.run(main())