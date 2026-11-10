"""Apply the mathAgents roster pin + orphan cleanup to the repo in CWD (used for sim and real run)."""
import json, pathlib
ROSTER = ["primary-producer", "quality-auditor", "cohesion-repairer", "technical-validator",
          "format-converter", "reference-manager", "output-compiler", "visual-designer",
          "post-production-auditor", "retrieval-integrator", "research-analyst"]
for p in ("brief.json", ".github/agents/_build-description.json"):
    d = json.loads(pathlib.Path(p).read_text()); d["selected_archetypes"] = ROSTER
    pathlib.Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
old = ["topic-scoping-expert", "literature-review-expert", "main-analysis-expert", "conclusion-expert"]
targets = [f".github/agents/{n}.agent.md" for n in old] + [f".claude/agents/{n}.md" for n in old] \
    + [f".goose/recipes/{n}.yaml" for n in old] \
    + [f"{s}/references/ref-bibtex-reference.md" for s in (".github/agents", ".claude/agents", ".goose/recipes")] \
    + [".goose/recipes/tool-pandoc.yaml", ".goose/recipes/AGENTS.md"]
for t in targets:
    p = pathlib.Path(t)
    print(("removed " if p.exists() else "absent  ") + t); p.unlink(missing_ok=True)
