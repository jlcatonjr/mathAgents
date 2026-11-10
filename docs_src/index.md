# mathAgents

mathAgents is a harness for developing, verifying and explaining mathematical and logical proofs. It covers applied
and modelling mathematics, research-level mathematics, competition problems, logic and foundations, and proofs used
in the philosophy of science.

Every proof passes through an explicit pipeline:

- an informal problem card;
- a formal statement, checked by a person for fidelity;
- a proof strategy;
- named-rule derivations;
- tactic plans;
- a Lean 4 proof.

**The Lean kernel judges validity; a person judges statement fidelity.** A result is accepted only as *Blueprint +
Lean*: a blueprint (a dependency graph of lemmas, each node naming the Lean declaration that proves it) whose nodes
are Lean 4 declarations that build with no `sorry`, `admit` or unapproved axiom.

[Get started :material-arrow-right:](getting-started.md){ .md-button .md-button--primary }
[Open the explorer :material-arrow-right:](explorer/index.html){ .md-button }

## What is here

| Page | What it covers |
|---|---|
| [Getting Started](getting-started.md) | Installing the `mathagents` package and setting up an *instance*, a project repository that uses the harness's gates and pipeline agents. |
| [Concepts](concepts.md) | The pipeline stages, the gates that check each one, and who decides what. |
| [CLI Reference](cli-reference.md) | Every `mathagents` subcommand and option, read from the real parser. |
| [API Reference](api-reference/index.md) | The public Python API: one page per module, held to the code by the parity and signature tests. |
| [Explorer](interactive-explorer.md) | An in-browser explorer of the API, the proof library and the pipeline, generated from the repository. |
| [Proof Library](proof-library.md) | The dossiers, and how to read a result. |
| [Stability](stability.md) | What is public, and what the versioning promises. |
| [Changelog](changelog.md) | Release notes. |

## In one example

```python
from mathagents.dossiers import require_stage
from mathagents.kernel import load_kernel_report

result = require_stage(slug="p3-dutch-book", stage=8)
if not result.success:
    print("\n".join(result.errors))
print(load_kernel_report().status("MathAgents.P3DutchBook.converse_R2"))  # the status in reports/kernel/latest.json
```

This needs a checkout with a current kernel report and name index. Run `bash scripts/check_proof_integrity.sh`
(the G-KERNEL gate) and `python3 scripts/build_name_index.py` first. Both need Lean, as
[Getting Started](getting-started.md) explains. The API reads and checks records but never writes an approval or a
verdict, because those belong to people (see [Who decides what](concepts.md#who-decides-what)).

!!! note "Status"
    mathAgents is at 1.x. The Lean half of the proof standard is met for the P2 and P3 pilot dossiers. Their
    declarations are kernel-checked, and a person approved each formal statement against its stated source. For
    P2, that source is the *Stanford Encyclopedia of Philosophy*'s statement of Lewis's theorem, not Lewis 1976. No
    dossier has a blueprint yet, so no result meets the full Blueprint + Lean standard. See
    [how to read a result](proof-library.md#how-to-read-a-result).
