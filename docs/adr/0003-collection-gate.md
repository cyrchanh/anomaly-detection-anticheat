# ADR 0003 — Hard gate on real-player data collection

- **Status:** Accepted (design). Implementation lands in Phase 4 together with the plugin.
- **Date:** 2026-10-15

## Decision

Real-player collection is controlled by `collection.real_players.enabled`. It defaults
to `false`, and setting it to `true` is **not enough** to turn collection on. At
startup the plugin also requires:

1. `collection.real_players.signoff_file` points to a file in `docs/signoffs/` that
   records the policy version, the signer, the date, and the **SHA-256 of
   `docs/privacy-consent-policy-*.md`** the sign-off refers to.
2. The configured policy file's SHA-256 matches the hash in that sign-off. So editing
   the policy invalidates the sign-off until it's renewed.
3. An allow-list of enrolled pseudonymised participants is configured. Capture runs
   only while **every** connected player is enrolled, and drops nearby-entity data for
   any non-enrolled UUID.
4. The data root is outside any known cloud-sync folder: OneDrive, Dropbox, Google
   Drive and iCloud path markers are refused.

If any check fails, the plugin logs the reason and runs with collection **off**. It
never "warns and continues".

## What this gate does not cover

- **Cheat-client recordings by team members on the isolated test VM** are covered by the
  staff consent form (policy §4). They go through the same gate.
- **Synthetic data and fixtures** need no gate.
- **Shadow-mode *scoring* (Phase 4) on a server without collection enabled** keeps only
  aggregate counters in memory and writes no per-player telemetry. Its design gets
  reviewed again before Phase 4 starts.
