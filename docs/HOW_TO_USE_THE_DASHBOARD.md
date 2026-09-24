# How to use the Command Center

No installing, no terminal, no Python. Open `heirbud_command_center.html` in Chrome
(double-click it from Drive, or use the published link) and it runs.

Your list and your details are stored **in that browser, on that device**. Nothing
uploads anywhere. That also means: bookmark the same link on the same machine, and
use **⬇ Export** now and then so you have a backup.

---

## First five minutes

**1. ⚙ My details.** Your name, business name, phone, email. These sign every
letter and fill the return address. This is the only thing in the app you have to
type, and you type it once. Until it's filled in, letters refuse to print —
on purpose, so you never mail something that says `[Your Name]`.

**2. ⬆ Import your CSV.** Pick your Wisconsin file. You'll get a screen showing how
your columns were matched, with a real value from your own file next to each one
("Amount ← CASH_REPORTED, e.g. $84,979.53"). Fix anything wrong, hit Import.
It handles commas, tabs, pipes and semicolons, `$1,234.56`, `(1,234)`, quoted
fields, and `LAST, FIRST` name columns. Nothing is saved until you click Import.

**3. Read the summary.** How many records, how much is workable today, how many
people appear more than once, how many heir bridges. Then "Show me the plan".

**4. Start here → Today's plan.** This tells you what to do, in order, highest
value per envelope first. Follow it top to bottom.

**5. Print a batch.** Say how many letters you want. You get one document, one
letter per page, ranked. Print → fold → stamp → mail. That's the job.

---

## What the eligibility labels mean

| Label | What it means | What you can do |
|---|---|---|
| **verified ✓** | You looked it up on the state site and wrote down what you saw | Anything, including a 10% contract |
| **presumed** | The report date in your file is 24+ months old | Gratuity letter today. Confirm to unlock a contract |
| **too recent** | Reported under 24 months ago | Wait. An agreement now would be void — you'd work for nothing |
| **no date** | Your file had no usable date | One lookup on the state site fixes it |

**Why "presumed" isn't "verified":** holders hand the money over when they report
it, so the report date is strong evidence — but it's evidence about a spreadsheet,
not the state's record. Telling someone about their money is fine either way.
Signing a fee agreement is not: if the real custody date turns out to be under 24
months, the agreement is void and you collect nothing. That's the whole reason
the Confirm step exists, and why it takes thirty seconds.

---

## The two approaches

- **🤝 Gratuity** — no contract. You tell them, you help, and if they want to send
  a thank-you of their own choosing, they can. Always allowed.
- **📄 Contract** — 10% contingency, Wisconsin's legal maximum, in writing first,
  owed only if they get paid. Needs a **verified** custody date.

HeirBud picks one per lead (small claims → gratuity, estates/trusts/larger →
contract). Click the 🤝/📄 button on any row to flip it, or set a global default
under ⚙ My details.

---

## The Households tab — the part nobody else does

Everyone works the same public list. The edge is **money per conversation**.

- **Same person, more than one claim.** Different banks and years, sometimes a
  nickname or a bare initial — all one human. "Combined letter" covers every claim
  in one envelope. Better response, a fraction of the postage, and one conversation
  instead of five.
- **Heir bridges.** A deceased owner's claim, plus living same-surname people at
  the same address — the heirs are already in your own list. "Heir approach script"
  gives you the phone call, with the free-claim line and the ground rules on it.
- **Households.** Families ranked by total reachable value.

**Privacy line:** a combined letter only ever lists *one person's own* claims.
Relatives are shown to **you** as research. You never tell one person about
another person's money.

---

## Follow-ups — one nudge, then you stop

The app remembers when every letter went out. Three weeks later, anyone who
hasn't replied appears under **Follow-ups due** on the Start here tab. Print them
in one batch, same as the first time.

Three rules, enforced by the software rather than your memory:

- **Exactly one follow-up.** After the second letter that person never appears in
  the queue again.
- **A reply ends it.** The moment you move someone past CONTACTED, no chaser is
  ever generated for them.
- **The second letter says it's the last one.** In those words. It also says you
  won't pass their name on, and apologises for the intrusion if it was one.

That last point is the whole difference between a reminder and being pestered,
and it's the reason someone who ignored the first letter might trust the second.

### Notes

The **📝** button on any lead keeps a dated log — who answered, what they said,
when to try again. It shows the letter dates too, so the third call isn't
accidentally your first conversation. Notes are included in the CSV export.

---

## Daily rhythm

1. **Start here** — work the plan top to bottom.
2. **Verify** — look up a few on the state site, hit Confirm. Each one turns a
   gratuity lead into a contract lead.
3. **Leads** — anyone who replies, move their Stage. When they get their money,
   hit 💵, then print the invoice (or thank-you) from **Collections**.
4. **Export** weekly. It's your backup.

---

## Things that are true and worth repeating

- Your CSV is a **snapshot**. Some claims may already be paid out. Confirm on the
  state site before promising anyone anything — and if it's gone, the Confirm
  dialog has a "Not listed anymore" button that closes it out cleanly.
- **Finding phone numbers is not automatic.** 🔎 Find builds the exact searches for
  that person — nickname variants, the address search that shows who lives there
  now, obituary lookups for estates — and you paste back what you find.
  People-search sites block automated lookups; real auto-fill needs a paid data
  provider, and that isn't wired up.
- **Nothing sends itself.** No email, no SMS. Letters print; you mail them.
- **Stop means stop.** Suppression is permanent and nothing can undo it —
  not a re-import, not auto-advance.
- **Never** ask for a Social Security number, bank details, or money up front,
  and never imply you're from the State of Wisconsin. The scripts already say the
  free option out loud, first, every time. That honesty is the business model,
  not a disclaimer bolted onto it.
