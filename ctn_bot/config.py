"""Settings loaded from .env (see .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

TEAM_CODE = os.getenv("CTN_TEAM_CODE", "")
SIDE = os.getenv("CTN_SIDE", "Vote Yes")
DRY_RUN = os.getenv("CTN_DRY_RUN", "1") != "0"
LOOP_SECONDS = int(os.getenv("CTN_LOOP_SECONDS", "60"))
ORIGINAL_EVERY = int(os.getenv("CTN_ORIGINAL_EVERY", "4"))
MONITOR_SECONDS = int(os.getenv("CTN_MONITOR_SECONDS", "300"))

# "competition" (qwen2.5-3b on llm.legitreal.com) or "ollama" (local model)
LLM_BACKEND = os.getenv("CTN_LLM", "competition").lower()
OLLAMA_URL = os.getenv("CTN_OLLAMA_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("CTN_OLLAMA_MODEL", "qwen2.5:7b")
DRAFTS = int(os.getenv("CTN_DRAFTS", "3"))

SECRETS_DIR = ROOT / "secrets"
LOGS_DIR = ROOT / "logs"
DATA_DIR = ROOT / "data"
NEWS_DIR = DATA_DIR / "news"
ACCOUNTS_FILE = SECRETS_DIR / "accounts.json"
STATE_FILE = LOGS_DIR / "state.json"
ACTIONS_LOG = LOGS_DIR / "actions.jsonl"
SUSPECTS_CSV = LOGS_DIR / "suspects.csv"
NEWS_FILE = NEWS_DIR / "articles.json"
DASHBOARD_DATA = ROOT / "dashboard_data.js"

MAX_POST_CHARS = 500
VOTE_DATE = "2 November 2026"

SECRETS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
NEWS_DIR.mkdir(parents=True, exist_ok=True)


def require_team_code() -> str:
    if not TEAM_CODE or TEAM_CODE == "TEAMCODE123456":
        raise SystemExit("Set CTN_TEAM_CODE in .env first (copy .env.example to .env).")
    return TEAM_CODE
