"""Usage: python scripts/run_bot.py USERNAME [persona]

Dry run by default. Set CTN_DRY_RUN=0 to post for real. Claim the run in TEAM.md first.
"""
import sys

import _path  # noqa: F401

from ctn_bot import bot

if len(sys.argv) < 2:
    raise SystemExit(__doc__)

try:
    bot.run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
except KeyboardInterrupt:
    print("\nstopped")
