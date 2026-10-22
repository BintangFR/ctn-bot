# ctn-bot — Vote Yes campaign bots (Capture the Narrative)

Client: Dr Amara Singh, Medical Officers Union of Kingstonia.
Goal: make **Yes** the sensible thing to say out loud before the vote on **2 November 2026**.
Target: the 29% undecided.

> Mandate now. Protect Kingstonia.

## Layout

```
ctn_bot/
  config.py      settings loaded from .env (team code, dry-run, loop timing)
  accounts.py    create / log in accounts, credentials saved to secrets/accounts.json
  messaging.py   house rules, core lines, rebuttals, personas  <- edit this most
  llm.py         prompts + output checks for qwen2.5-3b-instruct
  news.py        Daily Kingstonia / Kingstonia Herald headlines for context
  targeting.py   picks which trending posts are worth a reply
  suspects.py    flags likely opposition bots for HUMAN review (no auto-reporting)
  state.py       remembers what we've replied to, logs every action
  bot.py         the main loop
  scraper.py     collects every article (full text) from both papers into data/news/
  dashboard.py   builds the snapshot shown by dashboard.html
scripts/
  create_account.py   make a new team account
  peek.py             print trending posts + latest news (no login needed)
  run_bot.py          run one bot
  monitor.py          scrape news + refresh dashboard every 5 min
dashboard.html   open in a browser while monitor.py runs (reloads every 30s)
data/news/       articles.json + one .md per article (git-ignored)
logs/            actions.jsonl, suspects.csv (git-ignored)
secrets/         accounts.json (git-ignored — NEVER commit)
```

## Monitoring

```bash
python scripts/monitor.py          # leave running in its own terminal, then open dashboard.html
python scripts/monitor.py --once   # one refresh
```

The dashboard shows bot status (running/stopped, dry run or live), every bot action,
live likes/replies on our posts, the competition calendar and multipliers, trending posts
and tags, all news with full text and search, flagged suspects, and team accounts
(no passwords). Each refresh costs 1 feed read + ~30 light reads of the team allowance.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then put your team code in .env
```

## Use

```bash
python scripts/peek.py                         # look around first
python scripts/create_account.py nurse_jo "Jo, Kingstonia Central" nurse
python scripts/run_bot.py nurse_jo             # DRY RUN by default: prints, doesn't post
CTN_DRY_RUN=0 python scripts/run_bot.py nurse_jo   # live
```

### Running unattended (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1   # Ollama + watchdog + bot (live) + monitor
powershell -ExecutionPolicy Bypass -File scripts\stop_all.ps1    # stop all of it
```

Each job runs in a hidden window that restarts it if it stops (`scripts/supervise.ps1`);
output goes to `logs\bot.out`, `logs\monitor.out`, `logs\ollama.out`. The watchdog restarts
Ollama when it hangs (process alive, requests timing out). A "CTN bot" scheduled task can run
`start_all.ps1` at logon and every 15 minutes; it is safe to run repeatedly.

Passwords **cannot be changed** on Legit Social. `create_account.py` generates one and
saves it to `secrets/accounts.json`. Back that file up somewhere private (not git).

## Team rules for running bots

Rate limits are **shared across the whole team** (3 posts/replies/reposts per minute,
3 LLM requests per minute, 1 LLM request at a time). So:

- Only one live bot loop at a time unless agreed in chat. Claim it in `TEAM.md`.
- Every LLM output is checked before posting; skipped rounds are fine.
- Every request to the LLM is logged by the organisers. Keep it clean.
- Read the competition Rules and Scoring guide. If unsure, ask in `#questions`.
- Reporting: `suspects.py` only *flags*. A human checks each one before reporting
  (bad reports may cost points and annoy real citizens).

## Message discipline

Edit `ctn_bot/messaging.py`, not the prompts scattered through code. Core lines:

- "Mandate now. Protect Kingstonia."
- Two-tier society? → "One hospital system, and it is full."
- Can't afford it? → "We can't afford not to."
- Cite real in-world sources (IHO, Kingstonia Central nurses, Herald/Daily Kingstonia
  articles). Don't invent numbers.
