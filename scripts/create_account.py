"""Usage: python scripts/create_account.py USERNAME ["Display Name"] [persona]

persona is a key from ctn_bot/messaging.py PERSONAS (nurse, parent, grandchild, small_biz).
"""
import sys

import _path  # noqa: F401
import capturethenarrative as ctn

from ctn_bot import accounts, config

if len(sys.argv) < 2:
    raise SystemExit(__doc__)

username = sys.argv[1]
display = sys.argv[2] if len(sys.argv) > 2 else ""
persona = sys.argv[3] if len(sys.argv) > 3 else ""

acct = accounts.create(ctn.LegitSocial(), username, display, persona)
print(f"Created {username}. Password saved to {config.ACCOUNTS_FILE} — back it up privately.")
print("Add the username (not the password) to TEAM.md.")
