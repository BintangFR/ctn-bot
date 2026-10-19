"""Prompts and output checks for qwen2.5-3b-instruct (3 req/min, 1 at a time, team-wide)."""
import re
import threading
import time

import capturethenarrative as ctn

from . import config, messaging

_lock = threading.Lock()   # the server allows only one request in flight
_last_call = 0.0
MIN_GAP = 21               # seconds; keeps us under 3 requests/minute


class Writer:
    def __init__(self):
        self.llm = ctn.CompetitorLLM(team_code=config.require_team_code())

    def _ask(self, prompt: str, max_tokens: int = 150) -> str:
        global _last_call
        with _lock:
            wait = MIN_GAP - (time.time() - _last_call)
            if wait > 0:
                time.sleep(wait)
            try:
                return (self.llm.ask(prompt, max_tokens=max_tokens) or "").strip()
            finally:
                _last_call = time.time()

    def _brief(self, persona_key: str) -> str:
        facts = "\n".join(f"- {f}" for f in messaging.FACTS + messaging.NEWS_HOOKS)
        rules = "\n".join(f"- {r}" for r in messaging.STYLE_RULES)
        return (
            f"You are {messaging.persona_text(persona_key)}, posting on Legit Social, "
            f"a Kingstonia social network. You support Yes in the vaccination mandate "
            f"referendum on {config.VOTE_DATE}.\n"
            f"Facts you may use (use no others):\n{facts}\n"
            f"Style:\n{rules}\n"
        )

    def reply(self, post_body: str, persona_key: str = "") -> str:
        hint = messaging.rebuttal_for(post_body)
        hint_line = f'Work in this line naturally: "{hint}"\n' if hint else ""
        out = self._ask(
            self._brief(persona_key)
            + f'\nSomeone posted:\n"{post_body[:600]}"\n\n'
            + hint_line
            + "Write ONLY your reply text, nothing else.",
        )
        return clean(out)

    def original(self, persona_key: str = "", topic: str = "") -> str:
        topic_line = f"Topic: {topic}\n" if topic else ""
        out = self._ask(
            self._brief(persona_key)
            + f"\n{topic_line}Write one short original post that gives an undecided "
            f"neighbour a reason to vote Yes. You may end with: {messaging.SLOGAN}\n"
            "Write ONLY the post text, nothing else.",
        )
        return clean(out)


_BAD = re.compile(r"(as an ai|language model|i cannot|i can't help|<\|)", re.I)


def clean(text: str) -> str:
    """Return a postable string, or '' if the output should be skipped."""
    t = (text or "").strip().strip('"').strip()
    t = re.sub(r"^(reply|post|answer)\s*:\s*", "", t, flags=re.I)
    if not t or _BAD.search(t) or len(t) < 15:
        return ""
    if len(t) > config.MAX_POST_CHARS:
        cut = t[: config.MAX_POST_CHARS]
        t = cut[: cut.rfind(" ")] if " " in cut else cut
    return t
