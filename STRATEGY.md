# HeirBud — Strategy

A compliance-first unclaimed-property recovery operation, built so the honesty
*is* the growth engine, and engineered to throw off predictable cash that funds
the rest of the portfolio (EDNA, GMAPz, Odin).

This is the thinking behind the code. The code enforces it; this explains why.

---

## 1. The thesis in one line

**In a market full of sharks, the trustworthy operator wins the long game — and
trust is cheaper to run than deception.** Every scammy tactic (false urgency,
hidden fees, impersonating the state) raises suspicion, kills conversion, and
courts regulatory risk. Radical transparency does the opposite: it converts
*because* it disarms, and it's legal by construction.

We are not selling access to a secret list. The list is public. We sell
**certainty, convenience, and competence** on a process people find intimidating.

---

## 2. Why this business, for this purpose

The goal isn't to build a life around heir-finding. It's to build a **cash
engine** that is:

- **Low fixed cost** — software + your time, no inventory, no payroll to start.
- **Contingency-based** — you're paid only on success, so downside is capped.
- **Automatable** — the clerical 90% runs itself (see `AUTONOMOUS_SYSTEM.md`).
- **Non-seasonal** — unclaimed property is reported continuously, every state.
- **Fundable-outward** — steady fees become the runway for EDNA, GMAPz, Odin.

The strategic frame: **HeirBud is the patron. The creative projects are the art.**
Every closed claim buys time for the work you actually care about.

---

## 3. The moat (it is not the data)

Anyone can download the state file. Defensibility comes from the things that
compound:

1. **Verified data lineage** — you know each record is real, current, and
   eligible. Competitors guess; you prove.
2. **Compliant timing** — the 24-month gate means you contract only when it's
   enforceable. A rival who signs early has a *void* agreement and no fee.
3. **Claimant experience** — the owner portal, the proof-first letter, the calm
   tone. People refer the person who didn't feel like a scam.
4. **Complex-case capability** — estates, trusts, dissolved businesses. Hard,
   documentation-heavy, and where the real margin lives (see §6).
5. **Operational evidence** — a full audit trail turns "trust me" into "here's
   the record," which protects you and closes deals.

Trust is a moat because it's *expensive for a shark to copy* — they'd have to
stop being a shark.

---

## 4. Positioning & voice — strategic, never sharky

The brand is the **honest professional**. Concretely, in every touch:

- Lead with **their** money and the **free** state path — every time, unmissably.
- State plainly: *we are a private locator, not the government.*
- Frame the fee as **optional convenience**, capped, in writing, only-if-paid.
- Never manufacture urgency, never imply authority, never request SSN/bank
  details to "look up" a record.

This isn't only ethics — it's conversion science. The Email Template Library's
best-performing line is *"That's the honest version: you don't need me."* It
works because it removes the one thing stopping a reply: fear of a scam.

**Engagement strategy:** the proof-first sequence. USPS letter → owner portal
where they verify their *own* record → optional help. Each step earns the next.
The owner portal (`owner_portal.html`) is the centerpiece: it lets someone
confirm the property is real *without talking to us*, which paradoxically makes
them more likely to choose us.

---

## 5. The funnel, and where the money actually is

The pipeline is `IDENTIFIED → VERIFIED/ELIGIBLE → CONTACTED → RESPONDED →
AGREEMENT → SIGNED → FILED → PAID`. The analytics panel narrates where prospects
fall out. Strategic priorities by stage:

- **Biggest early leak is usually IDENTIFIED → ELIGIBLE** — records sitting
  unverified. The custody-verification worklist attacks exactly this.
- **CONTACTED → RESPONDED** is won by copy and channel, not volume. Proof-first
  beats aggressive every time; measure it.
- **RESPONDED → SIGNED** is won by making the agreement effortless and the free
  option honest. Friction and doubt are the enemies, not competition.

**Prioritize by expected, collectible fee — not raw dollars.** `scoring.py`
blends value, eligibility, contactability, and complexity, then routes each lead
to a track (Fast Track / Premium / Verify First / Self-Serve Nudge). A $300k
estate that needs probate is not automatically better than three clean $15k
owner claims you can bank this month.

**Then prioritize by money per *conversation*, not money per row.** `household.py`.
See §5b — this is the part competitors don't do.

---

## 5b. The household graph — our actual moat

Every locator in Wisconsin works from the same public list. The list is not an
edge; anyone can download it. The edge is **how much money one conversation is
worth**, and the state file quietly hands that to anyone who bothers to group it:

1. **The same person is listed several times.** Different holders, different
   report years, sometimes a nickname or a bare initial. Five rows are one human
   with five claims. Ungrouped, that's five letters to a stranger who is getting
   increasingly annoyed. Grouped, it's one letter listing everything they're
   owed — which converts better *and* costs a fifth as much to send.
2. **Families share an address, and one of them is often deceased.** A
   "Proceeds Due to Beneficiaries" record under an estate, with two living
   same-surname people at the same street address, means **the heir you're
   supposed to find is already sitting in your own data** — sometimes with a
   phone number you tracked down last week for a different claim.

Both are pure computation over records already in hand. No new data source, no
subscription, no scraping. And both cut the same way for the person on the other
end: fewer interruptions, one honest conversation that covers everything, and
estates that most locators skip because they "look hard" actually getting worked.

What it changes in the product:
- **Leads** show a `×3 · $94,300` badge and rank higher (`scoring.prioritize`
  applies a capped leverage multiplier — one call closing three claims is worth
  more of a solo operator's day than one call closing one).
- **Households tab** lists multi-claim people, heir bridges, and family clusters
  ranked by money per conversation.
- **Combined letter** replaces N letters with one.
- **Heir approach script** turns a bridge into an actual phone call, with the
  free-claim disclosure and the "never ask for an SSN" rules on the page.
- **Operator brief** leads with these, because they're the cheapest dollars on
  the list.

**The privacy line, enforced in code:** a combined document is only ever
assembled from *one person's own* claims. Relatives surface to the **operator**
as a research lead — we never disclose one person's money to another person.
Business claimants (banks, counties, hospitals, the State itself) are excluded
from household grouping entirely; they're real records but a different job.

---

## 6. Segmentation — the premium tier is the real prize

| Segment | Volume | Effort | Margin | Play |
|---|---|---|---|---|
| **Simple owner** | High | Low | Thin per-case | Fast-track, semi-automated, batch |
| **Small (<$500)** | High | — | Tiny | Self-serve nudge — point them to the state, build goodwill/referrals |
| **Estate** | Low | High | **Fat** | Premium specialist handling; charge for genuine complexity |
| **Trust** | Low | High | **Fat** | Premium; requires trustee authority docs |
| **Business (dissolved)** | Low | High | **Fat** | Premium; corporate authority + EIN work |

The simple-owner lane pays the bills and builds reputation. The **complex lane
is where a solo operator earns real money**, because self-filing is genuinely
hard there and legitimate value is high. Fund the premium lane's legal
capability first (see §8).

---

## 7. Unit economics (illustrative — replace with pilot data)

At the 10% cap, with automation driving cost-per-touch toward zero:

| Lane | Contacts/mo | Resp. | Claims | Avg recovery | Fee | **Monthly** |
|---|--:|--:|--:|--:|--:|--:|
| Simple, conservative | 200 | 2% | 2 | $2,500 | $250 | ~$500 |
| Simple, realistic | 800 | 2.5% | 10 | $3,000 | $300 | ~$3,000 |
| + Premium (2 estates) | — | — | 2 | $80,000 | $8,000 | +~$16,000 |

The lever is **eligible, verified, well-targeted contacts per human hour** —
exactly what scoring + automation maximize — plus a **small number of premium
cases** that dwarf the volume lane. One estate can equal a quarter of simple-lane
revenue. Model both; the analytics panel already separates published / eligible
/ expected / realized so you never mistake a list for a bank balance.

---

## 8. Expansion — schema-driven, one state at a time

Do **not** copy-paste into new states. Each state is a **rule pack**: fee cap,
waiting period, registration/licensing, required disclosures, contract content,
filing method, communication limits, complaint authority. `compliance.py` is
built to hold Wisconsin today and become `compliance/<state>.py` tomorrow. A
state launches only when its rule pack passes review. California, for instance,
requires registration *before* soliciting — a different pack, not a find-replace.

Sequence: **prove Wisconsin → template the rule pack → add one high-value
neighboring state → only then scale breadth.**

---

## 9. Risk register (business, not just legal)

- **Regulatory** — mitigated by the compliance engine + a lawyer's sign-off
  (see `docs/LEGAL_REVIEW_BRIEF.md`). Non-negotiable before live paid work.
- **Reputation** — one scam complaint poisons the well. The proof-first posture
  and suppression discipline are the defense.
- **Unauthorized practice of law** — preparing/filing claims for others can
  cross a line, especially in estates. Scope the service with counsel; know
  where "assistance" ends and "legal representation" begins.
- **Data/PII** — real owner data never in git, encrypted at rest before real
  claimants, audit trail on every action. (Open items in Master Control.)
- **Concentration** — don't let one premium case's timeline become your only
  income. Keep the simple lane flowing.

---

## 10. The 90-day path to first cash

1. **Weeks 1–2** — Legal review of templates + service scope (the brief is
   written; book the meeting). Confirm the Wisconsin rule pack against current
   guidance.
2. **Weeks 2–3** — Verified 25-record pilot. USPS-first, owner portal live,
   every touch logged, nothing auto-sent. Measure deliverability, response,
   trust.
3. **Weeks 4–6** — Convert the first simple claims. Bank the first fees. Feed
   real numbers into the analytics panel; recalibrate scoring priors.
4. **Weeks 6–12** — Take on the first premium (estate/business) case with
   counsel's guardrails. This is the first *large* fee.
5. **Ongoing** — Route a fixed share of every fee to the portfolio fund. HeirBud
   exists to buy runway for EDNA, GMAPz, and Odin. Keep that the point.

---

## 11. What would make this *not* work — read this honestly

- Skipping the lawyer and getting a UPL or fee complaint. (Cheap to avoid.)
- Chasing automation vanity instead of trustworthy throughput.
- Treating published value as revenue and over-investing ahead of realized fees.
- Going wide across states before Wisconsin is demonstrably repeatable.
- Letting the premium lane's slow timelines starve cash flow.

The system is built to make the right path the easy one. The discipline is
yours: verify before you contact, disclose before you pitch, and let the honesty
do the selling.
