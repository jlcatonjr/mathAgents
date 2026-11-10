# Shared helpers for the gate test suites (source it; portable across BSD and GNU tools).
sedi() { sed "$1" "$2" > "$2.sedi" && mv "$2.sedi" "$2"; }  # in-place edit without GNU-only `sed -i`
