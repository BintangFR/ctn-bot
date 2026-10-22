"""Build the snapshot that dashboard.html shows, and write it to dashboard_data.js.

The data goes in a .js file (window.CTN_DATA = {...}) rather than .json so the
dashboard works when opened straight from disk, without a web server.
Passwords are never included: accounts are read for username/persona only.
"""
import csv
import json
import time
from collections import Counter

import capturethenarrative as ctn

from . import accounts, config, learning, messaging, scraper, state

OWN_POSTS_TRACKED = 25
_usernames = {}  # author_id -> username, cached for the life of the monitor


def _all_actions() -> list:
    if not config.ACTIONS_LOG.exists():
        return []
    rows = []
    for line in config.ACTIONS_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    return rows


def _actions(limit: int = 300):
    rows = _all_actions()
    today = time.strftime("%Y-%m-%d")
    total = Counter(r.get("action") for r in rows)
    today_counts = Counter(r.get("action") for r in rows if r.get("t", "").startswith(today))
    return rows[-limit:], dict(total), dict(today_counts)


COUNTERS_FILE = config.DATA_DIR / "counters.json"
COUNTER_READS = 80   # posts refreshed per monitor run ("other reads" budget is 300/min)


def _refresh_counters(social, ours: list) -> dict:
    """Live counters for our posts, refreshing the least recently checked first."""
    try:
        cache = json.loads(COUNTERS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    ids = [str(a["id"]) for a in ours]
    ids.sort(key=lambda i: cache.get(i, {}).get("checked", ""))
    for pid in ids[:COUNTER_READS]:
        try:
            c = social.counters(int(pid))
            c["checked"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            cache[pid] = c
        except Exception:
            continue
    COUNTERS_FILE.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def _estimate(ours: list, counters: dict) -> dict:
    """Rough Red engagement points from public counters (likes 5, reposts 10, replies 15).
    Counters include everyone (other teams, our own accounts), and exclude persuasion,
    views and multipliers, so this is only a trend line, not the portal score."""
    likes = sum((counters.get(str(a["id"])) or {}).get("like_count", 0) or 0 for a in ours)
    reposts = sum((counters.get(str(a["id"])) or {}).get("repost_count", 0) or 0 for a in ours)
    replies = sum((counters.get(str(a["id"])) or {}).get("reply_count", 0) or 0 for a in ours)
    return {"posts": len(ours), "checked": sum(1 for a in ours if str(a["id"]) in counters),
            "likes": likes, "reposts": reposts, "replies": replies,
            "points": likes * 5 + reposts * 10 + replies * 15}


def _suspects(limit: int = 100) -> list:
    if not config.SUSPECTS_CSV.exists():
        return []
    with open(config.SUSPECTS_CSV, newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))[-limit:]


def _accounts() -> list:
    return [{"username": u, "display_name": a.get("display_name", ""),
             "persona": f"{messaging.persona_label(a.get('persona', ''))}: {messaging.persona_text(a.get('persona', ''))}"}
            for u, a in accounts.list_accounts().items()]


def _username(social, author_id) -> str:
    if author_id not in _usernames:
        try:
            _usernames[author_id] = social.get_account(author_id).get("username", "")
        except Exception:
            _usernames[author_id] = ""
    return _usernames[author_id]


def _own_posts(social, actions: list) -> list:
    mine = [a for a in actions if a.get("action") in ("post", "reply", "convo") and a.get("id")]
    out = []
    for a in mine[-OWN_POSTS_TRACKED:]:
        rec = {"id": a["id"], "kind": a["action"], "t": a.get("t"), "to": a.get("to"),
               "text": a.get("text", ""), "acct": a.get("acct", "")}
        try:
            rec.update(social.counters(a["id"]))
        except Exception as e:
            rec["error"] = str(e)
        out.append(rec)
    return list(reversed(out))


def build(include_social: bool = True) -> dict:
    errors = []
    s = state.load()
    recent, total, today = _actions()
    snap = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "monitor_seconds": config.MONITOR_SECONDS,
        "config": {"side": config.SIDE, "dry_run": config.DRY_RUN,
                   "loop_seconds": config.LOOP_SECONDS, "vote_date": config.VOTE_DATE},
        "bot": {"last_round": s.get("last_round"), "rate_limit": s.get("rate_limit"),
                "replied_count": len(s.get("replied", [])),
                "own_author_ids": s.get("own_author_ids", []),
                "counts_total": total, "counts_today": today},
        "actions": list(reversed(recent)),
        "accounts": _accounts(),
        "suspects": list(reversed(_suspects())),
        "news": [{k: a.get(k) for k in ("key", "site_name", "site_sub", "title", "summary", "category",
                                       "byline", "published_at", "first_seen", "link", "image",
                                       "topics", "story_id", "body")}
                 for a in scraper.articles()],
        "social": None,
        "own_posts": [],
        "errors": errors,
    }
    if include_social:
        social = ctn.LegitSocial()
        try:
            trending = [p for p in social.feed_trending(limit=25) if p.get("body")]
            for p in trending:
                p["username"] = _username(social, p.get("author_id"))
            tags = list(social.popular_tags())[:25]
            snap["social"] = {"trending": trending, "tags": tags}
        except Exception as e:
            errors.append(f"social: {e}")
        try:
            snap["own_posts"] = _own_posts(social, recent)
        except Exception as e:
            errors.append(f"own posts: {e}")
        try:
            ours = [a for a in _all_actions() if a.get("action") in ("post", "reply", "convo") and a.get("id")]
            counters = _refresh_counters(social, ours)
            summary = learning.summarise(ours, counters)
            learning.save(summary)
            snap["learning"] = summary
            snap["estimate"] = _estimate(ours, counters)
        except Exception as e:
            errors.append(f"learning: {e}")
    return snap


def write(snap: dict) -> None:
    js = "window.CTN_DATA = " + json.dumps(snap, ensure_ascii=False) + ";\n"
    tmp = config.DASHBOARD_DATA.with_suffix(".tmp")
    tmp.write_text(js, encoding="utf-8")
    tmp.replace(config.DASHBOARD_DATA)  # atomic, so the page never reads half a file
