"""
outreach_generator.py — Generate personalized cold call / email / SMS scripts
per prospect, tailored by asset holder type. Pure templates, fully offline.
"""
import re


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


def fee_for(amount: float) -> int:
    return 12 if amount > 200000 else 15 if amount > 100000 else 20


OPENERS = {
    "insurance": "I located an outstanding file from {holder} — it appears to be a life insurance or benefit payout — that belongs to you, which has been transferred to the Wisconsin state treasury.",
    "investment": "I found an outstanding account record from {holder} with your name on it — approximately ${amt} — which has been absorbed into the Wisconsin unclaimed property treasury.",
    "bank": "I've located a dormant bank account record associated with {holder} — roughly ${amt} — sitting unclaimed in the Wisconsin state treasury.",
    "utility": "I found an unclaimed utility refund or stock distribution from {holder} — approximately ${amt} — that's been transferred to Wisconsin's unclaimed property division.",
    "general": "I found an outstanding financial asset from {holder} — approximately ${amt} — that belongs to you and has been transferred to the Wisconsin state treasury for safekeeping.",
}


def generate_scripts(prospect: dict) -> dict:
    """Returns {cold_call_script, cold_email, sms_opener} for one prospect."""
    name = prospect.get("name", "")
    fn = name.split(" ")[0] if name else "there"
    holder = prospect.get("holder", "the original institution")
    amount = float(prospect.get("amount", 0))
    amt = f"{amount:,.0f}"
    fee = fee_for(amount)
    fee_amt = f"{amount * fee / 100:,.0f}"
    opener = OPENERS[holder_type(holder)].format(holder=holder, amt=amt)

    cold_call_script = f"""THE Z-WAY CALL — {name.upper()}

"Hi, is this {fn}?... Hi {fn}, this is [Your Name] from ZGroup."

{opener}

"Have you received any notices from the state about this?"

[PAUSE — listen]

"I want to be upfront with you. The state is holding this money and you have
every right to claim it yourself at no cost on the Wisconsin state website.
Some people do exactly that.

The state process involves affidavits, notarization, and 3-6 months of
follow-up. We handle all of that. Our fee is {fee}% — that's ${fee_amt} —
and we only get paid when the check is in your hands. Zero upfront cost, ever.

Does that sound like something you'd want us to handle?"

[YES]: "Great. Let me confirm a couple quick details and I'll send our
one-page agreement tonight. What's the best email for you?"

[NO]: "Completely understood. If the process gets complicated, don't
hesitate to call me back. Have a great day." """

    cold_email = f"""Subject: {name} — Outstanding Asset with Wisconsin Treasury (${amt})

Hi {fn},

I'm reaching out about an unclaimed financial asset associated with your
name — approximately ${amt} from {holder} — currently held by the Wisconsin
Department of Revenue Unclaimed Property Division.

You have the full legal right to claim this yourself at no cost through the
state website. I want to be transparent about that.

The process involves affidavits, notarizations, and several months of
follow-up. ZGroup specializes in handling exactly this on behalf of claimants.

Our model: {fee}% contingency fee, zero upfront cost. You only pay if we recover.

I can send you the official state record confirming your asset so you can
verify before committing to anything.

Reply or call [Phone] if you'd like to see it.

Best,
[Your Name]
ZGroup LLC — Wisconsin Asset Locator"""

    sms_opener = (f"Hi {fn}, this is [Name] from ZGroup. I found a ${amt} asset from "
                  f"{holder} in the WI state treasury under your name. Can send the "
                  f"official record to verify — no cost to look. Reply YES.")

    return {
        "cold_call_script": cold_call_script,
        "cold_email": cold_email,
        "sms_opener": sms_opener,
        "fee_pct": fee,
        "holder_type": holder_type(holder),
    }


if __name__ == "__main__":
    demo = {"name": "John Hoover", "holder": "COINBASE INC", "amount": 283265.10}
    s = generate_scripts(demo)
    print(s["cold_call_script"])
    print("\n" + "=" * 60 + "\n")
    print(s["cold_email"])
    print("\n" + "=" * 60 + "\n")
    print(s["sms_opener"])
