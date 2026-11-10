# MathAgentsWIP: open work

Theorem stubs from pipeline Stage 1 (`:= sorry`) and partial proofs live here. G-KERNEL tolerates
`sorry`/`admit`/`stop` in this library as *open markers* and reports each declaration as `open`.
Every other check stays fatal. `MathAgents` (the proved library) must never import this library.
Move a result into `MathAgents` once it is proved. See `docs/kernel-gate.md`.

This README also keeps the directory tracked by git: without it, fresh clones lack
`lean/MathAgentsWIP/`, and the `MathAgentsWIP.+` glob fails the build.
