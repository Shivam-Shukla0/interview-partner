"""Global configuration constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PROMPTS_DIR = PROJECT_ROOT / "agent" / "prompts"

# LLM
MODEL_NAME = "claude-sonnet-4-5"
PLANNER_MAX_TOKENS = 800
RESPONDER_MAX_TOKENS = 500
FEEDBACK_MAX_TOKENS = 2000

# Interview flow
TARGET_QUESTION_COUNT = 6  # main interview questions (excl. calibration)
MIN_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 7

# UI
SUPPORTED_ROLES = ["sde", "data_analyst", "sales", "retail", "marketing"]
ROLE_DISPLAY_NAMES = {
    "sde": "Software Development Engineer",
    "data_analyst": "Data Analyst",
    "sales": "Sales",
    "retail": "Retail Associate",
    "marketing": "Marketing",
}
