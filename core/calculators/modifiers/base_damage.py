from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.damage import DamageResult
from core.data_loader import loader


class BaseDamage:
    """Exact Base Damage step.
    Source lines (verbatim from repo):
    battle.c: wd.damage = battle_calc_base_damage2(sstatus, &sstatus->rhw, sc, tstatus->size, sd, i);
    battle.c: ATK_ADD2(wd.damage, sstatus->rhw.atk2);
    status.c: if (r) wa->atk2 = refine->get_bonus(wlv, r) / 100;"""

    @staticmethod
    def calculate(status: StatusData, weapon: Weapon, result: DamageResult) -> None:
        """Computes base damage and adds the step with full debug strings."""
        refine_bonus = loader.get_refine_bonus(weapon.level, weapon.refine)

        base_dmg = status.batk + weapon.atk + refine_bonus

        result.add_step(
            name="Base Damage",
            value=base_dmg,
            multiplier=1.0,
            note="Fixed portion only (variance added later in the exact Hercules order)",
            formula=f"status.batk + weapon.atk + get_refine_bonus({weapon.level}, {weapon.refine})",
            hercules_ref="battle.c: wd.damage = battle_calc_base_damage2(sstatus, &sstatus->rhw, sc, tstatus->size, sd, i);\n" +
                         "battle.c: ATK_ADD2(wd.damage, sstatus->rhw.atk2);\n" +
                         "status.c: if (r) wa->atk2 = refine->get_bonus(wlv, r) / 100;"
        )