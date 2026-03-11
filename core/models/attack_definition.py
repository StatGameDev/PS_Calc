from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AttackDefinition:
    """One outcome type in the attack distribution used by DPS calculation.

    avg_damage : average damage of this outcome (0 for a miss).
    pre_delay  : ms of cast/startup time before the hit lands (0 for auto-attacks).
    post_delay : ms of after-delay before the next action (adelay).
    chance     : steady-state probability weight; must sum to 1.0 across the list
                 passed to calculate_dps().

    Future Markov extension:
        state_requirement: Optional[str] = None
        next_state:        Optional[str] = None
    """
    avg_damage: float
    pre_delay:  float   # ms
    post_delay: float   # ms
    chance:     float   # steady-state probability weight
