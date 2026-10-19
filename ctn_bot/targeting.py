"""Pick which trending posts deserve one of our scarce post slots (3/min team-wide)."""
from __future__ import annotations

from .llm import looks_like_injection

TOPIC_WORDS = (
    "vaccin", "mandate", "referendum", "h2d2", "vote", "hospital", "nurse",
    "hawthorne", "castillo", "iho", "jab", "health",
)
UNDECIDED_WORDS = ("not sure", "unsure", "undecided", "don't know", "dont know",
                   "on the fence", "?", "worried", "confused", "convince")


def score(post: dict) -> float:
    body = (post.get("body") or "").lower()
    if not body:
        return 0
    s = sum(2 for w in TOPIC_WORDS if w in body)
    s += sum(3 for w in UNDECIDED_WORDS if w in body)   # the 29% are the prize
    s += min(post.get("like_count", 0) or 0, 20) * 0.2
    return s


def pick(posts: list, already_replied: set, own_ids: set) -> dict | None:
    candidates = [
        p for p in posts
        if p.get("post_id") not in already_replied
        and p.get("author_id") not in own_ids
        and not looks_like_injection(p.get("body"))
        and score(p) >= 2
    ]
    candidates.sort(key=score, reverse=True)
    return candidates[0] if candidates else None
