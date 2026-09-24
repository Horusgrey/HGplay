# THE ODIN CANON
**Version 1.0 — The single source of truth. Everything else is archive.**

If a document, zip, repo, or AI conversation conflicts with this file, this file wins.
If this file changes, the version number changes, and the old version goes to `/archive`.

---

## 1. THE THESIS

**The unit of education should be the job, not the degree.**

Every existing system runs the pipeline forward: learn things → get a credential → hope it maps to employment. Odin runs it backward: start from a real job's skill requirements → reverse-engineer the curriculum → the learner proves each skill with real deliverables → the learner walks away with evidence, not claims.

The motto is the spec: **No Debt. Real Skills. Get Hired.**

---

## 2. THE PROBLEM (no embellishment)

- U.S. student debt exceeds $1.7 trillion. The average borrower carries ~$39K.
- Roughly half of college graduates start out underemployed; many remain so a decade later.
- Employers report persistent skill gaps while hiring costs run ~$4,700+ per hire.
- The disconnect is structural: education sells credentials; employers need demonstrated ability. Nobody owns the handoff.

Odin owns the handoff.

---

## 3. THE MECHANIC (the actual product)

One mechanic. Everything else is decoration around it:

**The bidirectional skill map.**

1. A job's requirements are expressed as a **skill matrix** (e.g., "Marketing Coordinator: SEO, analytics, copywriting, campaign planning").
2. Odin reverse-engineers the matrix into a **course path** — modules with open resources, each ending in a **deliverable** (real work) and a **quiz** (verification).
3. Completing a module writes to the learner's **proof ledger** — XP, the deliverable itself, the score, the date.
4. The proof ledger **generates the resume.** The learner never writes a resume; the resume is a byproduct of the work. Every line on it is backed by an artifact.

The resume that builds itself is the wedge feature. It is valuable to a single human on day one, even with zero employers on the platform — because the existing job market (Indeed, LinkedIn, a walk-in application) accepts resumes. Odin doesn't need network effects to help person #1.

**XP is a competency ledger, not engagement points.** XP means "verified ability," nothing else. No XP for streaks, logins, or participation.

---

## 4. THE LOOP

**Learn → Prove → Apply → Get Hired.**

And it closes: hires validate courses → employers fund the platform → educators are paid from outcomes, not tuition → students never pay. The people who extract the value (employers) bear the cost. That is the entire monetization philosophy; details live in §9 and stay out of v1.

---

## 5. PRINCIPLES (non-negotiable)

1. **Free for learners. Forever.** No tuition, no ISA, no paywalled core path.
2. **Proof over claims.** Deliverables and verified scores, never self-reported skills.
3. **No gatekeeping.** No prerequisites, no admissions, no credentials required to learn or to teach well.
4. **Open by default.** Open resources (MIT OCW, freeCodeCamp, YouTube EDU), open code, community-refined content.
5. **Educators earn from outcomes**, not from student debt.
6. **Truth-first voice.** The platform speaks plainly. No fluff, no AI cheerleading, no marketing speak. (This applies to UI copy, error messages, and everything Odin says to a user.)
7. **One canon.** One repo. Deploys come from the repo — never drag-and-drop. Every fork or experiment merges back or dies in `/archive`.

---

## 6. THE PITCH (60 seconds)

> College costs six figures and half its graduates end up in jobs that didn't require it. Employers can't find proven skills; learners can't prove skills without a job. Odin closes that loop. Pick a career path. The curriculum is reverse-engineered from real job requirements using free, open resources. Every module ends in real work — a deliverable — and a verification quiz. Your resume writes itself from what you've actually done; every line is backed by an artifact an employer can inspect. Free for learners, always — employers pay because they get pre-proven candidates. No debt. Real skills. Get hired.

---

## 7. v1 SCOPE — RUTHLESS

The bar for v1 is one sentence: **one real person completes one course and downloads a resume Odin wrote from their work.**

### IN
- **One course:** Marketing 101 (already seeded in the Mongo backend). 5 modules, each: open resource → deliverable → quiz → XP.
- **The proof ledger:** XP, completed modules, stored deliverables (text or link), quiz scores. localStorage first, backend sync where endpoints exist.
- **The resume generator:** the single AI feature in v1. Converts the proof ledger into clean, ATS-friendly resume language. Download as text/print-to-PDF.
- **A read-only job feed** on the course page ("real jobs using this skill") — static or API-pulled. Look, don't manage.
- **Four screens.** Specified in §8.

### OUT (v2+; documented, not deleted)
- Educator Studio / course creation UI
- Employer dashboard, candidate search, skill-matrix authoring
- Auth0 / accounts (v1 is single-learner, local-first)
- X Spaces integration, community notes
- Payments, subscriptions, placement fees
- ODINNEXUS gamification skin (badges, tiers, "skill resonance" visuals)
- AI quizzes / AI tutoring (quizzes are static JSON in v1)

Cutting these is not abandoning them. They are sequenced behind proof that one human got value.

---

## 8. WIREFRAMES — v1 (text spec)

Style: dark, gritty, clean. Blue (#1E489E) base, orange (#E16427) for CTAs. Inter or system font. Mobile-first. The voice in all copy follows Principle 6.

### Screen 1 — HOME
```
[ODIN]                                    [The Path] [Proof] [Resume]
------------------------------------------------------------------
        NO DEBT. REAL SKILLS. GET HIRED.
        The curriculum is the job. Prove it, line by line.

                 [ START THE PATH ]  ← single CTA

   Learn ────► Prove ────► Apply ────► Get Hired
   (one-line explanation under each step)
------------------------------------------------------------------
Footer: open-source · free forever · odin.it.com
```

### Screen 2 — THE PATH (course view)
```
Marketing 101 — Career Path            XP: 120 ▓▓▓▓░░░░ 5 modules
------------------------------------------------------------------
▸ Module 1: Intro to Marketing                          ✔ 30 XP
▸ Module 2: Market Research & Analytics                 ✔ 30 XP
▾ Module 3: SEO Fundamentals                            ● ACTIVE
    LEARN: [MIT OCW link] [supplementary link]
    PROVE: Deliverable — "Write a 300-word SEO audit of any
           real website." [text area / link field]  [Submit]
    VERIFY: Quiz (5 questions, static)                [Take Quiz]
▸ Module 4: Campaign Planning                           🔒
▸ Module 5: Capstone — Full Campaign                    🔒
------------------------------------------------------------------
SIDEBAR/BELOW: Real jobs using these skills (read-only feed)
```

### Screen 3 — PROOF LOCKER (profile)
```
Your Proof Ledger                                   Total XP: 120
------------------------------------------------------------------
Module 1 — completed 6/14/26 — quiz 5/5
  Deliverable: [view artifact]
Module 2 — completed 6/18/26 — quiz 4/5
  Deliverable: [view artifact]
------------------------------------------------------------------
Skills verified: marketing strategy · market research · analytics
                                       [ GENERATE RESUME → ]
```

### Screen 4 — RESUME
```
[Generated resume — clean ATS layout]
Name / contact (user-entered, stored locally)
SKILLS — pulled from verified modules only
PROJECTS — each deliverable rendered as a project entry with
           outcome language, generated by the resume engine
VERIFICATION — "Every entry verified at odin.it.com/proof/{id}" (v2)
------------------------------------------------------------------
[ Download / Print ]        [ Edit details ]
```

---

## 9. CODE SPEC — v1

### Architecture (locked decisions)
- **Frontend:** ONE file. `index.html`. No build step, no bundler, no framework runtime. Vanilla JS + CSS. (This is a standing architectural preference and it's correct for this project's maintenance reality.)
- **Backend:** the EXISTING `eduquest-xp-api` on Render. Healthy, already seeded. Do not rebuild. Extend only when v1 demands it.
- **State:** localStorage is the source of truth for the learner in v1; sync to backend endpoints opportunistically (`/api/xp`). Survives backend cold starts.
- **Deploys:** GitHub repo `odin-platform` → Netlify auto-deploy. Drag-and-drop deploys are banned (a drag-and-drop is how the live site got overwritten by Visual-Co).
- **Resume engine:** one Claude API call. Input: the proof ledger JSON. Output: resume sections in plain text/JSON. Prompt lives in the repo as `resume-prompt.md` so it's versioned.

### Repo layout
```
odin-platform/
  index.html          ← the entire frontend
  resume-prompt.md    ← versioned prompt for the resume engine
  data/
    marketing-101.json  ← course content (modules, quizzes) — also
                          mirrors what's seeded in Mongo
  CANON.md            ← this document
  archive/            ← pointers to all prior versions (see §11)
```

### Data model
```json
// Course (data/marketing-101.json and Mongo)
{
  "slug": "marketing-101",
  "title": "Marketing 101",
  "skills": ["marketing strategy", "market research", "SEO",
             "campaign planning"],
  "modules": [{
    "id": "m1",
    "title": "Introduction to Marketing",
    "resources": [{"name": "MIT OCW: Marketing Management",
                    "url": "..."}],
    "deliverable": "Prompt text describing the real work",
    "quiz": [{"q": "...", "options": ["..."], "answer": 0}],
    "xp": 30
  }]
}

// Learner (localStorage key: odin.learner)
{
  "name": "", "contact": "",
  "xp": 0,
  "ledger": [{
    "moduleId": "m1",
    "deliverable": "text or url",
    "quizScore": 5, "quizMax": 5,
    "completedAt": "ISO date"
  }]
}
```

### Backend endpoints (existing → v1 usage)
| Endpoint | Status | v1 use |
|---|---|---|
| GET /api/health | live | status indicator |
| GET /api/courses | live | course content (fallback: local JSON) |
| GET/POST /api/xp | live | opportunistic sync |
| POST /api/resume | live (parser) | unused in v1 |
| GET /api/jobs | live | read-only job feed |

### Definition of done (v1)
1. odin.it.com loads the four screens on mobile.
2. A learner can complete all 5 modules: open resources, submit deliverables, pass quizzes, accrue XP.
3. "Generate Resume" produces a clean, downloadable resume from the ledger.
4. Everything survives a page refresh and a backend cold start.
5. Zero console errors. Zero lorem ipsum. Copy obeys Principle 6.

---

## 10. MILESTONES (human, not technical)

- **M1 — Canon live.** This file + repo + odin.it.com serving v1. (Tech milestone — the only one.)
- **M2 — Person #1.** One real human (not Zack) completes Marketing 101 and downloads their resume. Get their honest reaction in writing.
- **M3 — Person #1 uses it.** They send that resume to a real job application. What happened?
- **M4 — Five completions.** Five proof ledgers exist. NOW revisit §7's OUT list — employer features earn their way in only when there's a talent pool to show.

No new features between milestones. New ideas get one line in `IDEAS.md` and nothing else.

---

## 11. ARCHIVE MAP (what happens to the 14 versions)

Nothing is deleted. Everything is demoted.

| Asset | Disposition |
|---|---|
| "Odin Master File w gemini" (Drive) | source material — mined, archived |
| Grok update 0606, Grok beta specs | archived reference |
| Vision docs, manifestos, pitch scripts | superseded by this canon; archived |
| Wireframe specs (3 versions) | superseded by §8; archived |
| ODINNEXUS | v2+ design reference (gamification skin) |
| 3 Replit apps (zhorton888) | frozen; do not edit further |
| 8 Netlify sites | keep `edudrop` (backup) + the ONE canon site bound to odin.it.com; Visual-Co moves to its own site; delete or ignore the rest |
| Uploaded zips (dashboard, career-intelligence, frontend-ready) | mined for UI pieces; archived |
| `odin-platform-updated.html` (71KB) | primary frontend donor — closest existing code to §9 |

---

## 12. THE VOICE (so every future AI session matches)

Odin speaks like someone who respects your time. Short sentences. No exclamation marks in UI copy. No "unlock your potential." Errors say what broke and what to do. The platform never congratulates a user for logging in. It congratulates them for proof.

When in doubt, the test is: *would this sentence survive being read aloud to a skeptical tradesman?*

---

*Canon v1.0 — June 12, 2026. Built from a year of Zack's work across Drive, GitHub, Replit, Netlify, Render, and four AI collaborators. One source of truth from here forward.*
