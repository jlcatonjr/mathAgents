"""mathagents: the Python API of the mathAgents proof-development harness.

One public module per capability (see docs/api-reference/). The package re-exports nothing: import
from the module, e.g. ``from mathagents.dossiers import validate_dossiers``.
"""
from __future__ import annotations

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("mathagents")
except PackageNotFoundError:  # running from a checkout that is not installed
    __version__ = "0.0.0+local"
