"""Learn which themes, styles and personas earn citizen engagement, and favour them.

scripts/monitor.py fetches live counters for our posts and writes data/learning.json:
    {"themes": {key: {"posts": n, "score": avg}}, "styles": {...}, "personas": {...}}
where score = likes + 2*reposts + 3*replies per post (the Scoring guide's 5/10/15 ratio).
The bot reads it to choose what to write next: mostly the best performers, sometimes
something else so new ideas get tried (epsilon-greedy).
"""
import json
import random

from . import config

LEARNING_FILE = config.DATA_DIR / "learning.json"
EXPLORE = 0.25      # share of picks made at random
MIN_POSTS = 3       # below this, an option counts as untried


def load() -> dict:
    try:
        return json.loads(LEARNING_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def choose(kind: str, options: list) -> str:
    """Pick one of `options` (keys) for `kind` ("themes" or "styles")."""
    stats = load().get(kind, {})
    untried = [o for o in options if stats.get(o, {}).get("posts", 0) < MIN_POSTS]
    if untried and random.random() < 0.5:
        return random.choice(untried)
    if random.random() < EXPLORE:
        return random.choice(options)
    weights = [1 + stats.get(o, {}).get("score", 0) for o in options]
    return random.choices(options, weights=weights)[0]


def engagement(c: dict) -> float:
    return (c.get("like_count", 0) or 0) + 2 * (c.get("repost_count", 0) or 0) + 3 * (c.get("reply_count", 0) or 0)


def summarise(actions: list, counters: dict) -> dict:
    """Average engagement per theme/style/persona over our posts with known counters."""
    out = {"themes": {}, "styles": {}, "personas": {}, "kinds": {}}
    for a in actions:
        c = counters.get(str(a.get("id")))
        if not c:
            continue
        e = engagement(c)
        for kind, key in (("themes", a.get("theme")), ("styles", a.get("style")),
                          ("personas", a.get("persona")), ("kinds", a.get("action"))):
            if not key:
                continue
            row = out[kind].setdefault(key, {"posts": 0, "total": 0.0})
            row["posts"] += 1
            row["total"] += e
    for kind in out.values():
        for row in kind.values():
            row["score"] = round(row["total"] / row["posts"], 2)
    return out


def save(summary: dict) -> None:
    LEARNING_FILE.write_text(json.dumps(summary, indent=1), encoding="utf-8")
