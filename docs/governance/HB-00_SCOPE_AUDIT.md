# HEIRBUD — WHOLE-PROJECT SCOPE AUDIT

Project ID: PRJ-HB7K4
Assessment date: July 30, 2026

> Mirrored from Google Drive. This is a product and operational assessment,
> not legal advice.

# EXECUTIVE VERDICT

HEIRBUD is no longer merely an idea. It has a working prototype stack, real
public-source data, a pipeline model, a dashboard, outreach generation,
contract generation, follow-up logic, and a credible operational premise. The
project has crossed the line from concept into system.

It has not crossed the line into a safe production business.

The central issue is not lack of features. It is contradiction. The compliance
pack correctly states that Wisconsin locator fees may not exceed 10% and that a
locator agreement is void while property has been in state custody for less than
24 months. The current code generates 12%, 15%, and 20% fees, defaults contracts
to 15%, and contains no custody-age eligibility gate. That is a launch-blocking
conflict, not a future refinement.

The strongest direction is to reposition HEIRBUD as a compliance-first recovery
operations platform. Automation should accelerate verified, approved work. It
should never automate eligibility assumptions, unsupported urgency, uncontrolled
personal-data enrichment, or noncompliant agreements.

# CRITICAL LAUNCH BLOCKERS

1. **Fee logic conflicts with Wisconsin rules.** The outreach generator
   calculates 12/15/20%. The contract generator defaults to 15%. The API model
   defaults to 15%. The daily action queue estimates fees at 12/15%. Wisconsin
   DOR guidance caps a locator fee at 10% of the actual recovered value. Every
   calculation, default, template, projection, and agreement must be corrected
   and centrally controlled before any live use.
2. **No 24-month custody eligibility gate.** A locator agreement is void if the
   property has been in DOR custody for less than 24 months. The system needs a
   verified custody date, eligibility date, evidence, reviewer + timestamp, and
   an automatic prohibition on agreement generation until eligible.
3. **Agreement generation is incomplete.** WI requires: service explanation,
   clear fee statement, property value before and after the fee, property
   description, holder name and address, owner signature, and a prominent
   free-claim disclosure. A lawyer-reviewed template should replace programmatic
   improvisation.
4. **No authentication or authorization.** The FastAPI service permits
   unrestricted cross-origin access and exposes prospect/pipeline endpoints with
   no auth, roles, session security, or tenant separation.
5. **Personal data controls are absent.** PII sits in an unencrypted local
   SQLite file with no retention policy, access log, masking, or secure deletion.
6. **Real records appear in prototypes and documents.** Development, demos, and
   generated examples should use synthetic data.
7. **Enrichment is not governed.** Code generates links to commercial
   people-search sites without an approved-source policy.
8. **Outreach contains unsupported claims.** Older scripts generalize about
   mandatory affidavits, notarization, delay, inflation loss, or liquidation
   risk as pressure tactics.
9. **The fallback identifier is unstable.** The importer used Python's
   process-randomized `hash()` for fallback IDs, defeating deduplication. Use a
   deterministic hash of normalized source fields, or the official property ID.
10. **The system lacks release discipline.** Multiple folders and packages hold
    overlapping versions with no canonical build declared.

# RECOMMENDED PRODUCT DEFINITION

A compliance-controlled case-management and recovery-support system for verified
unclaimed-property records, designed to help an operator identify eligible
cases, communicate transparently with owners, assist claim preparation, preserve
a full audit trail, and measure recovery outcomes.

This definition intentionally EXCLUDES: autonomous cold outreach without human
approval; automatic identity assertions; automatic contract issuance before
eligibility review; collection of claimant SSNs or banking info outside the
official state process; legal determinations made by a language model;
uncontrolled bulk messaging.

# FIRST 30-DAY BUILD ORDER

- **Week 1 — Stop contradictions.** Declare one canonical package. Set the global
  WI fee ceiling to 10%. Disable agreement generation until eligibility is
  proven. Replace real demo records with synthetic data. Mark the server and
  HTML dashboard prototype-only.
- **Week 2 — Establish truth.** Define the canonical data dictionary. Add
  source-file checksum, retrieval date, verification date, custody date,
  eligibility date, and evidence fields. Create suppression/consent/contact-source
  fields. Build deterministic deduplication.
- **Week 3 — Build the controlled pilot.** Select a small verified batch. Use
  approved USPS-first outreach. Log every contact. Prohibit automated sending.
  Measure deliverability, response, verification, and owner trust.
- **Week 4 — Harden and decide.** Add authentication, roles, secure secrets,
  backups, and audit logs. Review pilot economics. Decide: internal tool,
  commercial SaaS, or managed service.

# STRATEGIC COMMENTS (abridged)

1. The moat is not finding the list — it's verified data lineage, compliant
   timing, claimant experience, complex-case handling, and operational evidence.
2. High dollar ≠ high priority. Blend value, eligibility, match confidence,
   complexity, contactability, cycle time, and compliance risk.
3. "Maximum automation" is the wrong top-level objective. The real objective is
   **maximum trustworthy throughput per human decision.** Automate clerical work;
   keep identity, eligibility, legal interpretation, and approvals under review.
4. The best conversion asset is proof, not persuasion.
5. USPS-first is strategically sensible for the pilot.
6. Owner self-service should be treated as a product feature.
7. Complex claims (estates, trusts, dissolved businesses) are the premium tier.
8. Multi-state expansion should be schema-driven (a rule pack per state), not
   copy-driven.
9. Keep money projections out of the action queue until eligibility is confirmed.
10. Build the audit trail as a first-class feature.
11. Do not make an LLM the legal brain.
12. The current prototype is worth preserving — freeze as v0.2, correct the
    highest-risk logic, write tests, validate requirements before a rebuild.

# FINAL ASSESSMENT

HEIRBUD has a strong skeleton and a dangerous gap between prototype confidence
and operational readiness. The project should continue — but not under the
premise that more automation is automatically progress. The next leap is
governance: one source of truth, verified eligibility, approved language, secure
data, release discipline, and measurable pilot evidence.

# OFFICIAL REFERENCES REVIEWED

- Wisconsin DOR: Heir Finders or Locator Services, guidance dated 2025-11-04.
- Wisconsin DOR: Unclaimed Property claim process and documentation guidance.
- Wisconsin DOR: Heirship claims guidance dated 2026-01-01.
