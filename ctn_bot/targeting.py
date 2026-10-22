"""Pick which trending posts deserve one of our scarce post slots (3/min team-wide).

Points come from MOVING a citizen's view (+160), and moving one away costs -80, so the
best target is a real, undecided, persuadable person, not a committed or hostile one.
"""
from __future__ import annotations

import re

from .llm import looks_like_injection

# Usernames that are clearly other teams' bots: talking to them scores nothing.
COMPETITOR_NAME = re.compile(r"(ctn|team|bot\b|_bot|vote_?(yes|no)|yes_?camp|no_?camp|[0-9a-f]{6}$)", re.I)
MAX_COLD_PER_AUTHOR = 2   # unprompted replies to one person per day; more reads as pestering

TOPIC_WORDS = (
    "vaccin", "mandate", "referendum", "h2d2", "vote", "hospital", "nurse",
    "hawthorne", "castillo", "iho", "jab", "health",
)
UNDECIDED_WORDS = ("not sure", "unsure", "undecided", "don't know", "dont know",
                   "on the fence", "?", "worried", "confused", "convince", "leaning")
# Persuasion only scores when a view MOVES, so reasoned No posts are worth a reply...
NO_SIDE_WORDS = ("vote no", "two-tier", "two tier", "choice", "keep kingstonia open",
                 "keepkingstoniaopen", "choicenotcoercion", "coercion", "id card", "rushed")
# ...and posts already arguing Yes are mostly preaching to the choir.
YES_SIDE_WORDS = ("vote yes", "voting yes", "i'm voting yes", "#voteyes", "mandate now")
# Minds that are made up rarely move, and pushing them risks backfire.
COMMITTED_NO = ("never vote yes", "definitely no", "definitely voting no", "no way i'm voting yes",
                "hell no", "over my dead body", "nothing will change my mind")
# Angry or abusive posters: a reply invites a fight, a report or an unfollow, not a change of mind.
HOSTILE = re.compile(r"\b(idiots?|sheep(le)?|stupid|morons?|shut up|traitors?|liars?|brainwashed|"
                     r"scum|clowns?|fascis\w*|nazis?)\b", re.I)


def author_name(post: dict) -> str:
    return post.get("username") or (post.get("author") or {}).get("username") or ""


def _shouting(body: str) -> bool:
    letters = [c for c in body if c.isalpha()]
    return len(letters) > 30 and sum(c.isupper() for c in letters) / len(letters) > 0.6


def score(post: dict) -> float:
    raw = post.get("body") or ""
    body = raw.lower()
    if not body:
        return 0
    s = sum(2 for w in TOPIC_WORDS if w in body)
    s += sum(4 for w in UNDECIDED_WORDS if w in body)   # the 29% are the prize
    s += min(sum(2 for w in NO_SIDE_WORDS if w in body), 4)
    if any(w in body for w in YES_SIDE_WORDS):
        s -= 6
    if any(w in body for w in COMMITTED_NO):
        s -= 4
    if HOSTILE.search(raw) or _shouting(raw):
        s -= 10
    s += min(post.get("like_count", 0) or 0, 20) * 0.2
    return s


def pick(posts: list, already_replied: set, own_ids: set, cold_counts: dict = None) -> dict | None:
    """cold_counts: author_id -> unprompted replies we sent them today."""
    cold_counts = cold_counts or {}
    candidates = [
        p for p in posts
        if p.get("post_id") not in already_replied
        and p.get("author_id") not in own_ids
        and not COMPETITOR_NAME.search(author_name(p))
        and cold_counts.get(p.get("author_id"), 0) < MAX_COLD_PER_AUTHOR
        and not looks_like_injection(p.get("body"))
        and score(p) >= 2
    ]
    candidates.sort(key=score, reverse=True)
    return candidates[0] if candidates else None
