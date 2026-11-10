import Mathlib.Data.Nat.GCD.Basic
import Mathlib.Tactic.Ring

/-!
# Toolchain smoke test

Confirms the pinned Lean + Mathlib pair builds and that the G-KERNEL axiom audit sees a
Mathlib-dependent declaration. Not a research result.
-/

namespace MathAgents.Smoke

theorem two_mul_eq_add (n : ℕ) : 2 * n = n + n := by ring

theorem gcd_succ_self (n : ℕ) : Nat.gcd (n + 1) n = 1 := by
  simp [Nat.gcd_comm]

end MathAgents.Smoke
