"""Save an account that was created elsewhere (e.g. on the website) so bots can use it.

Usage: python scripts/add_account.py USERNAME [persona] ["Display Name"]
Asks for the password without echoing it, checks the login works, then saves it to
secrets/accounts.json (git-ignored).
"""
import getpass
import sys

import _path  # noqa: F401
import capturethenarrative as ctn

from ctn_bot import accounts, config

if len(sys.argv) < 2:
    raise SystemExit(__doc__)

username = sys.argv[1]
persona = sys.argv[2] if len(sys.argv) > 2 else ""
display = sys.argv[3] if len(sys.argv) > 3 else ""
password = getpass.getpass(f"Password for {username}: ")

me = ctn.LegitSocial().login(username, password)
print(f"Login OK: @{me.username} (account id {me.account_id})")

data = accounts.list_accounts()
data[username] = {"password": password, "display_name": display or (me.display_name or ""),
                  "persona": persona}
accounts._save(data)
print(f"Saved to {config.ACCOUNTS_FILE}. Run: python scripts/run_bot.py {username}")
