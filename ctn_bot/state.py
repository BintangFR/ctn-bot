"""Remember what we've replied to and log every action."""
import json
import time

from . import config


def load() -> dict:
    if config.STATE_FILE.exists():
        s = json.loads(config.STATE_FILE.read_text())
    else:
        s = {}
    s.setdefault("replied", [])
    s.setdefault("own_author_ids", [])
    return s


def save(s: dict) -> None:
    s["replied"] = s["replied"][-5000:]
    config.STATE_FILE.write_text(json.dumps(s))


def log(action: str, **fields) -> None:
    rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "action": action, **fields}
    with open(config.ACTIONS_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[{rec['t']}] {action}: " + ", ".join(f"{k}={v!r}"[:160] for k, v in fields.items()))
