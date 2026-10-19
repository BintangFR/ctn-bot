"""Headlines from the Daily Kingstonia and the Kingstonia Herald."""
import capturethenarrative as ctn


def latest(n: int = 5) -> list:
    try:
        return list(ctn.NewsSites().latest(n))
    except Exception as e:
        print("news unavailable:", e)
        return []


def headlines(n: int = 5) -> list:
    out = []
    for a in latest(n):
        site = (a.get("site") or {}).get("name", "?")
        out.append(f"{site}: {a.get('title', '')}")
    return out
