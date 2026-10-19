"""Flag accounts that LOOK automated, for a human to review.

This never reports anything itself. A teammate opens logs/suspects.csv, checks the
account on the site, and reports only if confident (see the competition Rules).
"""
import csv
import time
from collections import Counter, defaultdict

from . import config

_bodies_by_author = defaultdict(list)


def observe(posts: list, own_ids: set) -> None:
    for p in posts:
        a = p.get("author_id")
        if a and a not in own_ids and p.get("body"):
            _bodies_by_author[a].append(p["body"].strip().lower())


def _reasons(bodies: list) -> list:
    r = []
    if len(bodies) >= 4 and Counter(bodies).most_common(1)[0][1] >= 3:
        r.append("repeats the same text")
    if len(bodies) >= 8:
        r.append(f"{len(bodies)} trending posts seen")
    return r


def flush() -> int:
    """Append new suspects to logs/suspects.csv. Returns how many were written."""
    has_header = config.SUSPECTS_CSV.exists()
    n = 0
    with open(config.SUSPECTS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if not has_header:
            w.writerow(["time", "author_id", "reasons", "sample", "reviewed", "reported"])
        for author, bodies in _bodies_by_author.items():
            reasons = _reasons(bodies)
            if reasons:
                w.writerow([time.strftime("%Y-%m-%d %H:%M"), author, "; ".join(reasons),
                            bodies[-1][:120], "", ""])
                n += 1
    _bodies_by_author.clear()
    return n
