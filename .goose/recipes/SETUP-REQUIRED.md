<!-- AGENTTEAMS:BEGIN content v=1 -->
# SETUP-REQUIRED.md

The following **7 placeholder(s)** could not be automatically resolved
for project **mathAgents** and require manual attention.

---

## 1. `{PIP_PACKAGE_NAME}`

**Found in:** `multiple`
**Context:** The placeholder {PIP_PACKAGE_NAME} could not be auto-resolved.

**Action required:** Search for `{MANUAL:PIP_PACKAGE_NAME}` across all generated
agent files and replace with the correct value.

---

## 2. `{DOC_SITE_CONFIG_FILE}`

**Found in:** `multiple`
**Context:** The placeholder {DOC_SITE_CONFIG_FILE} could not be auto-resolved.

**Action required:** Search for `{MANUAL:DOC_SITE_CONFIG_FILE}` across all generated
agent files and replace with the correct value.

---

## 3. `{TRIGGER_CONTRACT_VERSION}`

**Found in:** `multiple`
**Context:** The placeholder {TRIGGER_CONTRACT_VERSION} could not be auto-resolved.

**Action required:** Search for `{MANUAL:TRIGGER_CONTRACT_VERSION}` across all generated
agent files and replace with the correct value.

---

## 4. `{BULK_MUTATION_THRESHOLD}`

**Found in:** `multiple`
**Context:** The placeholder {BULK_MUTATION_THRESHOLD} could not be auto-resolved.

**Action required:** Search for `{MANUAL:BULK_MUTATION_THRESHOLD}` across all generated
agent files and replace with the correct value.

---

## 5. `{SOURCE_OF_TRUTH_SPEC}`

**Found in:** `multiple`
**Context:** The placeholder {SOURCE_OF_TRUTH_SPEC} could not be auto-resolved.

**Action required:** Search for `{MANUAL:SOURCE_OF_TRUTH_SPEC}` across all generated
agent files and replace with the correct value.

---

## 6. `{DUPLICATE_CLUSTER_CAP}`

**Found in:** `multiple`
**Context:** The placeholder {DUPLICATE_CLUSTER_CAP} could not be auto-resolved.

**Action required:** Search for `{MANUAL:DUPLICATE_CLUSTER_CAP}` across all generated
agent files and replace with the correct value.

---

## 7. `{AUDIT_SLUG}`

**Found in:** `multiple`
**Context:** The placeholder {AUDIT_SLUG} could not be auto-resolved.

**Action required:** Search for `{MANUAL:AUDIT_SLUG}` across all generated
agent files and replace with the correct value.

---


Once all items above are resolved, invoke `@conflict-auditor` to verify consistency.

## Recommended `.gitignore` entries

Your generated team writes two machine-local caches that should **not** be committed. Add these
to this repository's `.gitignore`:

```gitignore
# agentteams retrieval validation-cache sidecars — machine-local, rebuilt on demand
**/references/memory-index.vcache
**/references/code-index/
```

Already committed one by mistake? `.gitignore` does not untrack an existing file — use
`git rm --cached <path>` first, then confirm with `git ls-files | grep vcache`.
<!-- AGENTTEAMS:END content -->
