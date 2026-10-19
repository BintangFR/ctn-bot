"""Print trending posts and latest news. No login needed."""
import _path  # noqa: F401
import capturethenarrative as ctn

from ctn_bot import news, targeting

print("=== Trending on Legit Social ===")
for p in ctn.LegitSocial().feed_trending(limit=15):
    print(f"[{targeting.score(p):4.1f}] {p.get('post_id')} @{p.get('author_id')}: "
          f"{(p.get('body') or '')[:140]}")

print("\n=== Latest news ===")
for h in news.headlines(8):
    print("-", h)
