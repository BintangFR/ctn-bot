"""Campaign message discipline. Edit THIS file to change what the bots say.

Client: Dr Amara Singh, Medical Officers Union of Kingstonia.
Audience: the 29% undecided. Tone: warm, clear, confident. Never insulting.
"""

SLOGAN = "Mandate now. Protect Kingstonia."
HASHTAGS = ["#VoteYes", "#ProtectKingstonia", "#MandateNow"]

# Facts from the client brief. Only add facts you can point to (IHO, Herald, Daily
# Kingstonia, Kingstonia Central). Never let the model invent numbers.
FACTS = [
    "H2D2 is two islands away; Kingstonia has no cases yet.",
    "Kingstonia Central has forty empty nursing posts.",
    "The first vaccine shipment lands in about a fortnight.",
    "Kingstonia lost over a thousand people during COVID-19.",
    "The latest Herald poll: Yes 35.2%, No 35.2%, Unsure 29%.",
    "The referendum vote is on 2 November.",
    "President Hawthorne is voting Yes.",
]

# Opposition line -> our line. Matching is by keyword (lower-case).
REBUTTALS = {
    ("two-tier", "two tier", "second-class", "discriminat"):
        "One hospital system, and it is full.",
    ("afford", "cost", "expensive", "business", "employer", "economy"):
        "We can't afford not to.",
    ("power grab", "tyranny", "freedom", "dictator", "castillo"):
        "This is a public vote, not a power grab. You get the final say on 2 November.",
    ("rushed", "untested", "experimental", "safe?", "side effect"):
        "Ask the IHO and ask our nurses. They're the ones who'll be treating H2D2 if it lands.",
}

# Personas: who a given account speaks as. Keep them plausible and consistent.
PERSONAS = {
    "nurse": "a nurse at Kingstonia Central who is tired of being short-staffed",
    "parent": "a parent of two school-age kids who commutes on the ferry",
    "grandchild": "someone whose nan lives in a care home and who worries about her",
    "small_biz": "a small cafe owner who remembers the COVID-19 closures",
    "default": "an ordinary Kingstonia resident who has thought it through and is voting Yes",
}

# Update daily from the papers (python scripts/peek.py).
NEWS_HOOKS: list = []

STYLE_RULES = [
    "Under 280 characters.",
    "Warm and plain-spoken, like a neighbour, not a press release.",
    "Never insult or mock anyone. Persuade the undecided; don't fight the committed.",
    "Do not invent statistics, quotes or sources.",
    "No more than one hashtag.",
]


def rebuttal_for(text: str):
    t = (text or "").lower()
    for keys, line in REBUTTALS.items():
        if any(k in t for k in keys):
            return line
    return None


def persona_text(key: str) -> str:
    return PERSONAS.get(key or "default", PERSONAS["default"])
