import Mathlib.Algebra.Ring.Int.Defs

namespace MathAgents.P4ThirtyDividesN5MinusN

/-- Reading R1: for every integer `n`, `30 ∣ n ^ 5 - n`, computed in `ℤ`. -/
theorem thirty_dvd_pow_five_sub_self_int_R1 :
    ∀ n : ℤ, (30 : ℤ) ∣ n ^ 5 - n := sorry

/-- Reading R2: for every natural number `n`, `30 ∣ n ^ 5 - n`, computed in `ℕ`
(truncated subtraction). -/
theorem thirty_dvd_pow_five_sub_self_nat_R2 :
    ∀ n : ℕ, (30 : ℕ) ∣ n ^ 5 - n := sorry

end MathAgents.P4ThirtyDividesN5MinusN
