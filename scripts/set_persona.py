"""Choose who an account speaks as.

Usage:
    python scripts/set_persona.py                     # list accounts and persona options
    python scripts/set_persona.py USERNAME student    # use a built-in persona
    python scripts/set_persona.py USERNAME "a retired ferry captain from the outer islands"

Built-in personas live in ctn_bot/messaging.py (PERSONAS). Anything else is used as a
custom description. Restart the account's bot for the change to take effect.
"""
import sys

import _path  # noqa: F401

from ctn_bot import accounts, messaging

data = accounts.list_accounts()

if len(sys.argv) < 3:
    print("Accounts:")
    for u, a in data.items():
        key = a.get("persona", "")
        print(f"  @{u:<20} {messaging.persona_label(key):<30} {key}")
    print("\nPersonas:")
    for key, p in messaging.PERSONAS.items():
        print(f"  {key:<15} {p['label']:<30} {p['who']}")
    print('\nOr give your own description in quotes, e.g. "a retired ferry captain from the outer islands".')
    raise SystemExit(0)

username, persona = sys.argv[1], sys.argv[2].strip()
if username not in data:
    raise SystemExit(f"No saved account @{username}. Add it with scripts/add_account.py first.")
if persona not in messaging.PERSONAS and len(persona.split()) < 3:
    raise SystemExit(f"'{persona}' isn't a built-in persona. Use a key from the list, "
                     "or describe the person in a few words (in quotes).")
data[username]["persona"] = persona
accounts._save(data)
print(f"@{username} now speaks as: {messaging.persona_text(persona)}")
