"""Dry-run the bot's brain without an account: pick targets from trending, draft replies
and one original post, print them. Nothing is posted.

Usage: python scripts/try_writer.py [persona] [n_replies]
"""
import sys

import _path  # noqa: F401
import capturethenarrative as ctn

from ctn_bot import messaging, news, targeting
from ctn_bot.llm import Writer

persona = sys.argv[1] if len(sys.argv) > 1 else "nurse"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 2

messaging.NEWS_HOOKS[:] = [f"In the news: {h}" for h in news.headlines(3)]
posts = [p for p in ctn.LegitSocial().feed_trending(limit=20) if p.get("body")]
writer = Writer()
done = set()

for _ in range(n):
    t = targeting.pick(posts, done, set())
    if not t:
        print("nothing worth replying to")
        break
    done.add(t["post_id"])
    print(f"\n--- TARGET #{t['post_id']} (score {targeting.score(t):.1f}): {t['body'][:220]}")
    print(f"    rebuttal hint: {messaging.rebuttal_for(t['body'])}")
    reply = writer.reply(t["body"], persona)
    print(f">>> REPLY as {persona} ({len(reply)} chars): {reply or '[skipped: bad output]'}")

orig = writer.original(persona)
print(f"\n>>> ORIGINAL as {persona} ({len(orig)} chars): {orig or '[skipped: bad output]'}")
