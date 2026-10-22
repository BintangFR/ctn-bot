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

from . import accounts, config, learning, messaging, news, roster, scraper, state, suspects, targeting
from .llm import Writer
from .targeting import COMPETITOR_NAME

NEWS_SHARE = 0.35        # share of original posts that react to a fresh news article

MAX_CONVO_TURNS = 4      # replies to the same citizen per day, so we never look like a pest
NOTIF_EVERY = 2          # check notifications every N rounds (cheap "other" reads)
COOL_OFF = 1800          # seconds an account sits out after an auth error it survived
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
    writer.recent.extend(list(s["our_posts"].values())[-writer.recent.maxlen:])
    s.setdefault("cold_replies", {})    # "YYYY-MM-DD:author_id" -> unprompted replies sent
    mode =(f"dry run for {live_after} rounds, then LIVE" if live_after is not None
            else "DRY RUN" if config.DRY_RUN else "LIVE")
    print(f"Mode: {mode}. LLM: {config.LLM_BACKEND}. {len(team)} account(s) in rotation.")

    # Pull today's headlines into the prompts as context (titles only).
    messaging.NEWS_HOOKS[:] = [f"In the news: {h}" for h in news.headlines(3)]

    rnd, turn, latest = 0, 0, []
    while True:
        rnd += 1
        dry = rnd <= live_after if live_after is not None else config.DRY_RUN
        for _ in range(len(team)):  # skip accounts sitting out after an auth error
            if team[turn % len(team)].get("cool_until", 0) <= time.time():
                break
            turn += 1
        member = team[turn % len(team)]
        try:
            own = set(s["own_author_ids"])
            convo = _next_conversation(team, s, own) if rnd % NOTIF_EVERY == 1 or len(team) == 1 else None

            if convo:
                member, notif = convo
                _answer(social, member, notif, writer, s, dry)
            elif rnd % config.ORIGINAL_EVERY == 0:
                turn += 1
                article = _fresh_article(s) if random.random() < NEWS_SHARE else None
                if article:
                    theme, style = "news", "news"
                    text = writer.news_post(member["persona"], article)
                else:
                    theme = learning.choose("themes", list(messaging.THEMES))
                    style = learning.choose("styles", list(messaging.STYLES))
                    text = writer.original(member["persona"], theme, style)
                meta = {"acct": member["username"], "persona": member["persona"], "theme": theme,
                        "style": style, "llm": writer.last_backend}
                if article:
                    meta["article"] = article["key"]
                if text:
                    if dry:
                        state.log("dry_post", text=text, **meta)
                    else:
                        res = member["acct"].post(text)
                        _remember_self(s, res, text, member["username"])
                        if article:
                            s.setdefault("used_articles", []).append(article["key"])
                        state.log("post", id=_post_id(res), text=text, **meta)
                else:
                    state.log("skip", acct=member["username"], why="bad original output",
                              reason=writer.last_reject)
            else:
                turn += 1
                posts = [p for p in social.feed_trending(limit=25) if p.get("body")]
                if rnd % 3 == 0 or not latest:  # Latest feed: fresh posts with few replies yet
                    latest = [p for p in social.feed_latest(limit=25) if p.get("body")]
                seen = {p["post_id"] for p in posts}
                posts += [p for p in latest if p["post_id"] not in seen]
                suspects.observe(posts, own)
                today = time.strftime("%Y-%m-%d") + ":"
                cold = {int(k[len(today):]): v for k, v in s["cold_replies"].items()
                        if k.startswith(today) and k[len(today):].isdigit()}
                target = targeting.pick(posts, set(s["replied"]), own, cold)
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
                            ckey = f"{today}{target.get('author_id')}"
                            s["cold_replies"][ckey] = s["cold_replies"].get(ckey, 0) + 1
                            state.log("reply", acct=member["username"], id=_post_id(res), to=pid,
                                      text=text, persona=member["persona"], llm=writer.last_backend)
                    else:
                        state.log("skip", acct=member["username"], why="bad reply output",
                                  reason=writer.last_reject)
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
                _revive_or_drop(social, team, member, s, str(e)[:80])
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
        s["cold_replies"] = dict(list(s["cold_replies"].items())[-3000:])
        state.save(s)
        time.sleep(config.LOOP_SECONDS + random.randint(0, 10))


def _fresh_article(s):
    """Newest referendum article from the last 36h that no account has reacted to yet."""
    used = set(s.get("used_articles", []))
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 36 * 3600))
    for a in scraper.articles():
        if (a.get("published_at", "") >= cutoff and "referendum" in (a.get("topics") or [])
                and a["key"] not in used and a.get("body")):
            return a
    return None


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
        state.log("skip", acct=member["username"], why="bad conversation output",
                  reason=writer.last_reject)
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
                  persona=member["persona"], llm=writer.last_backend)
    if not dry:
        _resolve(member, notif)


def _resolve(member, notif) -> None:
    try:
        member["acct"].resolve_notification(notif["notification_id"])
    except Exception:
        pass


def _revive_or_drop(social, team, member, s, err: str) -> None:
    """An auth error. An expired token or a passing hiccup isn't a dead account: log in
    afresh and sit the account out for a while. Only if that fails is it replaced."""
    try:
        member["acct"] = accounts.login(social, member["username"], fresh=True)
        member["cool_until"] = time.time() + COOL_OFF
        state.log("account_relogin", acct=member["username"], error=err)
        return
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        why = f"{err} / login: {str(e)[:80]}"
    _drop(social, team, member, s, why)


def _drop(social, team, member, s, why: str) -> None:
    """Retire a dead account and bring in a replacement, so the pool stays at MAX_ACTIVE,
    never above. A suspended account still holds one of the portal's active places, so it is
    deleted to free that place before a new account is registered in its stead."""
    if member not in team:
        return
    team.remove(member)
    accounts.retire(member["username"], why)
    state.log("account_dropped", acct=member["username"], why=why, remaining=len(team))
    if re.search(r"suspend|banned", why, re.I):
        try:
            member["acct"].delete()
            state.log("account_deleted", acct=member["username"], why="suspended; frees an active place")
        except Exception as e:
            state.log("delete_failed", acct=member["username"], error=str(e)[:200])
    new = accounts.promote_reserve(member["persona"]) or _register_replacement(social, member["persona"])
    if new:
        joined = _login_all(social, [new], "", s)
        team.extend(joined)
        state.log("account_promoted", acct=new, replaces=member["username"], active=len(team))


def _register_replacement(social, persona: str):
    """Register one new account with the same persona. Returns its username, or None."""
    if len(accounts.list_accounts()) >= config.MAX_ACCOUNTS:
        return None
    taken = set(accounts.list_accounts())
    for name, display, p in roster.generated(3, taken, random.Random(), persona or "default"):
        try:
            accounts.create(social, name, display, p, active=True)
            state.log("account_created", acct=name, persona=p)
            return name
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            state.log("replacement_failed", acct=name, error=str(e)[:200])
            if "403" in str(e):
                return None  # the portal refused: no point trying other names
    return None


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
