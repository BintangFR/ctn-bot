"""Plausible Kingstonian names and handles for new persona accounts."""
import random

from . import messaging

FIRST = ["Aroha", "Ben", "Chloe", "Daniel", "Elena", "Finn", "Gemma", "Hamish", "Ines", "Jack",
         "Kiri", "Liam", "Maya", "Noah", "Olivia", "Pita", "Quinn", "Ruby", "Sione", "Tara",
         "Uli", "Vika", "Will", "Xavier", "Yasmin", "Zoe", "Amir", "Bella", "Callum", "Dina",
         "Eli", "Fatima", "George", "Hina", "Isaac", "Jade", "Kofi", "Lena", "Mateo", "Nia",
         "Oscar", "Paige", "Rangi", "Sofia", "Tevita", "Una", "Vince", "Wiremu", "Yuki", "Zara",
         "Anika", "Brody", "Carmen", "Dev", "Esther", "Felix", "Grace", "Harry", "Ivy", "Josh"]
LAST = ["Taufa", "Brown", "Nguyen", "Wilson", "Fonoti", "Clarke", "Singh", "Murphy", "Tupou",
        "Hughes", "Ramos", "Chen", "Kaufana", "Evans", "Doyle", "Fifita", "Grant", "Ito", "Kelly",
        "Lopez", "Mahe", "Nash", "Ortiz", "Pule", "Quigley", "Reyes", "Sato", "Thomson", "Vaka",
        "Walker", "Young", "Aziz", "Bishop", "Cruz", "Dunn", "Ellis", "Faleafa", "Gill", "Hart"]
# Handle styles per persona, so a name hints at who is speaking.
HANDLE = {
    "student": ["{f}.{l}", "{f}_uni", "{f}{n}", "ku_{f}"],
    "small_biz": ["{f}s_cafe", "{f}.{l}.shop", "{l}_and_co", "{f}_bakes"],
    "nurse": ["nurse_{f}", "{f}.rn", "{f}_on_shift", "{f}{l}_rn"],
    "parent": ["{f}.{l}", "parentof2_{f}", "{f}_schoolrun", "{l}_family"],
    "grandchild": ["{f}_and_nan", "{f}.{l}", "{f}{n}"],
    "retiree": ["{f}.{l}{n}", "retired_{f}", "{f}_in_kc", "{l}{n}_retired"],
    "tourism_worker": ["{f}_resort", "{f}.dives", "{f}_tours"],
    "bus_driver": ["route{n}_{f}", "{f}_drives", "ferry_{f}"],
    "fisher": ["{f}_fishes", "outer_isle_{f}", "{f}_reef"],
    "tech_worker": ["{f}.dev", "{f}_codes", "{f}{l}_eng"],
    "teacher": ["teacher_{l}", "{f}_teaches", "{f}.{l}.edu"],
    "default": ["{f}.{l}", "{f}_{l}", "{f}{n}", "{f}_kingstonia"],
}


def generated(n: int, taken: set, rng=None, persona: str = "") -> list:
    """n (username, display, persona) tuples, personas spread evenly (or all `persona`),
    none in `taken`."""
    rng = rng or random.Random(2026)
    personas = [persona] if persona else list(messaging.PERSONAS)
    out = []
    while len(out) < n:
        p = personas[len(out) % len(personas)]
        f, l = rng.choice(FIRST), rng.choice(LAST)
        u = rng.choice(HANDLE[p]).format(f=f.lower(), l=l.lower(), n=rng.randint(2, 99))
        if u not in taken:
            taken.add(u)
            out.append((u, f"{f} {l}", p))
    return out
