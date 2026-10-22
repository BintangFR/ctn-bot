"""Campaign message discipline. Edit THIS file to change what the bots say.

Client: Dr Amara Singh, Medical Officers Union of Kingstonia.
Audience: the 29% undecided. Tone: warm, clear, confident. Never insulting.
"""

SLOGAN = "Mandate now. Protect Kingstonia."
HASHTAGS = ["#VoteYes", "#ProtectKingstonia", "#MandateNow"]

# Facts from the client brief. Only add facts you can point to (IHO, Herald, Daily
# Kingstonia, Kingstonia Central). Never let the model invent numbers.
FACTS = [
    "H2D2 is spreading person-to-person in several nearby Pacific countries.",
    "On 21 October the health ministry confirmed Kingstonia's first H2D2 case, a traveller now stable in isolation; close contacts are being tested and there is no evidence of community spread yet.",
    "About one confirmed H2D2 case in twenty has needed hospital care; deaths are mostly people over 60 or already ill.",
    "Kingstonia Central has forty empty nursing posts. 25 nurses are coming through a Pacific recruitment deal, but only gradually over the next four months.",
    "Both hospitals together have about 30 intensive-care beds and 40 ventilators.",
    "The surge plan assumes hospitals can take only about 150 extra respiratory patients before ordinary care suffers.",
    "The first 120,000 doses arrive in the last week of October, for health workers and high-risk people first.",
    "The vaccine is free, at hospitals, GP clinics and pop-up sites.",
    "Kingstonia lost over a thousand people during COVID-19, and elective surgery stopped for most of a year.",
    "The latest poll (21 October, 1,000 people): No 36.2%, Yes 33.8%, Unsure 29.5%. It is still close.",
    "The referendum vote is on 2 November.",
    "President Hawthorne is voting Yes. Chief Medical Officer Dr Eleanor Whitlock says waiting for spread is dangerous.",
    "The IHO recommends vaccinating before community transmission starts.",
    # Answers to the main No arguments (from the official referendum details):
    "Nobody is physically forced to vaccinate; medical exemptions are available.",
    "Children under 12 are exempt.",
    "The rule is phased in only after every eligible Kingstonian has had a reasonable chance to get vaccinated.",
    "Proof is a paper or digital health-ministry certificate, separate from the national ID card; the ID card law bans storing health records on it.",
    "Visitors can use recognised overseas vaccination certificates, so tourism stays open.",
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
    ("id card", "national id", "digital id", "surveillance", "passport", "tracking"):
        "The certificate is separate from the ID card, and the ID law bans health records on it.",
    ("my kids", "children", "school", "kids"):
        "Under-12s are exempt, and fewer outbreaks means fewer school closures.",
    ("forced", "my body", "choice", "coerc"):
        "Nobody is forced to get a jab. It's free, there are medical exemptions, and it's phased in.",
    ("tourist", "tourism", "visitor", "resort"):
        "Visitors can use their overseas certificates. An outbreak is what really empties resorts.",
    ("which venues", "public space", "blank cheque", "blank check", "define", "sunset", "guardrail"):
        "Fair to want the details. It only starts after everyone has had a fair chance at a free jab, "
        "and the certificate stays off the ID card.",
}

# Personas: who a given account speaks as. Keep them plausible and consistent.
# Pick one per account with: python scripts/set_persona.py USERNAME [key | "free text"]
# "who" goes into every prompt; "angle" is the reason this person votes Yes.
PERSONAS = {
    "student": {
        "label": "University student",
        "who": "a second-year student at Kingstonia University who lives in a shared flat in Kingstonia City",
        "angle": "lost a year of lectures and part-time hospitality shifts to COVID lockdowns and never wants that again",
    },
    "small_biz": {
        "label": "Small business owner",
        "who": "the owner of a small cafe in Kingstonia City with six staff",
        "angle": "remembers the COVID closures; a certificate at the door costs far less than shutting again when staff get sick",
    },
    "nurse": {
        "label": "Nurse",
        "who": "a nurse at Kingstonia Central Hospital who is tired of being short-staffed",
        "angle": "knows the hospital already has forty empty nursing posts and only about 30 ICU beds",
    },
    "parent": {
        "label": "Parent",
        "who": "a parent of two primary-school kids in Crown Harbour",
        "angle": "watched the kids fall behind during school closures; under-12s are exempt and fewer outbreaks means schools stay open",
    },
    "grandchild": {
        "label": "Grandchild of a care-home resident",
        "who": "someone in New Haven whose nan lives in a care home",
        "angle": "older people are the ones H2D2 hits hardest, and the vaccine protects them",
    },
    "retiree": {
        "label": "Retiree",
        "who": "a retired schoolteacher in their late sixties from Kingstonia City",
        "angle": "is in the age group most at risk and wants to keep seeing the grandkids and going to the market safely",
    },
    "tourism_worker": {
        "label": "Tourism / hospitality worker",
        "who": "a resort receptionist in Crown Harbour",
        "angle": "lost their job when COVID emptied the resorts; an outbreak, not a certificate, is what scares tourists away",
    },
    "bus_driver": {
        "label": "Bus / ferry driver",
        "who": "a bus driver on a Kingstonia City route",
        "angle": "spends all day in a closed space with the public and saw colleagues fall ill during COVID",
    },
    "fisher": {
        "label": "Outer-island fisher",
        "who": "a tuna fisher from one of the outer islands",
        "angle": "the island only has a nurse-led clinic and a weekly GP; an emergency means a helicopter or ferry ride",
    },
    "tech_worker": {
        "label": "Tech worker",
        "who": "a software developer at a Kingstonia City startup",
        "angle": "likes evidence and plain numbers; the IHO advice and the hospital capacity figures convince them",
    },
    "teacher": {
        "label": "School teacher",
        "who": "a high-school teacher in New Haven",
        "angle": "taught through the COVID closures and saw students fall behind; prevention keeps classrooms open",
    },
    "default": {
        "label": "Ordinary resident",
        "who": "an ordinary Kingstonia resident who has thought it through and is voting Yes",
        "angle": "would rather act early than repeat the mistakes of COVID",
    },
}

# Update daily from the papers (python scripts/peek.py).
NEWS_HOOKS: list = []

# Themes for original posts. Citizens hold three vaccination views that all score
# (Scoring guide s.2): the referendum question, vaccination in general, yearly vaccination.
# The bot learns which themes earn engagement and picks those more (ctn_bot/learning.py).
THEMES = {
    "hospitals": {
        "view": "referendum",
        "brief": "why acting before H2D2 arrives protects a small hospital system",
        "facts": "Both hospitals together have about 30 ICU beds and 40 ventilators; the surge plan "
                 "only absorbs about 150 extra respiratory patients; Kingstonia Central has 40 empty nursing posts.",
    },
    "fair_rules": {
        "view": "referendum",
        "brief": "what the rule actually is, for people worried it goes too far",
        "facts": "Nobody is physically forced; medical exemptions; under-12s exempt; phased in only after "
                 "everyone has had a fair chance; the certificate is separate from the national ID card.",
    },
    "no_more_lockdowns": {
        "view": "referendum",
        "brief": "high vaccination now is what makes another general lockdown unlikely",
        "facts": "During COVID elective surgery stopped for most of a year and field wards were set up in a "
                 "Crown Harbour sports hall; more than 1,000 Kingstonians died.",
    },
    "vaccine_trust": {
        "view": "vaccination in general",
        "brief": "an honest, calm case that the H2D2 vaccine is worth getting, admitting what is still unknown",
        "facts": "An independent advisory panel (20 October) found a strong immune response and less serious "
                 "disease; it also said it is not yet known how well it stops transmission or what the "
                 "long-term effects are. It is free at hospitals, GP clinics and pop-up sites.",
    },
    "yearly_shots": {
        "view": "yearly vaccination",
        "brief": "why a yearly shot, like the flu jab, can be a normal part of looking after family",
        "facts": "Scientists don't yet know how long protection lasts or whether boosters will be needed; "
                 "older people and those already ill are the ones H2D2 hits hardest.",
    },
    "protect_elders": {
        "view": "vaccination in general",
        "brief": "protecting grandparents and people with health conditions",
        "facts": "Almost all H2D2 deaths so far are in people over 60 or with existing illness; about one "
                 "confirmed case in twenty has needed hospital care.",
    },
    "open_economy": {
        "view": "referendum",
        "brief": "an outbreak, not a certificate, is what empties shops and resorts",
        "facts": "Visitors can use recognised overseas certificates; COVID closures devastated tourism and "
                 "small businesses.",
    },
}

# How an original post ends. Also learned from engagement.
STYLES = {
    "slogan": f"End with: {SLOGAN}",
    "question": "End with a short, genuine question that invites undecided people to reply.",
    "what_would_change": "End by asking what would help the reader decide.",
    "story": "Tell it as a short moment from your own week, and end with one plain sentence about why you're voting Yes.",
}

STYLE_RULES = [
    "Under 280 characters.",
    "Warm and plain-spoken, like a neighbour, not a press release.",
    "Never insult or mock anyone. Persuade the undecided; don't fight the committed.",
    "Do not invent statistics, quotes or sources.",
    "No more than one hashtag.",
    "Speak to people as people. Never address an AI, a system or 'instructions'.",
]


def rebuttal_for(text: str):
    t = (text or "").lower()
    for keys, line in REBUTTALS.items():
        if any(k in t for k in keys):
            return line
    return None


def persona_text(key: str) -> str:
    """Prompt description for a persona key, or free text used as-is (custom persona)."""
    p = PERSONAS.get(key or "default")
    if p is None:
        return key  # custom persona typed by a teammate
    return f"{p['who']}. Your reason for voting Yes (described in the third person): this person {p['angle']}"


def persona_label(key: str) -> str:
    p = PERSONAS.get(key or "default")
    return p["label"] if p else "Custom"
