# Research Data Collection — Privacy, Consent & Retention Policy

> **⚠️ DRAFT v0.1 (2026-10-15) — NOT LEGAL ADVICE — NOT IN FORCE.**
> This document was written by an engineer and an AI assistant, not a lawyer.
> It has **not** had legal review. **No data may be collected from any real person under
> it** until every item in §14 (Sign-off gate) is complete, including review by a
> qualified lawyer and written sign-off by the project owner. That gate stays closed
> however complete this draft looks.

## 0. How this draft was written

No controller, server operator or jurisdiction has been chosen yet. So this draft
assumes that **all** of the following apply at once, and where they differ it adopts
the strictest requirement:

| Regime | Why it might apply | What it drives in this draft |
|---|---|---|
| US COPPA (16 CFR 312) | Minecraft's player base includes under-13s | Under-13s are never collected from. No "actual knowledge" loophole is relied on (§3). |
| EU GDPR, incl. Art. 8 ("GDPR-K") | Any EU-resident participant | Explicit consent. Data minimisation. Data-subject rights. DPIA. Breach notification. The age of digital consent varies by member state (13–16), so 16 is assumed. |
| UK GDPR + Age Appropriate Design Code (AADC) | Any UK-resident participant | The AADC protects **everyone under 18**. Profiling must be off by default for them. That is why §3 sets an adult-only floor. |
| US state privacy / biometric statutes (e.g. IL BIPA, TX CUBI, WA, CCPA/CPRA) | US participants | Aim behaviour is treated as potentially biometric-like (§5). No sale or sharing. Written retention schedule. |

## 1. Scope

This policy covers only the **research data-collection phase**: recording rotation and
combat telemetry on a **private test server** to build and evaluate the anticheat
model.

It does **not** cover running the anticheat in production on a public server. That is
different processing, typically justified as legitimate interest or contract rather
than consent, and needs its own assessment before Phase 6.

## 2. Hard constraint: where real data can come from

Minecraft has **no reliable server-side age signal**. The protocol carries no age,
Microsoft account age is not exposed to servers, and anything the client reports
can be spoofed.

So age rules cannot be enforced on a public server. In practice this means:

> Real data may be collected **only** on a private, allow-listed test server where
> every participant has been individually recruited, age-verified **out-of-band**
> (§3.2) and has given explicit consent **before** their account is added to the
> allow-list. **Public-server collection is out of scope under this policy, without
> exception.**

This limits where real data can ever come from. It is not just a policy preference:
the dataset will be small, adult-only, and drawn from people we can recruit
directly. The model's results must be reported with that limitation.

## 3. Age

### 3.1 Floor

| Age | Rule | Source of strictness |
|---|---|---|
| Under 13 | **Never collected.** No exceptions, no parental-consent route. | COPPA |
| 13–15 | **Not collected.** A verified parental-consent flow is a documented future option only. It is not built and is not to be built speculatively. | GDPR Art. 8 (up to 16 in some member states) |
| **16–17** | **Not collected under this draft.** ⚠️ This is **stricter than the project brief**, which excluded under-16s. See the note below. | UK AADC covers all under-18s |
| 18+ | Eligible, subject to §4 consent. | — |

> **Decision needed from the project owner.** The brief set the default exclusion at under-16.
> But the brief also says to satisfy the strictest overlap, and under that rule the UK AADC
> treats 16–17-year-olds as children. AADC Standard 12 requires profiling to be **off by
> default** for children unless there is a compelling reason, and research collection of
> behavioural telemetry is profiling. Including 16–17s would therefore need either
> (a) a documented compelling-reason assessment plus a DPIA that covers children, or
> (b) excluding UK-resident 16–17s specifically, which would require reliable residency
> checks we don't have. Adults-only is the simplest compliant position. Change it only
> on legal advice.

### 3.2 Verification (out-of-band, before allow-listing)

- Age is checked **before** consent is recorded and **before** the Minecraft account
  is allow-listed. It is never inferred from gameplay, and nothing the client
  reports is used.
- Acceptable methods are for the lawyer to confirm. Candidates, least intrusive
  first: participants who are already known adults (e.g. university staff or
  students over 18 recruited through an ethics-approved channel); or a one-time
  check by a recruiter. In both cases **only a "verified 18+: yes" flag and the
  verification date are stored. No ID documents or dates of birth are stored.**
- If a participant is later found to be under 18: stop collection immediately,
  delete **all** data linked to their pseudonym within 72 hours (including derived
  features and any training-set membership), record the deletion, and do not keep
  anything "for analysis".

## 4. Lawful basis & consent

- **Lawful basis:** explicit consent. That is GDPR/UK GDPR Art. 6(1)(a) together
  with Art. 9(2)(a), because the data is treated as potentially special category
  (§5).
- **Requirements for valid consent:**
  1. **Freely given.** Taking part is voluntary. Declining or withdrawing costs
     nothing except access to the research server itself. Consent is never bundled
     with any other server's terms of service.
  2. **Specific and granular.** There are separate opt-in checkboxes, all unticked
     by default, for: (a) recording telemetry; (b) using it to train models;
     (c) using it in evaluation sets; (d) optionally, being contacted about future
     studies.
  3. **Informed.** The participant information sheet (Appendix A) is shown in full
     before consent.
  4. **Unambiguous and recorded.** We store the policy version, a hash of the
     information-sheet text, which options were ticked, a timestamp and the
     pseudonym. That record is the only identifying link we keep (§6).
  5. **As easy to withdraw as to give.** Withdrawal works through an in-game command
     on the research server **and** by email. Withdrawal stops new collection
     immediately and triggers erasure (§9).
- **Other participants are data subjects too.** Each tick record includes the
  client-perceived positions of *nearby entities*, which includes other players.
  Collection may run **only while every player connected to the server is an
  enrolled participant**. The capture layer must drop the positions of any entity
  whose UUID is not on the allow-list.
- **People who operate cheat clients** (team members running Wurst, Meteor or
  LiquidBounce in isolated VMs to produce cheat-side data) are also data subjects.
  They give the same consent, on a separate form that makes the purpose of their
  sessions clear.

## 5. What is collected (data inventory)

Collection follows the data-minimisation principle: if a field isn't listed here,
it isn't collected.

| Data | Purpose | Notes |
|---|---|---|
| Per-tick yaw/pitch, whether rotation was sent, forced-rotation flag | Feature extraction | Core signal |
| Attack events (target entity id), main-hand item *class* | Window anchoring, conditioning | Item class only, not item names or NBT |
| Own position per tick | Context features (own movement speed) | Coordinates on the research world only |
| Nearby **enrolled** entities' client-perceived relative positions and hitbox size | Aim-error features | Non-enrolled entities are dropped at capture |
| Ping estimate | Conditioning, data-quality gating | |
| Client protocol version | Spec compatibility | |
| Pseudonym (§6) | Linking sessions for per-player analysis and erasure | |
| Consent record (§4) | Accountability | Stored separately from telemetry |

**Explicitly not collected:** chat; usernames or display names in telemetry; IP
addresses (the server sees them operationally, but they are never written to the
research dataset); client brand or mod lists of participants; skins; voice; any
data from outside the research server.

**Treated as potentially special-category / biometric-like.** Published work (e.g.
the UWEC Minecraft mouse-dynamics papers) uses mouse and aim behaviour to
**identify individuals**. We therefore assume this telemetry could identify people
and add the following safeguards:

- It is **prohibited** to use the data to identify, re-identify or authenticate any
  person.
- No linking to other datasets.
- Explicit consent as the legal basis (§4).
- Whether specific US biometric statutes apply is a question for the lawyer (§15).

## 6. Pseudonymisation

- At capture, the Minecraft UUID is replaced with `HMAC-SHA256(key, uuid)`. The key
  is held **offline**, separately from the dataset, by one named custodian.
- The UUID → pseudonym mapping exists only to process withdrawal and erasure
  requests. Destroying the key at project end leaves the remaining data unlinkable.
- Pseudonymised data is **still personal data** under GDPR. Every obligation in
  this policy continues to apply to it.

## 7. Use limitations

- Data is used only for building and evaluating the anticheat model described in
  `docs/project-brief.md`.
- The research data is **never used to take action against a participant** (no
  bans, flags or reports). This keeps it out of the scope of GDPR Art. 22
  (automated decision-making).
- No sale, rental or sharing with third parties. No publication of raw or per-tick
  data.
- Publications may contain only aggregate statistics, with any group under 5
  participants suppressed.
- Releasing any dataset would need fresh, specific consent and a new review.
- **No LLM or third-party AI service processes raw participant telemetry.** The
  brief's offline LLM uses (hard-negative generation, drift summaries) may only
  ever see synthetic or aggregate data.

## 8. Storage & security

- **Never stored in consumer cloud-sync folders.** This repository lives in a
  OneDrive-synced Desktop folder, so raw data must sit outside it, under
  `$FMAC_DATA_ROOT`, on an encrypted volume.
- Raw data is encrypted at rest. Access is limited to named project members and
  logged.
- Analysis copies are allowed only on encrypted devices and are deleted after use.
- Hosting location is chosen together with the lawyer. If data leaves the EEA or
  UK, a transfer mechanism (SCCs or UK IDTA) is required before it moves.
- The capture plugin writes to local storage on the research server and nowhere
  else: no telemetry to third-party endpoints. The Discord webhook (Phase 6)
  **never carries participant research data**.

## 9. Retention & deletion

| Item | Retention | Deletion trigger |
|---|---|---|
| Raw tick logs | Max **12 months** from capture, or project end if sooner | Scheduled job; withdrawal; under-18 discovery |
| Derived feature windows | Same as raw | Same |
| Trained models | While in use | Withdrawn participants' data is excluded from the **next** training run, at most 90 days after withdrawal. Already-trained weights are not "unlearned"; participants are told this up front (Appendix A). |
| Consent records | Duration of processing + 3 years (evidence of lawful basis) | Scheduled job |
| HMAC key | Until project end | Destroyed at project end, which makes the residue unlinkable |
| Age-verification flag | Same as consent record | Same |

Erasure requests are completed within **30 days**. Each one is logged with what was
deleted. Deletion must be implemented as a tested job before the gate opens (§14);
a manual procedure doesn't count.

## 10. Data-subject rights

Participants have the right to access, rectification, erasure, restriction,
portability, objection, and withdrawal of consent at any time. Responses are due
within one month. There is no fee. Identity is verified through the participant's
enrolment channel, not by asking for more personal data.

## 11. Data Protection Impact Assessment

A DPIA is **mandatory before collection starts**. The triggers are systematic
monitoring of behaviour, innovative technology, and potentially biometric-like
data. It must cover at least:

- necessity and proportionality
- re-identification risk of aim data
- the nearby-entity data of other participants
- risk from cheat-client VMs (malware containment)
- storage location
- deletion and unlearning limits
- residual risks, signed off by the controller

## 12. Breach response

- Notify the relevant supervisory authority within **72 hours** of becoming aware of
  a breach, unless it is unlikely to pose a risk.
- Notify participants without undue delay if the risk is high.
- Keep a breach log, whether or not notification was required.

## 13. Roles (to be filled before the gate opens)

| Role | Name | Status |
|---|---|---|
| Controller (legal entity or person responsible) | — | **TBD** |
| Contact for data-protection requests | — | **TBD** |
| EU/UK representative (Art. 27), if the controller is outside the EU/UK | — | **TBD / maybe N/A** |
| HMAC key custodian | — | **TBD** |
| Ethics/IRB approval, if run through an institution | — | **TBD** |

## 14. Sign-off gate (all items required; enforced in code by `collection.real_players.enabled`)

- [ ] Controller and contact named (§13).
- [ ] Qualified legal review completed for every jurisdiction participants may live in; this draft revised accordingly and re-versioned.
- [ ] Age-floor decision (§3.1) confirmed by the project owner on legal advice.
- [ ] DPIA completed and signed (§11).
- [ ] Out-of-band age-verification procedure documented and approved (§3.2).
- [ ] Consent flow implemented and tested; consent records stored separately (§4).
- [ ] Enrolled-only capture filter implemented and covered by a test (§4, §5).
- [ ] Pseudonymisation and offline key custody in place (§6).
- [ ] Storage environment provisioned to §8, outside any sync folder.
- [ ] Retention and erasure jobs implemented and tested (§9).
- [ ] Mojang/Microsoft EULA and Minecraft Usage Guidelines checked for server data-collection terms (§15).
- [ ] **Written sign-off by the project owner** recorded in `docs/signoffs/` with the policy version and SHA-256 of this file. The plugin refuses to enable real-player collection unless the configured sign-off hash matches (design: `docs/adr/0003-collection-gate.md`).

## 15. Open questions for the lawyer

1. Does a 1.21.x rotation and combat telemetry stream, pseudonymised, count as biometric
   or special-category data in any target jurisdiction? Is explicit consent the right
   basis, or would a research exemption fit better?
2. Is adults-only plus out-of-band verification sufficient under the AADC and COPPA
   for a private research server? Which verification methods are proportionate?
3. Is "excluded from the next retraining, no unlearning" an acceptable answer to
   erasure requests for trained model weights?
4. Do Microsoft/Mojang's EULA, Usage Guidelines or Services Agreement restrict
   collecting player telemetry for research on a self-hosted server?
5. Is the nearby-entity data of other enrolled participants adequately covered by
   their own consent?

---

## Appendix A — Participant information sheet (draft text)

> **Research study: detecting cheating in Minecraft PvP from aim behaviour.**
>
> **What we record:** while you're on the research server, your view rotation once
> per game tick, your attacks, which kind of item you're holding (e.g. "sword"),
> your position, your connection's ping, and where other participants near you
> appeared on your screen. We **do not** record chat, your username, your IP address
> or anything outside the research server.
>
> **Why:** to train and test a system that learns what normal human aim looks like,
> so that cheating can be detected without wrongly accusing real players.
>
> **Who you are to us:** we replace your Minecraft account ID with a code. The key
> that links the code back to you is stored offline, separately, and is destroyed
> when the project ends.
>
> **What we will never do:** ban or report you based on this data, sell or share it,
> publish your individual data, or use it to identify you.
>
> **Your choices (tick any, none are required):**
> ☐ Record my gameplay telemetry ☐ Use it to train models ☐ Use it to evaluate models
> ☐ Contact me about future studies
>
> **Changing your mind:** type `/fmac withdraw` on the server or email [TBD]. We stop
> recording immediately and delete your data within 30 days. If your data was
> already used to train a model, it is left out of the next training run, at most
> 90 days later. We can't remove it from a model that has already been trained;
> that model is retired when it's replaced.
>
> **How long:** raw data is kept at most 12 months.
>
> **You must be 18 or over to take part.**
>
> **Contact / controller:** [TBD]. You can also complain to your data-protection
> authority.
