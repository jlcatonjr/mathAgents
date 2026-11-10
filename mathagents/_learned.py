"""The AGENTTEAMS-LEARNED block in a managed agent file: excluded from the lock digest, carried across re-renders.

An agent records what it learns about its project in one agent-owned region of its own file::

    <!-- AGENTTEAMS-LEARNED:BEGIN -->
    - notes the agent wrote
    <!-- AGENTTEAMS-LEARNED:END -->

``agentteams --sync-agent-docs`` copies that region between an agent's copies on every surface. mathagents hashes
the agent files it manages (``mathagents.lock.json``), so it must leave the region out of the hash, and it must
carry the region into a fresh render, or a consumer could not use the feature on the pipeline agents. Everything
outside the region stays governed exactly as before.

The grammar is agentteams' (``agentteams/learned_blocks.py``, 1.0.0rc8), re-implemented here with the stdlib
because mathagents does not depend on agentteams:

* **markdown** (``*.agent.md``, ``.claude/agents/*.md``): the two markers are whole lines at column 0, in the body
  (never in the YAML front matter) and never inside an ``AGENTTEAMS:BEGIN/END`` template fence. A file without a
  block gets one appended at its end, after one blank line.
* **recipe** (``.goose/recipes/*.yaml``): the block sits inside the single ``instructions: |`` scalar, its markers
  exactly at the scalar's indent; it is appended after the scalar's last non-blank line, after one blank line.
* **toml** (``.codex/agents/*.toml``, mathagents' extension): the block sits inside the
  ``developer_instructions = '''`` literal string, markers at column 0; it is appended before the closing ``'''``.

Fail-closed: a file whose markers are unbalanced, duplicated, misplaced (front matter, a fence, outside the
scalar), indented wrongly, or whose block content could escape the block (a fence token, a non-``\\n`` line break
or control character, a Unicode format character such as a bidi control or zero-width space) has no excludable
block. Nor does a block whose content trips the policy denylist (agentteams' learned-block denylist, the
instruction-override / identity-change / capability-lift / governance-bypass / permission-widening patterns of
``@security`` rule S-5): the block's text is read by the agent as part of its own instructions, so content that
reads as an override is never let past the lock. The digest of such a file is the digest of the whole file, which
never matches a lock entry recorded for the clean render, so the file reads as edited.

The block itself is not hash-governed, but it is not invisible either: the lock records each agent file's block
digest (``block_digest``), and ``sync`` and ``doctor`` report a block added, changed or removed since the lock.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

__all__ = ["BEGIN_MARKER", "END_MARKER", "MARKDOWN", "RECIPE", "TOML", "LearnedBlockError", "Parsed", "parse",
           "policy_problems", "digest", "block_digest", "carry", "strip"]

BEGIN_MARKER = "<!-- AGENTTEAMS-LEARNED:BEGIN -->"
END_MARKER = "<!-- AGENTTEAMS-LEARNED:END -->"
MARKDOWN, RECIPE, TOML = "markdown", "recipe", "toml"

_FENCE_BEGIN = re.compile(r"<!--\s*AGENTTEAMS:BEGIN\s+\S+")
_FENCE_END = re.compile(r"<!--\s*AGENTTEAMS:END\s+\S+")
_FENCE_TOKEN = re.compile(r"AGENTTEAMS[:\-]")
_FORBIDDEN = frozenset("\r\x00\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")
_INSTRUCTIONS = re.compile(r"^instructions:[ \t]*\|[ \t]*$")
_TOML_OPEN = "developer_instructions = '''"

# The learned-block policy denylist of agentteams 1.0.0rc8 at 5562222 (``agentteams/learned_blocks.py``, ``_POLICY_PATTERNS``,
# Codex settings added in 9b6f9c3),
# copied word for word because mathagents does not depend on agentteams. Matched case-insensitively on NFKC text
# with format characters removed; _GAP tolerates whitespace and punctuation between words.
_GAP = r"[\W_]*"
_NEAR = r"[\W\w]{0,60}?"
_POLICY = tuple((label, re.compile(rx, re.IGNORECASE)) for label, rx in (
    ("instruction override", rf"\bignore\b{_NEAR}\b(?:previous|prior|all|above|earlier)\b{_NEAR}\binstructions?\b"),
    ("instruction override", r"\bdisregard"),
    ("instruction override", rf"\byou{_GAP}are{_GAP}now\b"),
    ("identity change", rf"\bact{_GAP}as\b"),
    ("identity change", rf"\bnew{_GAP}roles?\b"),
    ("identity change", rf"\bnew{_GAP}(?:system{_GAP})?instructions?\b"),
    ("identity change", rf"\bfrom{_GAP}now{_GAP}on{_GAP}you\b"),
    ("capability lift", rf"\blimitations?{_GAP}(?:(?:is|are|have{_GAP}been|has{_GAP}been){_GAP})?lifted\b"),
    ("capability lift", rf"\byou{_GAP}(?:may|can){_GAP}now{_GAP}(?:write|edit|run|delete)\b"),
    ("capability lift", rf"\brestrictions?{_GAP}(?:(?:is|are|have{_GAP}been|has{_GAP}been){_GAP})?"
                        rf"(?:removed|no{_GAP}longer{_GAP}apply)\b"),
    ("capability lift", r"\bunrestricted\b"),
    ("constitutional-tier claim", rf"\btier{_GAP}(?:1|one|i)\b"),
    ("constitutional-tier claim", r"\bC\s*-\s*[1-5]\b"),
    ("constitutional-tier claim", rf"\bconstitutional{_GAP}core\b"),
    ("constitutional-tier claim", r"\boverrid(?:e|es|ing|den)\b"),
    ("governance bypass", rf"\b(?:skip|skipping|bypass|bypassing|disable|disabling|ignore|ignoring)\b{_NEAR}@?"
                          rf"\b(?:security|adversarial|conflict{_GAP}auditor)\b"),
    ("governance bypass", rf"\bwithout{_GAP}(?:any{_GAP})?(?:clearance|@?security)\b"),
    ("governance bypass", rf"\bno{_GAP}need{_GAP}(?:for|of){_GAP}(?:a{_GAP})?clearance\b"),
    ("permission/tool widening", rf"\bpermission{_GAP}mode"),
    ("permission/tool widening", rf"\bbypass{_GAP}permissions"),
    ("permission/tool widening", r"\bdangerously"),
    ("permission/tool widening", rf"\ballowed{_GAP}tools"),
    ("permission/tool widening", r"\btools\s*:"),
    ("permission/tool widening", r"\bhooks\s*:"),
    ("permission/tool widening", rf"\bmcp{_GAP}servers"),
    # Codex capability settings (the block can't set them, but prose can coax a weaker sandbox).
    ("permission/tool widening", rf"\bsandbox{_GAP}mode"),
    ("permission/tool widening", rf"\bapproval{_GAP}policy"),
    ("permission/tool widening", rf"\bdanger{_GAP}full{_GAP}access"),
))


class LearnedBlockError(ValueError):
    """The file's learned block (or its host structure) cannot be handled safely."""


@dataclass(frozen=True)
class Parsed:
    """``start``/``end``: offsets of the block (BEGIN line start, just past the END line); ``None`` without a
    block. ``insert_at``: where a block is appended. ``indent``: the marker indent. ``content``: the canonical
    block content (indent removed). ``last``: nothing but blank lines follows the block in its region (where
    an appended block sits)."""
    start: int | None
    end: int | None
    insert_at: int
    indent: str
    content: str
    last: bool = False


def _lines(text: str) -> list[str]:
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def _offsets(lines: list[str]) -> list[int]:
    out = [0]
    for line in lines:
        out.append(out[-1] + len(line))
    return out


def _fence_spans(lines: list[str]) -> list[tuple[int, int]]:
    spans, open_at = [], None
    for i, line in enumerate(lines):
        if open_at is None and _FENCE_BEGIN.search(line):
            open_at = i
        elif open_at is not None and _FENCE_END.search(line):
            spans.append((open_at, i))
            open_at = None
    if open_at is not None:
        spans.append((open_at, len(lines)))
    return spans


def _locate(lines: list[str], lo: int, hi: int) -> tuple[int, int] | None:
    begins = [i for i, line in enumerate(lines) if line.strip() == BEGIN_MARKER]
    ends = [i for i, line in enumerate(lines) if line.strip() == END_MARKER]
    if not begins and not ends:
        if any(BEGIN_MARKER in line or END_MARKER in line for line in lines):
            raise LearnedBlockError("a learned marker that is not a whole line")
        return None
    if len(begins) != 1 or len(ends) != 1:
        raise LearnedBlockError(f"expected one BEGIN and one END marker line, found {len(begins)} and {len(ends)}")
    b, e = begins[0], ends[0]
    if not lo <= b < e < hi:
        raise LearnedBlockError("the learned block is out of order or outside the allowed region")
    if any(f0 <= b <= f1 or f0 <= e <= f1 for f0, f1 in _fence_spans(lines)):
        raise LearnedBlockError("the learned block sits inside an AGENTTEAMS template fence")
    return b, e


def _content_problems(content: str) -> list[str]:
    problems = []
    if _FENCE_TOKEN.search(content):
        problems.append("contains an AGENTTEAMS fence or learned marker token")
    if any(c in _FORBIDDEN for c in content):
        problems.append("contains a line-break or control character other than \\n")
    if any(unicodedata.category(c) == "Cf" for c in content):  # bidi controls, zero-width characters
        problems.append("contains a Unicode format character (bidi control or zero-width)")
    if content and not content.endswith("\n"):
        problems.append("does not end with a newline")
    return problems


def policy_problems(content: str) -> list[str]:
    """The policy-denylist matches in learned-block ``content`` (empty when clean)."""
    text = "".join(c for c in unicodedata.normalize("NFKC", content) if unicodedata.category(c) != "Cf")
    return [f"policy: {label} ({' '.join(m.group(0).split())[:60]!r})"
            for label, rx in _POLICY if (m := rx.search(text))]


def _region(lines: list[str], kind: str) -> tuple[int, int, int, str]:
    """(first line, end line exclusive, insert line, indent) of the region a block may occupy."""
    if kind == MARKDOWN:
        body = 0
        if lines and lines[0].rstrip("\n") == "---":
            body = next((i + 1 for i in range(1, len(lines)) if lines[i].rstrip("\n") == "---"), None)
            if body is None:
                raise LearnedBlockError("unterminated YAML front matter")
        return body, len(lines), len(lines), ""
    if kind == RECIPE:
        heads = [i for i, line in enumerate(lines) if line.startswith("instructions:")]
        if len(heads) != 1 or not _INSTRUCTIONS.match(lines[heads[0]].rstrip("\n")):
            raise LearnedBlockError("expected exactly one plain `instructions: |` block scalar")
        first, end, indent = heads[0] + 1, len(lines), None
        for i in range(first, len(lines)):
            line = lines[i]
            if not line.strip():
                continue
            if line[0] not in " \t":
                end = i
                break
            if line[0] == "\t":
                raise LearnedBlockError("tab indentation in the instructions block")
            if indent is None:
                indent = line[: len(line) - len(line.lstrip(" "))]
        if not indent:
            raise LearnedBlockError("the instructions block scalar is empty")
        last = max((i for i in range(first, end) if lines[i].strip()), default=first - 1)
        return first, end, last + 1, indent
    if kind == TOML:
        opens = [i for i, line in enumerate(lines) if line.rstrip("\n") == _TOML_OPEN]
        if len(opens) != 1:
            raise LearnedBlockError(f"expected exactly one `{_TOML_OPEN}` line")
        close = next((i for i in range(opens[0] + 1, len(lines)) if lines[i].rstrip("\n") == "'''"), None)
        if close is None or any("'''" in line for line in lines[opens[0] + 1:close]):
            raise LearnedBlockError("the developer_instructions literal string is not closed by a `'''` line")
        return opens[0] + 1, close, close, ""
    raise LearnedBlockError(f"unknown host format {kind!r}")


def parse(text: str, kind: str) -> Parsed:
    """Locate the learned block of ``text`` (a ``kind`` host file); raise LearnedBlockError when it is unsafe."""
    lines = _lines(text)
    offs = _offsets(lines)
    lo, hi, insert, indent = _region(lines, kind)
    loc = _locate(lines, lo, hi)
    if loc is None:
        return Parsed(None, None, offs[insert], indent, "")
    b, e = loc
    for i, marker in ((b, BEGIN_MARKER), (e, END_MARKER)):
        if lines[i].rstrip("\n") != indent + marker:
            raise LearnedBlockError("learned markers must be whole lines at the host indent")
    content = []
    for line in lines[b + 1:e]:
        if line.startswith(indent):
            content.append(line[len(indent):])
        elif not line.strip():
            content.append("\n")
        else:
            raise LearnedBlockError("a learned-block line is indented less than its host (dedent)")
    text_content = "".join(content)
    problems = _content_problems(text_content) + policy_problems(text_content)
    if problems:
        raise LearnedBlockError("; ".join(problems))
    last = all(not line.strip() for line in lines[e + 1:hi])
    return Parsed(offs[b], offs[e + 1], offs[insert], indent, text_content, last)


def strip(text: str, kind: str) -> str:
    """``text`` without its learned block (the governed text). When the block is the last thing in its region,
    where agentteams and `carry` append it, the one blank separator line in front of it goes too.

    Raises LearnedBlockError when the block is unsafe. A file without a block is returned unchanged."""
    p = parse(text, kind)
    if p.start is None:
        return text
    head, tail = text[: p.start], text[p.end:]
    if p.last and head.endswith("\n\n"):  # the separator agentteams (and `carry`) put before an appended block
        head = head[:-1]
    return head + tail


def digest(data: bytes, kind: str | None) -> str:
    """The lock digest of a managed file: sha256 of its governed text (the learned block left out) for an agent
    file (``kind`` set), of all its bytes otherwise. An unsafe block, or bytes that are not UTF-8, make the
    digest that of the whole file (fail-closed: it then never matches the lock entry of a clean render)."""
    if kind is not None:
        try:
            return hashlib.sha256(strip(data.decode("utf-8"), kind).encode("utf-8")).hexdigest()
        except (LearnedBlockError, UnicodeDecodeError):
            pass  # fail-closed by design: an unsafe block is governed like any other byte of the file
    return hashlib.sha256(data).hexdigest()


def block_digest(data: bytes, kind: str) -> str | None:
    """sha256 of the canonical content of the file's safe learned block; None without one (or with an unsafe one,
    which ``digest`` already reports as an edit). The lock records it so a changed block is reported."""
    try:
        p = parse(data.decode("utf-8"), kind)
    except (LearnedBlockError, UnicodeDecodeError):
        return None
    return None if p.start is None else hashlib.sha256(p.content.encode("utf-8")).hexdigest()


def _render(content: str, indent: str) -> str:
    body = "".join(line if line == "\n" else indent + line for line in _lines(content))
    return f"{indent}{BEGIN_MARKER}\n{body}{indent}{END_MARKER}\n"


def carry(old: bytes, fresh: bytes, kind: str) -> tuple[bytes, str | None]:
    """``fresh`` (a new render) carrying the learned block of ``old`` (the file on disk).

    Returns ``(bytes to write, problem)``. ``fresh`` is returned unchanged when ``old`` has no block or an unsafe
    one, or when ``fresh`` already carries the same block. ``problem`` is set when ``old`` has a block that is not
    carried (unsafe, or with no safe place in ``fresh``); the caller must then refuse rather than drop it silently."""
    try:
        src = parse(old.decode("utf-8"), kind)
    except (LearnedBlockError, UnicodeDecodeError) as exc:
        # an unsafe block reads as an edit (``digest``); say so if an --overwrite is about to drop it
        return fresh, (f"its learned block is unsafe ({exc}) and is not carried"
                       if BEGIN_MARKER.encode() in old or END_MARKER.encode() in old else None)
    if src.start is None:
        return fresh, None
    try:
        text = fresh.decode("utf-8")
        dest = parse(text, kind)
    except (LearnedBlockError, UnicodeDecodeError) as exc:
        return fresh, f"the new render has no safe place for the learned block ({exc})"
    if dest.start is not None:
        if dest.content == src.content:
            return fresh, None
        return fresh, "the new render already carries a different learned block"
    prefix = text[: dest.insert_at]
    composed = prefix + ("\n" if prefix.endswith("\n") else "\n\n") + _render(src.content, dest.indent) \
        + text[dest.insert_at:]
    try:  # prove the carry changed nothing governed
        ok = parse(composed, kind).content == src.content and strip(composed, kind) == text
    except LearnedBlockError:
        ok = False
    if not ok:
        return fresh, "the learned block could not be carried without changing governed text"
    return composed.encode("utf-8"), None
