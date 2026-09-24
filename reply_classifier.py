"""
reply_classifier.py — Sort inbound replies so only real leads reach a human.

Deliberately RULE-BASED, not an LLM call: the compliance-critical decisions
(detecting an opt-out, defaulting to human review when unsure) must be
deterministic, offline, and testable. An LLM can later refine the fuzzy middle,
but STOP detection and safe defaults must never depend on a model's mood.

Categories:
  STOP            — opt-out. SAFE to auto-act: suppress immediately.
  WRONG_PERSON    — not them. Auto-suppress (don't keep contacting).
  ALREADY_CLAIMED — already got it. Close out, no fee.
  INTERESTED      — wants help. Surface to human, advance to RESPONDED.
  QUESTION        — has questions (often "is this a scam?"). Surface to human.
  UNCLEAR         — ambiguous. NEVER auto-act — flag for a human to read.

Design rule: opting someone OUT is always safe to automate; opting them IN or
making any money-affecting move always needs a human.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Order matters: the first matching, highest-precedence rule wins. Opt-out and
# wrong-person are checked before interest so "stop, wrong person" suppresses.
STOP_PATTERNS = [
    r"\bunsubscribe\b", r"\bstop\b", r"\bremove me\b", r"\btake me off\b",
    r"\bdo not (contact|email|call|text)\b", r"\bdon'?t contact\b",
    r"\bleave me alone\b", r"\bopt(?:\s|-)?out\b", r"\bno thanks?\b.*\b(remove|stop)\b",
]
WRONG_PERSON_PATTERNS = [
    r"\bwrong (person|number|email)\b", r"\bnot me\b", r"\bthat'?s not me\b",
    r"\bdon'?t know (who|what) (you|this)\b", r"\bno one (by|named)\b",
    r"\byou have the wrong\b",
]
ALREADY_PATTERNS = [
    r"\balready (claimed|got|received|have) it\b", r"\balready claimed\b",
    r"\bgot (it|the money|paid) already\b", r"\bclaimed it (myself|already)\b",
]
SPAM_PATTERNS = [
    r"\bout of office\b", r"\bauto(?:matic)? reply\b", r"\bdelivery (status|failure)\b",
    r"\bmailer-daemon\b", r"\bundeliverable\b", r"\bvacation (response|reply)\b",
]
QUESTION_PATTERNS = [
    r"\bis this (a )?(scam|real|legit|legitimate)\b", r"\bhow (do|does|much|long)\b",
    r"\bwhat('?s| is)\b", r"\bwhy\b", r"\bwho are you\b", r"\bproof\b", r"\?\s*$",
]
INTERESTED_PATTERNS = [
    r"\byes\b", r"\binterested\b", r"\bsounds good\b", r"\bhelp me\b",
    r"\bgo ahead\b", r"\bsend (me )?(the )?(details|info|agreement|forms?)\b",
    r"\bhow do (i|we) (start|proceed|claim)\b", r"\blet'?s do (it|this)\b",
    r"\bplease (help|proceed|send)\b",
]

# What each category should do in the pipeline.
ACTION = {
    "STOP":            ("suppress", "Opt-out — suppress immediately (safe, automatic)"),
    "WRONG_PERSON":    ("suppress", "Wrong person — suppress so we stop contacting"),
    "ALREADY_CLAIMED": ("close",    "Already claimed — close out, no fee"),
    "INTERESTED":      ("advance",  "Interested — advance to RESPONDED, human sends agreement"),
    "QUESTION":        ("human",    "Question — human should answer (often a scam-check)"),
    "UNCLEAR":         ("human",    "Ambiguous — human must read; no automatic action"),
    "SPAM":            ("ignore",   "Auto-reply/bounce — ignore"),
}


@dataclass
class Classification:
    category: str
    action: str
    note: str
    matched: str

    def as_dict(self) -> dict:
        return {"category": self.category, "action": self.action,
                "note": self.note, "matched": self.matched}


def _first_match(text: str, patterns: list[str]) -> str | None:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def classify(text: str) -> Classification:
    """Classify one reply body. Precedence favors safe outcomes (opt-out first)."""
    t = (text or "").strip()
    if not t:
        return Classification("UNCLEAR", *ACTION["UNCLEAR"][:2] + ("",))  # empty -> human
    # Precedence: opt-out > wrong-person > already > spam/bounce > question > interested.
    for cat, patterns in (
        ("STOP", STOP_PATTERNS),
        ("WRONG_PERSON", WRONG_PERSON_PATTERNS),
        ("ALREADY_CLAIMED", ALREADY_PATTERNS),
        ("SPAM", SPAM_PATTERNS),
        ("QUESTION", QUESTION_PATTERNS),
        ("INTERESTED", INTERESTED_PATTERNS),
    ):
        hit = _first_match(t, patterns)
        if hit:
            action, note = ACTION[cat]
            return Classification(cat, action, note, hit)
    action, note = ACTION["UNCLEAR"]
    return Classification("UNCLEAR", action, note, "")


def process_reply(crm, property_id: str, text: str) -> dict:
    """Classify a reply and take only the SAFE automatic action.

    - STOP / WRONG_PERSON → auto-suppress (opting out is always safe).
    - ALREADY_CLAIMED → move to CLOSED.
    - INTERESTED → advance to RESPONDED (human still sends the agreement).
    - QUESTION / UNCLEAR → logged and surfaced; NO automatic state change.
    Returns the classification plus what was done.
    """
    p = crm.get_prospect(property_id)
    if not p:
        return {"error": "not found"}
    c = classify(text)
    # Neutral outcome: does NOT trigger the CRM's auto-advance, so we control the
    # stage transition explicitly below (a bounce must never advance a prospect).
    crm.log_contact_attempt(property_id, "Email", "Reply Received",
                            f"[{c.category}] {text[:160]}")
    done = "logged"
    if c.category in ("STOP", "WRONG_PERSON"):
        crm.suppress(property_id, f"Auto: {c.category} — {c.matched!r}")
        done = "suppressed"
    elif c.category == "ALREADY_CLAIMED":
        if p["stage"] != "SUPPRESSED":
            crm.update_stage(property_id, "CLOSED", "Auto: already claimed")
        done = "closed"
    elif c.category in ("INTERESTED", "QUESTION"):
        # Both are genuine replies → RESPONDED. A human still handles the next step
        # (send the agreement, or answer the question). We never auto-send.
        if p["stage"] not in ("SUPPRESSED", "CLOSED"):
            crm.update_stage(property_id, "RESPONDED", f"Auto: {c.category.lower()} reply")
        done = "advanced_to_responded"
    # SPAM / UNCLEAR: no state change on purpose (bounce, OOO, or ambiguous).
    return {"classification": c.as_dict(), "action_taken": done,
            "needs_human": c.category in ("INTERESTED", "QUESTION", "UNCLEAR")}


if __name__ == "__main__":
    samples = [
        "Please STOP emailing me.",
        "wrong person, I don't know what this is",
        "Yes! Please send me the details.",
        "Is this a scam? How do I know it's real?",
        "I already claimed it myself last month, thanks.",
        "Out of office until Monday.",
        "ok",
    ]
    for s in samples:
        c = classify(s)
        print(f"{c.category:16} {c.action:9} | {s}")
