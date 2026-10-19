"""Usage: python scripts/run_bot.py USERNAME [persona] [--live-after N]

Dry run by default. Set CTN_DRY_RUN=0 to post for real, or pass --live-after N to
draft for N rounds and then post for real. Claim the run in TEAM.md first.
Persona defaults to the one saved with scripts/set_persona.py.
"""
import argparse

import _path  # noqa: F401

from ctn_bot import bot

ap = argparse.ArgumentParser(usage=__doc__)
ap.add_argument("username")
ap.add_argument("persona", nargs="?", default="")
ap.add_argument("--live-after", type=int, default=None)
args = ap.parse_args()

try:
    bot.run(args.username, args.persona, live_after=args.live_after)
except KeyboardInterrupt:
    print("\nstopped")
