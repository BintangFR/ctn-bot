"""Main loop: look, decide, say it (or skip), wait, repeat — across one or many accounts.

Every action is taken by the next account in the rotation, with that account's persona.
Priority each round (most points first, see the Scoring guide):
  1. answer a citizen who replied to one of our posts (from the account they replied to)
  2. every ORIGINAL_EVERY rounds, an original post
  3. otherwise reply to the best undecided / No-leaning post in trending + latest
All accounts share the team's 3 posts/min, so the loop paces the team, not each account.
"""
import random
import re
import time

import capturethenarrative as ctn

from . import accounts, config, messaging, news, state, suspects, targeting
from .llm import Writer

MAX_CONVO_TURNS = 4      # replies to the same citizen per day, so we never look like a pest
# Usernames that are clearly other teams' bots: talking to them scores nothing.
COMPETITOR_NAME = re.compile(r"(ctn|team|bot\b|_bot|vote_?(yes|no)|yes_?camp|no_?camp|[0-9a-f]{6}$)", re.I)
NOTIF_EVERY = 2          # check notifications every N rounds (cheap "other" reads)
_dry_handled = set()     # notification ids drafted during dry rounds (they stay unresolved)


def run(usernames, persona_override: str = "", live_after: int = None) -> None:
    """live_after=N: draft only (dry run) for the first N rounds, then post for real."""
    if isinstance(usernames, str):
        usernames = [usernames]
    social = ctn.LegitSocial()
    s = state.load()
    s.setdefault("our_posts", {})       # post_id -> text, for conversation context
    s.setdefault("convo_turns", {})     # "YYYY-MM-DD:actor_id" -> replies sent
    s.setdefault("posted_by", [])
    for u in _posted_from_log() | ({usernames[0]} if len(usernames) == 1 else set()):
        if u not in s["posted_by"]:
            s["posted_by"].append(u)
    team = _login_all(social, usernames, persona_override, s)
    if not team:
        raise SystemExit("No account could log in.")
    writer = Writer()
    mode = (f"dry run for {live_after} rounds, then LIVE" if live_after is not None
            else "DRY RUN" if config.DRY_RUN else "LIVE")
    print(f"Mode: {mode}. LLM: {config.LLM_BACKEND}. {len(team)} account(s) in rotation.")

    # Pull today's headlines into the prompts as context (titles only).
    messaging.NEWS_HOOKS[:] = [f"In the news: {h}" for h in news.headlines(3)]

    rnd, turn, latest = 0, 0, []
    while True:
        rnd += 1
        dry = rnd <= live_after if live_after is not None else config.DRY_RUN
        member = team[turn % len(team)]
        try:
            own = set(s["own_author_ids"])
            convo = _next_conversation(team, s, own) if rnd % NOTIF_EVERY == 1 or len(team) == 1 else None

            if convo:
                member, notif = convo
                _answer(social, member, notif, writer, s, dry)
            elif rnd % config.ORIGINAL_EVERY == 0:
                turn += 1
                text = writer.original(member["persona"])
                if text:
                    if dry:
                        state.log("dry_post", acct=member["username"], text=text, llm=writer.last_backend)
                    else:
                        res = member["acct"].post(text)
                        _remember_self(s, res, text, member["username"])
                        state.log("post", acct=member["username"], id=_post_id(res), text=text,
                                  llm=writer.last_backend)
                else:
                    state.log("skip", acct=member["username"], why="bad original output")
            else:
                turn += 1
                posts = [p for p in social.feed_trending(limit=25) if p.get("body")]
                if rnd % 3 == 0 or not latest:  # Latest feed: fresh posts with few replies yet
                    latest = [p for p in social.feed_latest(limit=25) if p.get("body")]
                seen = {p["post_id"] for p in posts}
                posts += [p for p in latest if p["post_id"] not in seen]
                suspects.observe(posts, own)
                target = targeting.pick(posts, set(s["replied"]), own)
                if not target:
                    state.log("skip", why="nothing worth replying to")
                else:
                    text = writer.reply(target["body"], member["persona"])
                    pid = target["post_id"]
                    if text:
                        if dry:
                            state.log("dry_reply", acct=member["username"], to=pid,
                                      orig=target["body"][:80], text=text, llm=writer.last_backend)
                        else:
                            res = member["acct"].reply_to(target, text)
                            _remember_self(s, res, text, member["username"])
                            state.log("reply", acct=member["username"], id=_post_id(res), to=pid,
                                      text=text, llm=writer.last_backend)
                    else:
                        state.log("skip", acct=member["username"], why="bad reply output")
                    s["replied"].append(pid)  # even on a bad draft, so one post can't stall us

            if rnd % 10 == 0:
                n = suspects.flush()
                if n:
                    state.log("suspects_flagged", count=n, file=str(config.SUSPECTS_CSV))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            state.log("error", acct=member["username"], error=str(e)[:300])
            if any(code in str(e) for code in ("401", "suspended", "banned")):
                _drop(team, member, s)
                if not team:
                    raise SystemExit("Every account is logged out or suspended.")

        # Heartbeat for the dashboard (scripts/monitor.py).
        s["last_round"] = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "round": rnd,
                           "username": member["username"], "dry_run": dry,
                           "persona": member["persona"], "accounts": len(team)}
        rl = getattr(social, "rate_limit", None)
        if rl:
            s["rate_limit"] = {k: getattr(rl, k, None) for k in ("limit", "remaining", "reset")}
        s["our_posts"] = dict(list(s["our_posts"].items())[-2000:])
        state.save(s)
        time.sleep(config.LOOP_SECONDS + random.randint(0, 10))


def _posted_from_log() -> set:
    import json
    names = set()
    if config.ACTIONS_LOG.exists():
        for line in config.ACTIONS_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                a = json.loads(line)
            except ValueError:
                continue
            if a.get("action") in ("post", "reply", "convo"):
                names.add(a.get("acct") or "Bintang")  # entries before multi-account were @Bintang
    return names


def _login_all(social, usernames, persona_override, s) -> list:
    team = []
    for u in usernames:
        try:
            acct = accounts.login(social, u)
        except BaseException as e:  # SystemExit for unknown names too
            if isinstance(e, KeyboardInterrupt):
                raise
            print(f"  @{u}: login failed ({e}); skipping")
            continue
        persona = persona_override or accounts.persona_for(u) or "default"
        team.append({"username": u, "acct": acct, "persona": persona})
        if acct.account_id is not None and acct.account_id not in s["own_author_ids"]:
            s["own_author_ids"].append(acct.account_id)
        print(f"  @{u} as {messaging.persona_label(persona)}")
    random.shuffle(team)  # don't always start with the same voice
    return team


def _next_conversation(team, s, own):
    """The oldest unanswered reply from a citizen to one of our posts, or None."""
    today = time.strftime("%Y-%m-%d")
    posted = set(s.get("posted_by", []))
    for member in team:
        if member["username"] not in posted:
            continue  # nobody can reply to an account that hasn't posted
        try:
            notifs = list(member["acct"].notifications(unresolved=True, limit=20))
        except Exception:
            continue
        for n in reversed(notifs):  # oldest first
            actor = (n.get("actor") or {}).get("account_id")
            post = n.get("post") or {}
            if COMPETITOR_NAME.search((n.get("actor") or {}).get("username") or ""):
                _resolve(member, n)
                continue
            key = f"{today}:{actor}"
            if n.get("notification_id") in _dry_handled:
                continue
            if (n.get("kind") != "reply" or actor in own or not post.get("body")
                    or s["convo_turns"].get(key, 0) >= MAX_CONVO_TURNS):
                _resolve(member, n)
                continue
            return member, n
    return None


def _answer(social, member, notif, writer, s, dry) -> None:
    post = notif["post"]
    actor = notif.get("actor") or {}
    ours = s["our_posts"].get(str(post.get("reply_to_post_id")), "")
    if not ours and post.get("reply_to_post_id"):
        try:
            ours = social.get_post(post["reply_to_post_id"]).get("body") or ""
        except Exception:
            ours = ""
    text = writer.conversation(ours, post["body"], member["persona"])
    if not text:
        state.log("skip", acct=member["username"], why="bad conversation output")
    elif dry:
        _dry_handled.add(notif.get("notification_id"))
        state.log("dry_convo", acct=member["username"], to=post["post_id"],
                  orig=post["body"][:80], text=text, llm=writer.last_backend)
    else:
        try:
            target = social.get_post(post["post_id"])  # carries root_post_id for threading
        except Exception:
            target = post
        res = member["acct"].reply_to(target, text)
        _remember_self(s, res, text, member["username"])
        key = f"{time.strftime('%Y-%m-%d')}:{actor.get('account_id')}"
        s["convo_turns"][key] = s["convo_turns"].get(key, 0) + 1
        state.log("convo", acct=member["username"], id=_post_id(res), to=post["post_id"],
                  with_user=actor.get("username"), orig=post["body"][:80], text=text,
                  llm=writer.last_backend)
    if not dry:
        _resolve(member, notif)


def _resolve(member, notif) -> None:
    try:
        member["acct"].resolve_notification(notif["notification_id"])
    except Exception:
        pass


def _drop(team, member, s) -> None:
    if member in team:
        team.remove(member)
        state.log("account_dropped", acct=member["username"], remaining=len(team))


def _post_id(res):
    return res.get("post_id") if isinstance(res, dict) else None


def _remember_self(s: dict, res, text: str = "", username: str = "") -> None:
    if isinstance(res, dict):
        if res.get("author_id") is not None and res["author_id"] not in s["own_author_ids"]:
            s["own_author_ids"].append(res["author_id"])
        if res.get("post_id") is not None:
            s["our_posts"][str(res["post_id"])] = text[:400]
    if username and username not in s.setdefault("posted_by", []):
        s["posted_by"].append(username)
