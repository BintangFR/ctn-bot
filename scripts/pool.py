"""See and change which accounts are in the active pool (max CTN_MAX_ACTIVE, default 50).

Usage:
    python scripts/pool.py                         # summary + active accounts
    python scripts/pool.py --reserves              # also list reserves
    python scripts/pool.py swap OLD NEW            # deactivate OLD, activate NEW
    python scripts/pool.py off USERNAME            # move to reserves
    python scripts/pool.py on USERNAME             # move to active (only if there is room)

Restart the bot after changing the pool.
"""
import sys
from collections import Counter

import _path  # noqa: F401

from ctn_bot import accounts, config, messaging

args = sys.argv[1:]
if args[:1] == ["swap"] and len(args) == 3:
    accounts.set_active(args[1], False)
    accounts.set_active(args[2], True)
    print(f"@{args[1]} -> reserve, @{args[2]} -> active")
elif args[:1] in (["on"], ["off"]) and len(args) == 2:
    accounts.set_active(args[1], args[0] == "on")
    print(f"@{args[1]} -> {'active' if args[0] == 'on' else 'reserve'}")
elif args and args[0] != "--reserves":
    raise SystemExit(__doc__)

data = accounts.list_accounts()
active, reserves = accounts.active_usernames(), accounts.reserve_usernames()
retired = [u for u, r in data.items() if r.get("retired")]
print(f"{len(data)}/{config.MAX_ACCOUNTS} accounts: {len(active)}/{config.MAX_ACTIVE} active, "
      f"{len(reserves)} reserves, {len(retired)} retired")
print("Active personas:", dict(Counter(data[u].get("persona") or "default" for u in active)))
print("\nActive:")
for u in active:
    print(f"  @{u:<24} {messaging.persona_label(data[u].get('persona', ''))}")
if "--reserves" in args:
    print("\nReserves:")
    for u in reserves:
        print(f"  @{u:<24} {messaging.persona_label(data[u].get('persona', ''))}")
for u in retired:
    print(f"  retired @{u}: {data[u]['retired']}")
