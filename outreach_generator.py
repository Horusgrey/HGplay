"""
outreach_generator.py — Generate personalized call / email / SMS scripts per
prospect, tailored by asset holder type. Pure templates, fully offline.

Rewritten per the PRJ-HB7K4 audit and the project Email Template Library:
the honesty IS the conversion strategy. Every script leads with the owner's
money, states plainly they can claim it FREE from the state, frames the fee
(capped at the state maximum) as optional convenience, and never impersonates
the state or manufactures urgency. Suppressed records return no scripts.
"""
import re

import compliance


def holder_type(holder: str) -> str:
    h = (holder or "").upper()
    if re.search(r"INSURANCE|LIFE|BRIGHTHOUSE|NATIONWIDE|METLIFE|PRUDENTIAL", h):
        return "insurance"
    if re.search(r"COINBASE|CRYPTO|AMERITRADE|ROBINHOOD|SCHWAB|FIDELITY|VANGUARD|E\*?TRADE", h):
        return "investment"
    if re.search(r"BANK|CREDIT UNION|SAVINGS", h):
        return "bank"
    if re.search(r"ENERGY|UTILIT|GAS|ELECTRIC|POWER", h):
        return "utility"
    return "general"


# Neutral, factual openers. No false authority, no "absorbed/seized" language.
OPENERS = {
    "insurance": "your name is attached to an unclaimed benefit or policy payout from {holder}, now held by the Wisconsin Department of Revenue.",
    "investment": "your name is attached to an unclaimed account from {holder} — about ${amt} — now held by the Wisconsin Department of Revenue.",
    "bank": "there's an unclaimed account balance associated with {holder} — about ${amt} — now held by the Wisconsin Department of Revenue.",
    "utility": "there's an unclaimed refund or distribution from {holder} — about ${amt} — now held by the Wisconsin Department of Revenue.",
    "general": "your name is attached to unclaimed property from {holder} — about ${amt} — now held by the Wisconsin Department of Revenue.",
}


class SuppressedProspectError(Exception):
    """Raised when outreach is requested for an opted-out record."""


def generate_scripts(prospect: dict) -> dict:
    """Returns {cold_call_script, cold_email, sms_opener, fee_pct, holder_type}."""
    if prospect.get("suppression_status") == "SUPPRESSED":
        raise SuppressedProspectError(
            f"{prospect.get('name', 'record')} is suppressed — no outreach permitted.")

    name = prospect.get("name", "")
    fn = name.split(" ")[0] if name else "there"
    holder = prospect.get("holder", "the original institution")
    amount = float(prospect.get("amount", 0))
    amt = f"{amount:,.0f}"
    fee = compliance.compliant_fee_pct()           # 10%, capped by rule
    fee_amt = f"{compliance.fee_amount(amount, fee):,.0f}"
    opener = OPENERS[holder_type(holder)].format(holder=holder, amt=amt)

    cold_call_script = f"""HEIRBUD CALL — {name.upper()}

"Hi, is this {fn}? ... Hi {fn}, this is [Your Name] with ZGroup, a Wisconsin
locator service. I'm not with the state — I want to be clear about that up front.

I research public unclaimed-property records, and {opener}"

"A few things you should know: this is your money, the state is holding it for
you, and you can claim it yourself for free at {compliance.STATE_PORTAL} — you
don't need me or anyone else to get it."

[PAUSE — listen]

"If you'd rather not deal with the paperwork and back-and-forth, that's what I
do. I work on contingency: my fee is {fee:.0f}% — about ${fee_amt} — and only if
you actually receive your money. We'd agree on it in writing first, and there's
never any upfront cost. If you'd rather do it yourself, I'm glad to point you to
the free state page and we're done."

[YES]: "Great. I'll send a plain one-page agreement so you can read it — no
obligation. What's the best email for you?"

[NO / NOT INTERESTED]: "No problem at all. Please do claim it directly so it
doesn't sit unclaimed — it's yours. Take care." """

    cold_email = f"""Subject: {fn}, unclaimed property in your name — Wisconsin DOR

Hi {fn},

I research unclaimed-property records, and {opener}

A few things up front:
  • This is YOUR money — the state is holding it for you.
  • You can claim it yourself, free, at {compliance.STATE_PORTAL}
    (or call {compliance.STATE_PHONE}). You do not need me.

That's the honest version. If you'd rather skip the paperwork and follow-up,
I help people recover these funds on contingency — a {fee:.0f}% fee (the maximum
Wisconsin allows), agreed in writing beforehand, and owed ONLY if you actually
get paid. No upfront cost, no risk to you.

If you'd rather do it yourself, I'm genuinely glad to point you there at no charge.

Want me to send the details so you can verify the record?

[Your Name]
[Your Phone] · [Your Email]
ZGroup LLC — Wisconsin locator service (not a government agency)"""

    sms_opener = (f"Hi {fn}, this is [Name] with ZGroup (a private WI locator, not the "
                  f"state). Your name is on ~${amt} of unclaimed property held by "
                  f"Wisconsin. You can claim it free at {compliance.STATE_PORTAL}. "
                  f"Happy to help for a {fee:.0f}% fee only if you get paid — reply YES for details.")

    return {
        "cold_call_script": cold_call_script,
        "cold_email": cold_email,
        "sms_opener": sms_opener,
        "fee_pct": fee,
        "holder_type": holder_type(holder),
    }


if __name__ == "__main__":
    demo = {"name": "Jordan Sample", "holder": "EXAMPLE HOLDINGS INC", "amount": 283265.10}
    s = generate_scripts(demo)
    print(s["cold_call_script"])
    print("\n" + "=" * 60 + "\n")
    print(s["cold_email"])
    print("\n" + "=" * 60 + "\n")
    print(s["sms_opener"])
