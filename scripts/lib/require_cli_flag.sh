#!/usr/bin/env bash
# Require that a command's --help lists a flag (a capability check before refresh_agent_surfaces.sh renders).
#
#   require_cli_flag.sh FLAG COMMAND [ARGS...]     e.g. require_cli_flag.sh --discard-user-regions agentteams
#
# The help text is captured before it is searched: piping into `grep -q` under `set -o pipefail` can fail
# spuriously when grep exits at its first match and the command dies of SIGPIPE while still printing.
# Exit 0 = the flag is listed; 1 = the command runs but does not list it; 127 = the command is not installed.
set -uo pipefail
flag=$1; shift
command -v "$1" >/dev/null 2>&1 || { echo "require_cli_flag: $1 is not installed" >&2; exit 127; }
help=$("$@" --help 2>&1) || true
grep -q -- "$flag" <<<"$help" || { echo "require_cli_flag: '$*' does not list $flag" >&2; exit 1; }
