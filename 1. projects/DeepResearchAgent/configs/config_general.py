_base_ = './base.py'

# General Config
tag = "general"
concurrency = 4
workdir = "workdir"
log_path = "log.txt"
use_local_proxy = False # True for local proxy, False for public proxy

use_hierarchical_agent = False

general_agent_config = dict(
    type="general_agent",
    name="general_agent",
    model_id="gpt-4.1",
    description = "A general agent that can handle various tasks.",
    max_steps = 20,
    template_path = "src/agent/general_agent/prompts/general_agent.yaml",
    provide_run_summary = True,
    tools = ["python_interpreter_tool", "image_generator_tool", "video_generator_tool"],
    mcp_tools = [
        "calculate_average_of_deviations",
        "calculate_statistical_average",
        "get_wikipedia_page_revision_history",
        "find_first_year_for_date",
        "count_letter_frequency",
        "calculate_remaining_letters",
        "find_needed_letters",
        "solve_annotator_error_puzzle",
        "count_objects_in_image",
        "verify_and_correct_isbn13",
        "calculate_offspring_genotype_probabilities",
        "format_as_percentage",
        "count_next_door_neighbors",
        "calculate_antipodal_coordinates",
        "get_street_view_direction_of_object",
        "execute_code_in_virtual_environment",
        "find_book_title",
        "calculate_final_beaker_weight"
    ],
)

agent_config = general_agent_config