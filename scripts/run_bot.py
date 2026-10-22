"""Usage:
    python scripts/run_bot.py USERNAME [USERNAME ...] [--persona KEY] [--live-after N]
    python scripts/run_bot.py --all [--live-after N]      # the active pool (max CTN_MAX_ACTIVE = 50)

Dry run by default. Set CTN_DRY_RUN=0 to post for real, or pass --live-after N to
draft for N rounds and then post for real. With several accounts, each action is taken
by the next account in turn, using that account's saved persona (scripts/set_persona.py).
Claim the run in TEAM.md first: all accounts share the team's 3 posts/min.
"""
import argparse

import _path  # noqa: F401

from ctn_bot import accounts, bot, config

ap = argparse.ArgumentParser(usage=__doc__)
ap.add_argument("usernames", nargs="*")
ap.add_argument("--all", action="store_true")
ap.add_argument("--persona", default="", help="override every account's saved persona")
ap.add_argument("--live-after", type=int, default=None)
args = ap.parse_args()

names = accounts.active_usernames() if args.all else args.usernames
if not names:
    raise SystemExit(__doc__)
if len(names) > config.MAX_ACTIVE:
    print(f"Only {config.MAX_ACTIVE} accounts may be active at once; using the first {config.MAX_ACTIVE}.")
    names = names[: config.MAX_ACTIVE]

try:
    bot.run(names, args.persona, live_after=args.live_after)
except KeyboardInterrupt:
    print("\nstopped")
