"""Create and log in team accounts. Credentials live in secrets/accounts.json (git-ignored)."""
import json
import secrets as pysecrets
import time

import capturethenarrative as ctn

from . import config


def _load() -> dict:
    if config.ACCOUNTS_FILE.exists():
        return json.loads(config.ACCOUNTS_FILE.read_text())
    return {}


def _save(data: dict) -> None:
    # Atomic replace: the bot and the bulk creator may both write this file. OneDrive
    # briefly locks files while syncing them, so retry rather than lose a password.
    tmp = config.ACCOUNTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    for attempt in range(20):
        try:
            tmp.replace(config.ACCOUNTS_FILE)
            break
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.5)
    try:
        config.ACCOUNTS_FILE.chmod(0o600)
    except OSError:
        pass


def list_accounts() -> dict:
    return _load()


# ---- active pool -------------------------------------------------------------
# The portal allows MAX_ACTIVE accounts active at once. Only accounts in the active pool
# ever log in or act; the rest are reserves, promoted when an active one is retired.

def _is_active(rec: dict) -> bool:
    return rec.get("active", True) and not rec.get("retired")


def active_usernames() -> list:
    return [u for u, r in _load().items() if _is_active(r)]


def reserve_usernames() -> list:
    return [u for u, r in _load().items() if not _is_active(r) and not r.get("retired")]


def set_active(username: str, active: bool) -> None:
    data = _load()
    if active and not _is_active(data[username]) and len(active_usernames()) >= config.MAX_ACTIVE:
        raise SystemExit(f"Active pool is full ({config.MAX_ACTIVE}). Deactivate one first.")
    data[username]["active"] = active
    _save(data)


def retire(username: str, why: str) -> None:
    """Take an account out of use for good (suspended, banned, or unusable)."""
    data = _load()
    if username in data:
        data[username].update({"active": False, "retired": why})
        _save(data)


def promote_reserve(persona_hint: str = ""):
    """Move one reserve into the active pool, preferring the same persona. Returns its name."""
    if len(active_usernames()) >= config.MAX_ACTIVE:
        return None
    data = _load()
    reserves = reserve_usernames()
    same = [u for u in reserves if data[u].get("persona") == persona_hint]
    pick = (same or reserves or [None])[0]
    if pick:
        data[pick]["active"] = True
        _save(data)
    return pick


def create(social: "ctn.LegitSocial", username: str, display_name: str = "", persona: str = "",
           active: bool = None):
    """Register a new account. The password is generated, saved, and can never be changed.
    active=None joins the active pool only if it has room; otherwise the account is a reserve."""
    data = _load()
    if username in data:
        raise SystemExit(f"{username} already exists in {config.ACCOUNTS_FILE}")
    if active is None:
        active = len(active_usernames()) < config.MAX_ACTIVE
    password = pysecrets.token_urlsafe(18)
    # Save BEFORE registering so a crash can't lose an unchangeable password.
    data[username] = {"password": password, "display_name": display_name, "persona": persona,
                      "active": active}
    _save(data)
    try:
        try:
            account = social.register(username, password, config.require_team_code(),
                                      display_name=display_name or None)
        except TypeError:  # older package without display_name kwarg
            account = social.register(username, password, config.require_team_code())
    except Exception:
        data.pop(username, None)
        _save(data)
        raise
    _store_session(username, account)
    return account


def login(social: "ctn.LegitSocial", username: str, fresh: bool = False):
    """Resume from the saved session token if it still works, else log in and save the token.
    fresh=True skips the token (it just failed). Logins are limited to 5/min per network
    address, so tokens matter with many accounts."""
    data = _load()
    if username not in data:
        raise SystemExit(f"No saved credentials for {username}. Run scripts/create_account.py first.")
    rec = data[username]
    if rec.get("token") and not fresh:
        try:
            return social.account_from_token(rec["token"])
        except Exception:
            pass  # expired: fall through to a fresh login
    account = social.login(username, rec["password"])
    _store_session(username, account)
    return account


def _store_session(username: str, account) -> None:
    data = _load()
    data[username]["token"] = account.token
    if account.account_id is not None:
        data[username]["account_id"] = account.account_id
    _save(data)


def persona_for(username: str) -> str:
    return _load().get(username, {}).get("persona", "")
