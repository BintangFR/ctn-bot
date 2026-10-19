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

from . import accounts, config, messaging, scraper, state

OWN_POSTS_TRACKED = 25
_usernames = {}  # author_id -> username, cached for the life of the monitor


def _actions(limit: int = 300):
    if not config.ACTIONS_LOG.exists():
        return [], {}, {}
    rows = []
    for line in config.ACTIONS_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    today = time.strftime("%Y-%m-%d")
    total = Counter(r.get("action") for r in rows)
    today_counts = Counter(r.get("action") for r in rows if r.get("t", "").startswith(today))
    return rows[-limit:], dict(total), dict(today_counts)


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
    return snap


def write(snap: dict) -> None:
    js = "window.CTN_DATA = " + json.dumps(snap, ensure_ascii=False) + ";\n"
    tmp = config.DASHBOARD_DATA.with_suffix(".tmp")
    tmp.write_text(js, encoding="utf-8")
    tmp.replace(config.DASHBOARD_DATA)  # atomic, so the page never reads half a file
