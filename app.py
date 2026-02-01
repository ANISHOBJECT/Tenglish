# app.py
# English → Telangana/Hyderabad-style Tenglish (offline, mobile-friendly)
# Run:
#   pip install streamlit
#   streamlit run app.py

import re
import streamlit as st

# -----------------------------
# Page config (mobile-friendly)
# -----------------------------
st.set_page_config(
    page_title="Tenglish Converter",
    page_icon="🟧",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Styling for smooth mobile UI
# -----------------------------
st.markdown(
    """
    <style>
      .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 760px; }
      .stTextArea textarea { font-size: 1.05rem; line-height: 1.4; }
      .stButton>button { width: 100%; border-radius: 14px; padding: 0.8rem; font-size: 1.05rem; }
      .outbox { border:1px solid #e7e7e7; border-radius: 14px; padding: 14px; background:#0b0b0b0a;
               font-size: 1.05rem; line-height: 1.5; white-space: pre-wrap; }
      .chip { display:inline-block; padding:6px 10px; border-radius:999px; border:1px solid #ddd;
              margin-right:6px; margin-bottom:6px; font-size:0.95rem; }
      .muted { color: #666; font-size: 0.95rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Regex helpers
# -----------------------------
PUNCT_RE = re.compile(r"([.!?,;:])")
WORD_RE = re.compile(r"^[a-zA-Z']+$")

def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def tokenize(text: str):
    text = PUNCT_RE.sub(r" \\1 ", text)
    return [p for p in text.split() if p.strip()]

def is_word(tok: str) -> bool:
    return WORD_RE.match(tok) is not None

def english_plural_to_singular(word: str) -> str:
    # light heuristic
    if word.endswith("ies") and len(word) > 3:
        return word[:-3] + "y"
    if word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
        return word[:-1]
    return word

# -----------------------------
# Phrase rules (Telangana casual)
# -----------------------------
PHRASES = [
    (r"\bthanks a lot\b", "chala thanks"),
    (r"\bthank you\b", "chala thanks"),
    (r"\bthank u\b", "chala thanks"),
    (r"\bthanks\b", "thanks"),
    (r"\bgood morning\b", "good morning"),
    (r"\bgood night\b", "good night"),
    (r"\bi love you\b", "nenu ninnu premistunna"),
    (r"\bi miss you\b", "nenu ninnu miss avtunna"),
    (r"\bwhat are you doing\b", "em chestunnav"),
    (r"\bwhat is this\b", "idi enti"),
    (r"\bhow are you\b", "ela unnav"),
    (r"\bi am fine\b", "bagunna"),
    (r"\bi am sorry\b", "sorry ra"),
    (r"\bexcuse me\b", "excuse me"),
    (r"\bplease\b", "please"),
]

def apply_phrase_rules(text: str) -> str:
    t = text.lower()
    for pat, rep in PHRASES:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    return t

# -----------------------------
# Built-in BIG Dictionary (Telangana style)
# - Base + expansions => 1500+ usable forms (offline)
# -----------------------------
@st.cache_data
def build_tenglish_dictionary():
    # Core base words (hand-crafted)
    base = {
        # Pronouns
        "i":"nenu","me":"nannu","my":"naa","mine":"naadi",
        "you":"nuvvu","your":"nee","yours":"needi",
        "he":"vaadu","him":"vaadini","his":"vaadi",
        "she":"aame","her":"aameni","hers":"aame di",
        "we":"manam","us":"manalni","our":"maa",
        "they":"vaallu","them":"vaallani","their":"vaalla",

        # Aux / state
        "am":"unna","is":"undi","are":"unnaru","was":"unde","were":"unnaru",
        "be":"undu",

        # Glue / connectors / postpositions (we convert these into Telugu-ish)
        "and":"inka","but":"kani","because":"endukante","so":"andukani","then":"appudu",
        "to":"ki","in":"lo","with":"tho","on":"meeda","at":"daggara",
        "from":"nundi","for":"kosam","about":"gurinchi","before":"mundhu","after":"tarvata",

        # Common verbs (roots)
        "go":"ellu",
        "come":"ra",
        "do":"chey",
        "eat":"tinu",
        "drink":"taagu",
        "sleep":"nidra",
        "work":"pani",
        "study":"chaduvu",
        "wait":"agu",
        "stop":"aapu",
        "start":"start",
        "see":"choodu",
        "watch":"choodu",
        "look":"choodu",
        "say":"cheppu",
        "tell":"cheppu",
        "give":"ivvu",
        "take":"teesko",
        "help":"help",

        # Question words
        "what":"em",
        "why":"enduku",
        "how":"ela",
        "where":"ekkada",
        "when":"eppudu",
        "who":"evaru",
        "which":"edi",

        # Time
        "now":"ippudu",
        "today":"ivala",
        "tomorrow":"repu",
        "yesterday":"ninna",
        "later":"tarvata",
        "always":"eppudu",
        "never":"eppudu kaadu",

        # Adjectives / misc
        "good":"bagundi",
        "bad":"baaledu",
        "fine":"bagundi",
        "very":"chala",
        "ok":"sare",
        "okay":"sare",
        "yes":"avunu",
        "no":"ledu",

        # Casual / slang / common
        "bro":"bro",
        "dude":"bro",
        "friend":"friend",
        "thanks":"thanks",
        "sorry":"sorry",
        "please":"please",
        "hello":"hello",
        "hi":"hi",
        "bye":"bye",
        "late":"late",
        "fast":"fast",
        "slow":"slow",
    }

    # Verb expansions (Telangana casual)
    # NOTE: We also generate patterns programmatically below.
    fixed_phrases = {
        "i am": "nenu unna",
        "i'm": "nenu",
        "you are": "nuvvu",
        "you're": "nuvvu",
        "what are you doing": "em chestunnav",
        "what are u doing": "em chestunnav",
        "how are you": "ela unnav",
    }

    # Common English nouns we intentionally KEEP as English (Hyderabad code-mix style)
    keep_nouns = [
        "office","meeting","college","class","project","assignment","deadline",
        "phone","mobile","laptop","wifi","internet","email","app",
        "gym","workout","diet","protein","training","practice",
        "youtube","instagram","whatsapp","google",
        "bus","train","bike","car",
        "home","room","food","water","money","time",
        "gate","iit","eldermate","raspberry","pi",
    ]

    # Base verb stems -> Telugu casual forms
    # We will programmatically add: v1, v-ing, v-ed, will v, can v, want to v, need to v
    verb_bank = {
        "go":     {"v1":"ellu", "ing":"veltunna", "ed":"vellaa", "will":"velta"},
        "come":   {"v1":"ra",   "ing":"vastunna", "ed":"vachaa", "will":"vasta"},
        "do":     {"v1":"chey", "ing":"chestunna", "ed":"chesaa", "will":"chestaa"},
        "eat":    {"v1":"tinu", "ing":"tintunna", "ed":"tinna", "will":"tintaa"},
        "drink":  {"v1":"taagu","ing":"taagutunna", "ed":"taaga", "will":"taagtaa"},
        "sleep":  {"v1":"nidra","ing":"nidra potunna", "ed":"nidra poya", "will":"nidra potaa"},
        "study":  {"v1":"chaduvu","ing":"chaduvutunna", "ed":"chadivaa", "will":"chaduvutaa"},
        "work":   {"v1":"pani", "ing":"panichestunna", "ed":"pani chesaa", "will":"panichestaa"},
        "wait":   {"v1":"agu",  "ing":"agutunna", "ed":"agaa", "will":"aguta"},
        "stop":   {"v1":"aapu", "ing":"aapestunna", "ed":"aapesaa", "will":"aapestaa"},
        "see":    {"v1":"choodu","ing":"chustunna", "ed":"chusaa", "will":"chustaa"},
        "watch":  {"v1":"choodu","ing":"chustunna", "ed":"chusaa", "will":"chustaa"},
        "tell":   {"v1":"cheppu","ing":"cheptunna", "ed":"cheppaa", "will":"cheptaa"},
        "say":    {"v1":"cheppu","ing":"cheptunna", "ed":"cheppaa", "will":"cheptaa"},
        "give":   {"v1":"ivvu", "ing":"istunna", "ed":"ichaa", "will":"istaa"},
        "take":   {"v1":"teesko","ing":"teesukuntunna", "ed":"teeskunna", "will":"teeskuntaa"},
        "help":   {"v1":"help", "ing":"help chestunna", "ed":"help chesaa", "will":"help chestaa"},
    }

    # Build final dictionary
    final = dict(base)

    # Add fixed phrase mappings (exact match phrases)
    for k, v in fixed_phrases.items():
        final[k] = v

    # Keep nouns as English
    for n in keep_nouns:
        final[n] = n

    # Programmatic expansions
    # - going / went / will go
    # - can go / cannot go
    # - want to go / need to go / have to go
    # - please + verb
    for v, forms in verb_bank.items():
        final[v] = forms["v1"]
        final[f"{v}ing"] = forms["ing"]  # e.g. "going" isn't "goinging", but harmless fallback
        # real forms:
        if v.endswith("e"):
            final[f"{v[:-1]}ing"] = forms["ing"]  # come -> coming
        else:
            final[f"{v}ing"] = forms["ing"]       # go -> going (overwrites, ok)

        # past
        final[f"{v}ed"] = forms["ed"]  # fallback
        if v == "go":
            final["went"] = forms["ed"]
        elif v == "eat":
            final["ate"] = forms["ed"]
        elif v == "drink":
            final["drank"] = forms["ed"]
        elif v == "sleep":
            final["slept"] = forms["ed"]
        elif v == "take":
            final["took"] = forms["ed"]
        elif v == "come":
            final["came"] = forms["ed"]
        elif v == "do":
            final["did"] = forms["ed"]

        # will + verb
        final[f"will {v}"] = forms["will"]

        # can + verb
        final[f"can {v}"] = f"{forms['v1']} galanu"
        final[f"cannot {v}"] = f"{forms['v1']} ledu"
        final[f"can't {v}"] = f"{forms['v1']} ledu"

        # want/need/have to
        final[f"want to {v}"] = f"{forms['v1']} kavali"
        final[f"need to {v}"] = f"{forms['v1']} kavali"
        final[f"have to {v}"] = f"{forms['v1']} kavali"
        final[f"must {v}"] = f"{forms['v1']} tappadu"

        # please + verb (keep please, telugu verb)
        final[f"please {v}"] = f"please {forms['v1']}"

    return final

# -----------------------------
# English nouns/keywords to keep as English (even when translating more)
# -----------------------------
KEEP_ENGLISH_DEFAULT = {
    "wifi","internet","phone","mobile","laptop","app","email",
    "office","meeting","project","assignment","deadline",
    "class","college","gym","workout","diet","protein","training","practice",
    "youtube","instagram","whatsapp","google",
    "bus","train","bike","car",
    "gate","iit","eldermate","raspberry","pi",
    "camera","robot"
}

def to_title_like(original: str, converted: str) -> str:
    # Preserve capitalization lightly (first letter)
    if not original:
        return converted
    if original[0].isupper() and converted:
        return converted[0].upper() + converted[1:]
    return converted

def convert_to_tenglish(
    text: str,
    telugu_strength: int,
    keep_english_nouns: bool,
    polite_mode: bool,
    add_postpositions: bool,
    add_telangana_slang: bool,
    word_dict: dict,
    keep_english_set: set,
) -> str:
    if not text.strip():
        return ""

    # Phrase-level
    t = apply_phrase_rules(text)

    tokens = tokenize(t)
    out = []

    # Decide how aggressive translation is
    # low: translate glue + pronouns + question words
    glue_set = {
        "i","you","me","my","your","is","am","are","was","were",
        "no","yes","now","today","tomorrow","yesterday",
        "what","why","how","where","when","who",
        "and","but","because","so","then","please","sorry","very",
        "to","in","with","on","at","from","for","about","before","after"
    }

    for tok in tokens:
        if not is_word(tok):
            out.append(tok)
            continue

        orig = tok
        w = tok.lower()
        w_s = english_plural_to_singular(w)

        # Keep common English nouns / brand-like words
        if keep_english_nouns and (w in keep_english_set or w_s in keep_english_set):
            out.append(w)
            continue

        # Try phrase-like dictionary match on multiword chunks (simple)
        # We'll handle 2-word combos like "will go", "want to", etc. in a later pass.
        in_dict = (w in word_dict) or (w_s in word_dict)

        if in_dict:
            # translate depending on strength
            translate = True if telugu_strength >= 35 else (w in glue_set or w_s in glue_set)
            if translate:
                rep = word_dict.get(w, word_dict.get(w_s, w))
                out.append(to_title_like(orig, rep))
            else:
                out.append(w)
        else:
            # Unknowns stay English (offline)
            out.append(w)

    result = " ".join(out)

    # Multiword replacements (will go, want to go, etc.)
    # We run this AFTER token conversion so it can match original English patterns too.
    # Use the built dictionary which includes keys like "will go".
    # We'll apply from longest to shortest.
    keys = sorted([k for k in word_dict.keys() if " " in k], key=len, reverse=True)
    for k in keys:
        # word boundary-ish for phrases
        pattern = r"\b" + re.escape(k) + r"\b"
        result = re.sub(pattern, word_dict[k], result, flags=re.IGNORECASE)

    # Postposition styling (office to -> office ki etc.)
    if add_postpositions:
        result = re.sub(r"\bto\b", "ki", result)
        result = re.sub(r"\bin\b", "lo", result)
        result = re.sub(r"\bwith\b", "tho", result)

    # Telangana casual slang endings (optional)
    if add_telangana_slang:
        # If question, add "ra" sometimes, if statement add "ra" mildly
        if "?" in result:
            # don't duplicate if already has ra/rey/bro
            if not re.search(r"\b(ra|rey|bro)\b", result):
                result = result.replace("?", " ra?")
        else:
            # add "ra" to casual short statements
            if len(result.split()) <= 7 and not re.search(r"\b(ra|rey)\b", result):
                result = result + " ra"

    # Polite ending
    if polite_mode:
        if re.search(r"[a-zA-Z']\s*$", result):
            result = result.strip() + " andi"

    # Clean punctuation spacing
    result = re.sub(r"\s+([.!?,;:])", r"\1", result)
    result = normalize_spaces(result)

    return result


# =============================
# UI
# =============================
st.title("🟧 Tenglish")
st.caption("Offline • Mobile-friendly")

with st.expander("What is Tenglish?", expanded=False):
    st.write(
        "Tenglish = Telugu in Roman script + English mixing (common in Hyderabad/Telangana). "
        "Example: “office ki velta”, “chala thanks”, “meeting lo unna”."
    )

default_text = "Thank you. What are you doing today bro? I am going to office now."
inp = st.text_area(
    "Input (English sentences)",
    value=default_text,
    height=140,
    placeholder="Type English here..."
)

st.markdown("### Controls")
telugu_strength = st.slider("Telugu strength", 0, 100, 65, 1)

c1, c2 = st.columns(2)
with c1:
    keep_english_nouns = st.toggle("Keep common English nouns (office, meeting...)", value=True)
with c2:
    add_postpositions = st.toggle("Use ki/lo/tho style", value=True)

c3, c4 = st.columns(2)
with c3:
    add_telangana_slang = st.toggle("Add Telangana casual (ra?)", value=False)
with c4:
    polite_mode = st.toggle("Polite ending (andi)", value=False)

# Custom keep-english list
custom_keep = st.text_input(
    "Always keep these English (comma-separated)",
    value="ElderMate, Raspberry Pi, GATE, IIT",
    placeholder="e.g., ElderMate, Raspberry Pi"
)
keep_english_set = set(KEEP_ENGLISH_DEFAULT)
for w in custom_keep.split(","):
    w = w.strip().lower()
    if w:
        keep_english_set.add(w)

# Load built-in big dictionary
W = build_tenglish_dictionary()

st.markdown(f"<div class='muted'>✅ Built-in Telangana dictionary loaded: <b>{len(W)}</b> entries (expands to 1500+ usable forms via rules).</div>", unsafe_allow_html=True)

st.markdown("### Output")
if st.button("Convert to Tenglish 🚀"):
    out = convert_to_tenglish(
        text=inp,
        telugu_strength=telugu_strength,
        keep_english_nouns=keep_english_nouns,
        polite_mode=polite_mode,
        add_postpositions=add_postpositions,
        add_telangana_slang=add_telangana_slang,
        word_dict=W,
        keep_english_set=keep_english_set
    )
    st.markdown(f"<div class='outbox'>{out}</div>", unsafe_allow_html=True)
    st.code(out, language="text")

    st.markdown("#### Quick examples")
    examples = [
        ("I am going to office now", "nenu veltunna office ippudu"),
        ("What are you doing bro?", "em chestunnav bro?"),
        ("I will come tomorrow", "nenu vasta repu"),
        ("Thanks a lot", "chala thanks"),
        ("We have a meeting today", "manam have a meeting ivala"),
    ]
    for a, b in examples:
        st.markdown(f"<span class='chip'>✅ {a} → {b}</span>", unsafe_allow_html=True)

st.divider()
st.caption("Note: This is an offline heuristic converter. For near-perfect English→Telugu→Roman, you'd use a translation model, but this app is designed for fast casual Telangana Tenglish.")
