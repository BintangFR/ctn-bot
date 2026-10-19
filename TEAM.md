# Team coordination

## Who is running what right now
| Person | Script / account | Started (Sydney time) | Notes |
|--------|------------------|-----------------------|-------|
| Bintang | run_bot.py --all --live-after 0 (26 accounts, Ollama qwen2.5:7b) | 2026-10-19 23:18 | LIVE; uses most of the team's 3 posts/min. monitor.py --every 120 also running |

## Accounts (usernames only — passwords live in secrets/accounts.json, never here)
| Username | Persona | Owner |
|----------|---------|-------|
| Bintang ("R A T") | student | Bintang |
| + 25 persona accounts (mia.tavita … annie_newhaven) | see `python scripts/set_persona.py` | Bintang |

## Daily checklist
- [ ] Read both papers (python scripts/peek.py)
- [ ] Update `NEWS_HOOKS` / talking points in messaging.py if a new story broke
- [ ] Review logs/suspects.csv and report confirmed bots via the site
- [ ] Check how citizens reacted to yesterday's posts; drop lines that flopped
