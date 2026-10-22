"""Create the team's persona accounts in one go. Each gets its own random password,
saved (with its session token) to secrets/accounts.json before/after registering.

Usage: python scripts/create_accounts_bulk.py [total]     # default: fill up to CTN_MAX_ACCOUNTS (200)

New accounts join the active pool only while it has fewer than CTN_MAX_ACTIVE (50);
the rest are reserves that never log in or act until promoted (scripts/pool.py).
Account creation is limited to 5/min per network address; the package waits and retries,
so 100 accounts take about 20 minutes. Usernames already taken get a number appended.
Existing entries in secrets/accounts.json are skipped, so it is safe to re-run.
"""
import random
import sys

import _path  # noqa: F401
import capturethenarrative as ctn

from ctn_bot import accounts, config, messaging
from ctn_bot.roster import generated

# (username, display name, persona key). Varied, plausible Kingstonians.
ROSTER = [
    ("mia.tavita", "Mia Tavita", "student"),
    ("jono_harbourside", "Jono Reid", "small_biz"),
    ("sina.nurse.kc", "Sina Faleolo", "nurse"),
    ("dad_of_two_ch", "Ben Okafor", "parent"),
    ("lucy_nh", "Lucy Harrington", "grandchild"),
    ("mrs.pereira", "Ana Pereira", "retiree"),
    ("kai.resortlife", "Kai Mendes", "tourism_worker"),
    ("route9_raj", "Raj Patel", "bus_driver"),
    ("tuna_tomasi", "Tomasi Vea", "fisher"),
    ("devon.codes", "Devon Liu", "tech_worker"),
    ("mr_alder_teaches", "Sam Alder", "teacher"),
    ("hana.kuni", "Hana Kimura", "student"),
    ("bakery_on_mill", "Rosa Delgado", "small_biz"),
    ("nightshift_ellie", "Ellie Martin", "nurse"),
    ("crownharbour_mum", "Priya Nair", "parent"),
    ("grandpa_joe_kc", "Joe Whitfield", "retiree"),
    ("leilani.dives", "Leilani Moana", "tourism_worker"),
    ("ferry_frank", "Frank O'Neill", "bus_driver"),
    ("outer_isle_ana", "Ana Lealaiauloto", "fisher"),
    ("chit_engineer", "Marcus Tan", "tech_worker"),
    ("ms_okoro", "Grace Okoro", "teacher"),
    ("theo.kingstonia", "Theo Brennan", "default"),
    ("nan_visits_sundays", "Isla Fraser", "grandchild"),
    ("uni_kieran", "Kieran Walsh", "student"),
    ("annie_newhaven", "Annie Lowe", "default"),
]

total = min(int(sys.argv[1]) if len(sys.argv) > 1 else config.MAX_ACCOUNTS, config.MAX_ACCOUNTS)
social = ctn.LegitSocial()
existing = accounts.list_accounts()
need = total - len(existing)
if need <= 0:
    raise SystemExit(f"Already {len(existing)} accounts (target {total}).")
todo = [r for r in ROSTER if r[0] not in existing]
todo += generated(max(need - len(todo), 0), set(existing) | {r[0] for r in ROSTER})
todo = todo[:need]
print(f"{len(existing)} accounts now; creating {len(todo)} to reach {total}. "
      f"Active pool: {len(accounts.active_usernames())}/{config.MAX_ACTIVE}.")
made = 0

for username, display, persona in todo:
    if username in existing:
        print(f"skip @{username}: already saved")
        continue
    for attempt in range(3):
        name = username if attempt == 0 else f"{username}{random.randint(10, 99)}"
        try:
            acct = accounts.create(social, name, display, persona)
            made += 1
            pool = "ACTIVE" if name in accounts.active_usernames() else "reserve"
            print(f"created @{name} ({display}) as {messaging.persona_label(persona)}, "
                  f"id {acct.account_id} [{pool}]")
            break
        except SystemExit:
            raise
        except Exception as e:
            msg = str(e)
            if "409" in msg or "taken" in msg.lower() or "exists" in msg.lower():
                continue  # username taken: try with a number
            print(f"failed @{name}: {msg}")
            if "limit" in msg.lower() or "maximum" in msg.lower() or "403" in msg:
                raise SystemExit("The portal refused more accounts; stopping.")
            break

print(f"\n{made} new accounts. All credentials are in secrets/accounts.json; back it up privately.")
