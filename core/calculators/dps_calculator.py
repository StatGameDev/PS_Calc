from __future__ import annotations

from abc import ABC, abstractmethod

from core.models.attack_definition import AttackDefinition


class SelectionStrategy(ABC):
    @abstractmethod
    def compute_weights(self, attacks: list[AttackDefinition]) -> list[AttackDefinition]:
        """Return attacks with chance values representing steady-state probability.

        Future Markov extension: replace with eigenvector solution over the state graph.
        """
        ...


class FormulaSelectionStrategy(SelectionStrategy):
    """Stateless: AttackDefinition.chance values are already the steady-state weights.

    Replace with MarkovSelectionStrategy when turn-sequence modelling is added.
    """

    def compute_weights(self, attacks: list[AttackDefinition]) -> list[AttackDefinition]:
        return attacks


def calculate_dps(attacks: list[AttackDefinition],
                  strategy: SelectionStrategy) -> float:
    """Return damage per second.

    Correct formula: Σ(chance_i × damage_i) / Σ(chance_i × (pre_i + post_i)).

    Do NOT use Σ(chance_i × dps_i) — that is incorrect when delays differ between
    attack types because it weights each dps_i by its own chance rather than by the
    fraction of time it consumes.

    Returns 0.0 if total weighted time is zero (prevents division by zero).
    """
    weighted = strategy.compute_weights(attacks)
    total_dmg  = sum(a.chance * a.avg_damage                for a in weighted)
    total_time = sum(a.chance * (a.pre_delay + a.post_delay) for a in weighted)
    if total_time == 0:
        return 0.0
    return total_dmg / total_time * 1000   # ms → per-second
