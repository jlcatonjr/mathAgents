"""Internal: which files of this checkout make up the harness (D35, docs/module.md).

Read by ``setup.py`` (which copies them into the wheel under ``mathagents/_harness/``, same layout) and by
the CLI (which vendors some of them into an instance). Paths are relative to the checkout. Stdlib only:
``setup.py`` imports this module before the package is installed.
"""
from __future__ import annotations

# gate scripts (scripts/ minus the operator, maintenance, researchteam-bridge and test tooling)
GATE_SCRIPTS = (
    "scripts/instance_root.py", "scripts/proof_integrity.py", "scripts/check_proof_integrity.sh",
    "scripts/axiom_allowlist.py", "scripts/validate_dossier.py", "scripts/dossier_structure.py",
    "scripts/check_lean_bindings.py", "scripts/check_blueprint_consistency.py", "scripts/build_name_index.py",
    "scripts/preferences.py", "scripts/snapshot_kernel.py", "scripts/log_counterexample.py",
    "scripts/validate_registries.py", "scripts/probe_machine.py",
    "scripts/validate_evidence.py", "scripts/validate_claim_ledger.py",  # the evidence layer (mathAgents' own)
    "scripts/lean_docs.py",  # the documentation matching the instance's pinned Lean and Mathlib
    "scripts/lean_pin.py",  # the instance's Lean pin (P1-P4) and its consistency checks
    "scripts/scan_lean_draft.py",  # a returned Lean draft is scanned before it is piped to Lean or written (D39)
    "scripts/check_strategy_sha.py",  # proposal gate: a strategy review names the strategy it reviews (write policy)
    "scripts/lean/AxiomAudit.lean", "scripts/lean/NameIndex.lean",
)

# the eleven bespoke pipeline agents (D24, D27, D28), canonical in .github/agents
AGENTS = (
    "interpretation-advisor", "statement-formalizer", "fidelity-auditor", "proof-strategist", "logic-articulator",
    "tactic-planner", "lean-prover", "counterexample-hunter", "axiom-auditor", "engine-advisor", "lean-informalization",
)
AGENT_FILES = tuple(f".github/agents/{a}.agent.md" for a in AGENTS)

# harness-owned contract files the gates read from the instance root: vendored by `mathagents init`,
# refreshed by `mathagents sync`, and hash-locked (a local edit is never overwritten silently)
VENDORED = (
    "references/schemas/counterexample-log.schema.json", "references/schemas/fidelity-record.schema.json",
    "references/schemas/gax-record.schema.json", "references/schemas/object-logics.schema.json",
    "references/schemas/prover-engines.schema.json", "references/object-logics.json", "references/prover-engines.json",
    "docs/charter/decisions-summary.md", "docs/kernel-gate.md", "docs/lean-version-governance.md",
)

# instance-owned files seeded once by `mathagents init` from these defaults, never overwritten afterwards
SEEDED = ("references/preferences.toml", "references/axiom-allowlist.json")

# reference reading for agents and operators (shipped, not vendored)
DOCS = ("docs/module.md", "docs/baseagent-integration-plan.md", "reports/02-harness-spec.md",
        "docs/lean-toolchain-upgrade.md")

# the toolchain-bump wave's tools (`mathagents bump`; docs/lean-toolchain-upgrade.md): shipped, run from the
# harness, never vendored, and outside the gate digest (they decide no verdict)
BUMP_TOOLS = (
    "scripts/toolchain_bump/bump_trial.sh", "scripts/toolchain_bump/statement_types.py",
    "scripts/toolchain_bump/statement_drift.py", "scripts/toolchain_bump/lean_template.py",
    "scripts/toolchain_bump/StatementTypes.lean", "scripts/toolchain_bump/StatementDeps.lean",
)

# harness-published data read from the harness, never from the instance: the Lean toolchains the gates are
# verified on (`mathagents status`, `mathagents doctor`; docs/lean-version-governance.md)
VERIFIED_TOOLCHAINS = "references/verified-toolchains.json"
HARNESS_DATA = (VERIFIED_TOOLCHAINS,)

ALL = GATE_SCRIPTS + AGENT_FILES + VENDORED + SEEDED + DOCS + BUMP_TOOLS + HARNESS_DATA
