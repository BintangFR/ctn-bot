"""Create and log in team accounts. Credentials live in secrets/accounts.json (git-ignored)."""
import json
import secrets as pysecrets

import capturethenarrative as ctn

from . import config


def _load() -> dict:
    if config.ACCOUNTS_FILE.exists():
        return json.loads(config.ACCOUNTS_FILE.read_text())
    return {}


def _save(data: dict) -> None:
    config.ACCOUNTS_FILE.write_text(json.dumps(data, indent=2))
    try:
        config.ACCOUNTS_FILE.chmod(0o600)
    except OSError:
        pass


def list_accounts() -> dict:
    return _load()


def create(social: "ctn.LegitSocial", username: str, display_name: str = "", persona: str = ""):
    """Register a new account. The password is generated, saved, and can never be changed."""
    data = _load()
    if username in data:
        raise SystemExit(f"{username} already exists in {config.ACCOUNTS_FILE}")
    password = pysecrets.token_urlsafe(18)
    # Save BEFORE registering so a crash can't lose an unchangeable password.
    data[username] = {"password": password, "display_name": display_name, "persona": persona}
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
    return account


def login(social: "ctn.LegitSocial", username: str):
    data = _load()
    if username not in data:
        raise SystemExit(f"No saved credentials for {username}. Run scripts/create_account.py first.")
    return social.login(username, data[username]["password"])


def persona_for(username: str) -> str:
    return _load().get(username, {}).get("persona", "")
