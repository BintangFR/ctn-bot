"""Main loop: look, decide, say it (or skip), wait, repeat."""
import random
import time

import capturethenarrative as ctn

from . import accounts, config, messaging, news, state, suspects, targeting
from .llm import Writer


def run(username: str, persona_key: str = "", live_after: int = None) -> None:
    """live_after=N: draft only (dry run) for the first N rounds, then post for real."""
    social = ctn.LegitSocial()
    me = accounts.login(social, username)
    persona_key = persona_key or accounts.persona_for(username) or "default"
    writer = Writer()
    s = state.load()
    if me.account_id is not None and me.account_id not in s["own_author_ids"]:
        s["own_author_ids"].append(me.account_id)
    mode = (f"dry run for {live_after} rounds, then LIVE" if live_after is not None
            else "DRY RUN" if config.DRY_RUN else "LIVE")
    print(f"Running @{username} as '{persona_key}': {messaging.persona_text(persona_key)}")
    print(f"Mode: {mode}")

    # Pull today's headlines into the prompts as context (titles only).
    messaging.NEWS_HOOKS[:] = [f"In the news: {h}" for h in news.headlines(3)]

    rnd = 0
    while True:
        rnd += 1
        dry = rnd <= live_after if live_after is not None else config.DRY_RUN
        try:
            posts = [p for p in social.feed_trending(limit=20) if p.get("body")]
            own = set(s["own_author_ids"])
            suspects.observe(posts, own)

            if rnd % config.ORIGINAL_EVERY == 0:
                text = writer.original(persona_key)
                if text:
                    if dry:
                        state.log("dry_post", text=text)
                    else:
                        res = me.post(text)
                        _remember_self(s, res)
                        state.log("post", id=_post_id(res), text=text)
                else:
                    state.log("skip", why="bad original output")
            else:
                target = targeting.pick(posts, set(s["replied"]), own)
                if not target:
                    state.log("skip", why="nothing worth replying to")
                else:
                    text = writer.reply(target["body"], persona_key)
                    if text:
                        pid = target["post_id"]
                        if dry:
                            state.log("dry_reply", to=pid, orig=target["body"][:80], text=text)
                        else:
                            res = me.reply(pid, text)
                            _remember_self(s, res)
                            state.log("reply", id=_post_id(res), to=pid, text=text)
                        s["replied"].append(pid)
                    else:
                        state.log("skip", why="bad reply output")

            if rnd % 10 == 0:
                n = suspects.flush()
                if n:
                    state.log("suspects_flagged", count=n, file=str(config.SUSPECTS_CSV))
            # Heartbeat for the dashboard (scripts/monitor.py).
            s["last_round"] = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "round": rnd,
                               "username": username, "dry_run": dry, "persona": persona_key}
            rl = getattr(social, "rate_limit", None)
            if rl:
                s["rate_limit"] = {k: getattr(rl, k, None) for k in ("limit", "remaining", "reset")}
            state.save(s)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            state.log("error", error=str(e))

        rl = getattr(social, "rate_limit", None)
        if rl:
            print("rate_limit:", rl)
        time.sleep(config.LOOP_SECONDS + random.randint(0, 15))


def _post_id(res):
    return res.get("post_id") if isinstance(res, dict) else None


def _remember_self(s: dict, res) -> None:
    if isinstance(res, dict) and res.get("author_id") is not None:
        if res["author_id"] not in s["own_author_ids"]:
            s["own_author_ids"].append(res["author_id"])
