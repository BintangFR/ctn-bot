"""Collect every article from the Daily Kingstonia and the Kingstonia Herald.

Uses the sites' own .json pages (via capturethenarrative.NewsSites), not HTML parsing.
Front pages are re-read on every sync; each article's full body is fetched once and
cached in data/news/articles.json, plus a readable copy in data/news/<site>/<slug>.md.
"""
import json
import re
import time

import capturethenarrative as ctn

from . import config

BASE_URL = "https://sites.legitreal.com"

# Rough topic tags so the dashboard can filter. Matched against title + summary + body.
TOPICS = {
    "referendum": r"referend|h2d2|mandate|vaccin|proof rule",
    "yes-camp": r"medical officers union|\bmouk\b|vote yes|yes campaign",
    "no-camp": r"tourism board|\bkitb\b|vote no|no campaign|two-tier",
    "health": r"hospital|nurse|doctor|outbreak|chief medical",
    "economy": r"business|jobs|tourism|economy|cost|k\$",
}


def load() -> dict:
    if config.NEWS_FILE.exists():
        return json.loads(config.NEWS_FILE.read_text(encoding="utf-8"))
    return {}


def _save(data: dict) -> None:
    config.NEWS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _topics(a: dict) -> list:
    text = " ".join([a.get("title", ""), a.get("summary", ""), a.get("body", "")]).lower()
    return [name for name, rx in TOPICS.items() if re.search(rx, text)]


def _write_md(a: dict) -> None:
    folder = config.NEWS_DIR / a["site_sub"]
    folder.mkdir(exist_ok=True)
    md = (f"# {a['title']}\n\n{a['site_name']} | {a.get('category', '')} | "
          f"{a.get('byline', '')} | {a.get('published_at', '')}\n{a['link']}\n\n"
          f"> {a.get('summary', '')}\n\n{a.get('body', '')}\n")
    (folder / f"{a['slug']}.md").write_text(md, encoding="utf-8")


def sync(news: "ctn.NewsSites" = None) -> dict:
    """Fetch front pages and any new article bodies. Returns {"new": [...keys], "total": n}."""
    news = news or ctn.NewsSites()
    data = load()
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    new = []
    for site in news.sites():
        for art in news.articles(site):
            key = f"{site['sub_url']}/{art['slug']}"
            rec = data.get(key)
            if rec is None:
                try:
                    full = news.article(site, art["slug"])
                except Exception as e:
                    print("article unavailable:", key, e)
                    continue
                rec = {**art, **full, "first_seen": now}
                new.append(key)
                time.sleep(0.2)  # be polite to the news host
            else:
                # Front-page fields (headline, summary) can change; keep the cached body.
                rec.update({k: v for k, v in art.items() if k != "body"})
            rec.update({
                "key": key,
                "site_name": site["name"],
                "site_sub": site["sub_url"],
                "link": BASE_URL + art.get("url", ""),
                "image": BASE_URL + art["lead_image_url"] if art.get("lead_image_url") else "",
                "last_seen": now,
            })
            rec["topics"] = _topics(rec)
            data[key] = rec
            if key in new:
                _write_md(rec)
    _save(data)
    return {"new": new, "total": len(data)}


def articles(newest_first: bool = True) -> list:
    return sorted(load().values(), key=lambda a: a.get("published_at", ""), reverse=newest_first)
