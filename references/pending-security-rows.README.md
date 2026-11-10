# Pending security rows (fallback)

`pending-security-rows.csv` holds `@security` rows that a session could not write to
`.github/agents/references/security-decisions.log.csv`, for example because a sandbox denies writes
to `.github/`. Without it, such a clearance survived only in a gitignored plan and was lost (the
2026-10-04 toolchain push; see the retroactive row of 2026-10-05). Same columns as the log.

**Rules** (security review 2026-10-05, conditions P1–P6):

- **P1. A pending row is never a clearance.** No gate, script or agent treats this file as one.
- **P2. Commit the pending row before the action, or in the same commit.** A row that lives only in
  `tmp/` does not satisfy C-5.
- **P3. Transfer word for word.** The next session that can write `.github/` copies each row unchanged
  into all three logs (`.github/agents`, `.claude/agents`, `.goose/recipes`). It then appends a
  separate `@security` row that reviews the transferred one, cites the commit that added it
  (`git log -- references/pending-security-rows.csv`), and says "transferred from pending on <date>".
- **P4. Add only.** A row is removed from this file only in the commit that transfers it.
- **P5. No transfer without provenance.** A row with no matching plan or work-summary entry is
  reported, not transferred.
- **P6. Not a way around the sandbox.** This fallback records clearances; it grants no right to write
  `.github/`.
