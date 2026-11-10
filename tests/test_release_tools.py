"""Release tooling (docs/release-checklist.md; STABILITY.md): the operator's tag script and the toolchain lock."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG_RELEASE = ROOT / "scripts" / "operator" / "tag-release.sh"


def run_tag_release(env: dict, cwd: Path) -> subprocess.CompletedProcess:
    key = cwd / "key"
    key.write_text("not a key")
    return subprocess.run(["bash", str(TAG_RELEASE), "0" * 40, str(key)], cwd=cwd, env=env, capture_output=True,
                          text=True)


def test_tag_release_refuses_inside_an_agent_session(tmp_path):
    env = {**os.environ, "CLAUDECODE": "1"}
    r = run_tag_release(env, tmp_path)
    assert r.returncode == 1 and "plain Terminal" in r.stderr, r.stderr


def test_tag_release_refuses_without_allowed_signers(tmp_path):
    """The signers file lives outside every write root (~/.config/agentteams/allowed_signers, policy §2)."""
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "pyproject.toml").write_text('version = "1.0.0"\n')
    r = run_tag_release(env, tmp_path)
    assert r.returncode == 1 and "allowed_signers" in r.stderr, r.stderr


def test_tag_release_never_writes_the_trust_root():
    script = TAG_RELEASE.read_text()
    assert not re.search(r">>?\s*\"?\$SIGNERS|>>?\s*allowed_signers|tee .*allowed_signers", script)
    assert 'SIGNERS="$HOME/.config/agentteams/allowed_signers"' in script  # outside every write root


def test_tag_release_verifies_with_the_neutralised_command():
    script = TAG_RELEASE.read_text()
    assert "SSH_KEYGEN=/usr/bin/ssh-keygen" in script and 'gpg.ssh.program="$SSH_KEYGEN"' in script
    for flag in ("core.hooksPath=/dev/null", "core.fsmonitor=false"):
        assert flag in script, flag
    assert "SHA256:IPdnLwlFdHNhr7QGKVWU40BOKyYzv2u8qxP/qxnzTNM" in script


def test_the_changelog_records_each_released_toolchain():
    changelog = (ROOT / "CHANGELOG.md").read_text()
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    as_tuple = [tuple(map(int, v.split("."))) for v in released]
    assert released and as_tuple == sorted(as_tuple, reverse=True), released  # newest first
    version = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    if re.fullmatch(r"\d+\.\d+\.\d+", version):  # a release commit: its own section is the newest
        assert released[0] == version, (released[0], version)
    for section in re.split(r"^## ", changelog, flags=re.M)[1:]:
        if section.startswith("[Unreleased]"):
            continue
        assert "**Toolchain:**" in section, section.splitlines()[0]


def test_tag_release_allows_only_the_release_key():
    """Policy §2 names exactly one key for 1.0.x: any other key is refused, never waved through on a prompt; a
    commented-out allowed_signers line does not count."""
    script = TAG_RELEASE.read_text()
    assert '[[ "$KEY_FP" == "$RELEASE_FP" ]] || die' in script
    assert "anyway" not in script
    assert "grep -v '^[[:space:]]*#' \"$SIGNERS\"" in script


def test_tag_release_ignores_global_git_config_and_reads_the_fingerprint_from_stderr():
    """researchteam #52 @security: url.insteadOf in global config isn't neutralised by -c flags, and a tag message can
    mimic a verification line, so the signer is parsed from git's stderr only."""
    script = TAG_RELEASE.read_text()
    assert "export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null" in script
    assert 'for v in ${!GIT_@}; do unset "$v"; done' in script  # no GIT_* overrides from the environment
    assert 'tag -v "$TAG" 2>&1 >/dev/null' in script  # stderr kept, stdout (the tag message) dropped


def test_tag_release_signs_in_a_fresh_clone_not_the_working_checkout():
    """agentteams-f3 review (2026-10-18, HIGH): a working checkout's .git/config is agent-writable (gpg.ssh.program,
    core.sshCommand, url.*.insteadOf, hooks), so the script clones the fixed URL into a temp dir and works only there."""
    script = TAG_RELEASE.read_text()
    assert 'URL="git@github.com:jlcatonjr/mathAgents.git"' in script and 'clone -q --no-checkout "$URL" "$TMP/repo"' in script
    assert 'GITX=(git -C "$TMP/repo"' in script and "git fetch -q origin --tags" not in script
    assert '[[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]]' in script  # a full SHA, not a ref resolved after the checks
    assert '[[ "$VERSION" != "$PARENT_VERSION" ]]' in script


def test_tag_release_requires_a_green_long_suites_run_on_the_commit():
    """D46: the long suites run before every release; the tag script refuses a commit they have not passed."""
    script = TAG_RELEASE.read_text()
    assert 'head_sha=$COMMIT&status=success' in script
    # a push run, or a workflow_dispatch run on exactly this commit (D45 condition 4, third text)
    assert '.head_sha == "\'"$COMMIT"\'" and (.event == "push" or .event == "workflow_dispatch")' in script
    assert '.name == "long-suites" and .conclusion == "success"' in script
    assert 'die "no successful Gates run on $COMMIT passed long-suites' in script
    assert script.index("LONG_OK") < script.index('tag -s "$TAG"')  # checked before anything is signed


# --- the release-day wrappers (scripts/operator/release-merge-and-sign.sh, merge-forward.sh, lib_release.sh) ---------
OPERATOR = ROOT / "scripts" / "operator"
LIB_RELEASE = OPERATOR / "lib_release.sh"
WRAPPERS = [OPERATOR / "release-merge-and-sign.sh", OPERATOR / "merge-forward.sh"]


def _clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}


def test_release_wrappers_stop_unless_run_in_privileged_mode(tmp_path):
    """Without -p, caller-exported functions and $BASH_ENV apply, so the wrappers do nothing outside privileged mode."""
    for w in WRAPPERS:
        r = subprocess.run(["bash", str(w)], cwd=tmp_path, env=_clean_env(), capture_output=True, text=True)
        assert r.returncode == 0 and "STOP: run as /bin/bash -p" in r.stderr and "nothing was done" in r.stderr, w


def test_release_wrappers_refuse_inside_an_agent_session(tmp_path):
    for w in WRAPPERS:
        r = subprocess.run(["/bin/bash", "-p", str(w)], cwd=tmp_path, env={**_clean_env(), "CLAUDECODE": "1"},
                           capture_output=True, text=True)
        assert r.returncode == 1 and "not an agent session" in r.stderr, w


def test_release_wrappers_share_the_tag_scripts_url_and_release_key():
    """lib_release.sh repeats tag-release.sh's fixed URL and pinned key (the signer runs as a sha256-pinned copy taken
    from the merge commit, so it can't source the library): the two must not drift apart."""
    lib, tag = LIB_RELEASE.read_text(), TAG_RELEASE.read_text()
    url = re.search(r'URL="(git@github\.com:[^"]+)"', tag).group(1)
    fp = re.search(r'RELEASE_FP="(SHA256:[^"]+)"', tag).group(1)
    assert f'URL="{url}"' in lib and f'RELEASE_FPS=("{fp}")' in lib


def test_release_scripts_check_the_name_reaches_the_public_repository():
    """After the rename the old name redirects to the private repository until the public one exists (runbook step 5);
    the wrappers and the signer refuse unless gh shows the public, unarchived repository."""
    expect = '"jlcatonjr/mathAgents public false"'
    assert expect in LIB_RELEASE.read_text() and expect in TAG_RELEASE.read_text()
    tag = TAG_RELEASE.read_text()
    assert tag.index("REPO_ID") < tag.index('tag -s "$TAG"')


def test_clean_reexec_allowlists_exactly_the_librarys_functions():
    """clean_reexec refuses any function it doesn't list, so a function added to the library must be listed too."""
    lib = LIB_RELEASE.read_text()
    defined = set(re.findall(r"^([a-z_]+)\(\) \{", lib, flags=re.M))
    listed = set(re.search(r"declare -f \(([a-z_|]+)\)", lib).group(1).split("|"))
    assert defined == listed, defined ^ listed


def test_release_merge_signs_only_with_the_signer_already_on_the_line():
    script = WRAPPERS[0].read_text()
    assert 'rev-parse "$MERGE:$sp"' in script and 'rev-parse "$PREV_HEAD:$sp"' in script
    assert '[[ "$got" == "$SIGNER_SHA256" ]]' in script
    assert script.index("SIGNER_SHA256\" ]]") < script.index('/bin/bash -p "$TMP/tag-release.sh"')
    assert '/bin/ln -s "$GH" "$GHDIR/gh"' in script  # tag-release.sh's D46 check needs gh on the signer's PATH


def test_no_interpreter_is_used_for_signing():
    """CA-154 (operator, 2026-11-06): the tag signer reads pyproject.toml with awk, so neither it nor the wrapper uses
    python or /opt/anaconda3 (release-policy §7: /opt/anaconda3 is not used for signing)."""
    for path in (TAG_RELEASE, *WRAPPERS, LIB_RELEASE):
        code = "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("#"))
        assert "python" not in code and "anaconda" not in code and "tomllib" not in code, path


def test_tag_release_reads_the_project_name_and_version_with_awk(tmp_path):
    """The awk reader takes [project]'s own name and version, not another table's, and prints nothing otherwise."""
    script = TAG_RELEASE.read_text()
    awk = re.search(r"/usr/bin/awk -v k=\"\$2\" '(.+)'$", script, flags=re.M).group(1)
    toml = '[build-system]\nname = "wrong"\n[project]\nname = "mathagents"\nversion = "1.1.0"  # c\n[tool.x]\nversion = "9"\n'
    def read(key, text=toml):
        return subprocess.run(["/usr/bin/awk", "-v", f"k={key}", awk], input=text, capture_output=True, text=True).stdout.strip()
    assert read("name") == "mathagents" and read("version") == "1.1.0"
    assert read("version", '[project]\nversion="1.1.0"\n') == ""  # another layout: nothing, so the checks refuse


def test_the_signers_awk_reads_pyproject_as_tomllib_does():
    """@security, 2026-11-06 (CA-154 follow-up): the awk readers (tag-release.sh project_field, lib_release.sh
    version_at) can disagree with TOML on crafted files (a key line inside a multi-line string; a repeated [project]).
    Gates runs this file on every push, so a release merge can't be tagged (tag-release.sh requires a successful
    Gates run on the commit) unless the awk reads the same [project] name and version that tomllib does."""
    import tomllib
    text = (ROOT / "pyproject.toml").read_text()
    project = tomllib.loads(text)["project"]
    tag_awk = re.search(r"/usr/bin/awk -v k=\"\$2\" '(.+)'$", TAG_RELEASE.read_text(), flags=re.M).group(1)
    lib_awk = re.search(r"pyproject\) \"\$\{GITX\[@\]\}\" show \"\$1:pyproject.toml\" \| awk '(.+)' ;;", LIB_RELEASE.read_text()).group(1)
    awk = "/usr/bin/awk" if Path("/usr/bin/awk").exists() else "awk"
    def run(prog, *args):
        return subprocess.run([awk, *args, prog], input=text, capture_output=True, text=True, check=True).stdout.strip()
    assert run(tag_awk, "-v", "k=name") == project["name"] == "mathagents"
    assert run(tag_awk, "-v", "k=version") == project["version"]
    assert run(lib_awk) == project["version"]
    assert text.count("\n[project]\n") + text.startswith("[project]\n") == 1  # one [project] table
