"""Create the team's persona accounts in one go. Each gets its own random password,
saved (with its session token) to secrets/accounts.json before/after registering.

Usage: python scripts/create_accounts_bulk.py [how_many]

Account creation is limited to 5/min per network address; the package waits and retries,
so 25 accounts take about 5 minutes. Usernames already taken get a number appended.
Existing entries in secrets/accounts.json are skipped, so it is safe to re-run.
"""
import random
import sys

import _path  # noqa: F401
import capturethenarrative as ctn

from ctn_bot import accounts, messaging

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

n = int(sys.argv[1]) if len(sys.argv) > 1 else len(ROSTER)
social = ctn.LegitSocial()
existing = accounts.list_accounts()
made = 0

for username, display, persona in ROSTER[:n]:
    if username in existing:
        print(f"skip @{username}: already saved")
        continue
    for attempt in range(3):
        name = username if attempt == 0 else f"{username}{random.randint(10, 99)}"
        try:
            acct = accounts.create(social, name, display, persona)
            made += 1
            print(f"created @{name} ({display}) as {messaging.persona_label(persona)}, id {acct.account_id}")
            break
        except SystemExit:
            raise
        except Exception as e:
            msg = str(e)
            if "409" in msg or "taken" in msg.lower() or "exists" in msg.lower():
                continue  # username taken: try with a number
            print(f"failed @{name}: {msg}")
            break

print(f"\n{made} new accounts. All credentials are in secrets/accounts.json; back it up privately.")
