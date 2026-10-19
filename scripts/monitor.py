"""Scrape the news sites and refresh dashboard_data.js, then open dashboard.html.

Usage:
    python scripts/monitor.py              # loop every CTN_MONITOR_SECONDS (default 300)
    python scripts/monitor.py --once       # one refresh and exit
    python scripts/monitor.py --no-social  # skip Legit Social reads (news + bot logs only)

Each refresh uses 1 feed read and ~30 "other" reads of the team's Legit Social
allowance, so it barely touches what the bot needs.
"""
import argparse
import time

import _path  # noqa: F401

from ctn_bot import config, dashboard, scraper

ap = argparse.ArgumentParser()
ap.add_argument("--once", action="store_true")
ap.add_argument("--no-social", action="store_true")
ap.add_argument("--every", type=int, default=config.MONITOR_SECONDS)
args = ap.parse_args()
config.MONITOR_SECONDS = args.every

print(f"Dashboard: {config.ROOT / 'dashboard.html'}  (open it in your browser)")
while True:
    started = time.strftime("%H:%M:%S")
    news_error = None
    try:
        res = scraper.sync()
        news_msg = f"{len(res['new'])} new / {res['total']} articles"
    except Exception as e:
        news_error = f"news: {e}"
        news_msg = news_error
    snap = dashboard.build(include_social=not args.no_social)
    if news_error:
        snap["errors"].append(news_error)
    dashboard.write(snap)
    print(f"[{started}] {news_msg}; {len(snap['actions'])} bot actions; "
          f"errors: {snap['errors'] or 'none'}")
    for key in (res["new"] if not news_error else []):
        print("   NEW:", key)
    if args.once:
        break
    time.sleep(args.every)
