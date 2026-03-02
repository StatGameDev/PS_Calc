from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.damage import DamageRange, DamageResult
from core.data_loader import loader


class BaseDamage:
    """Exact Base Damage step — computes the initial DamageRange from weapon ATK variance.
    Source lines (verbatim from repo):
    battle.c: wd.damage = battle_calc_base_damage2(sstatus, &sstatus->rhw, sc, tstatus->size, sd, i);
    battle.c: ATK_ADD2(wd.damage, sstatus->rhw.atk2);
    status.c: if (r) wa->atk2 = refine->get_bonus(wlv, r) / 100;"""

    # Weapon ATK variance — confirmed in battle_calc_base_damage2 (battle.c ~line 650).
    # Three rnd() calls exist for PC attacks:
    #   1. Main weapon range:  rnd()%(atkmax-atkmin)+atkmin
    #      atkmax = wa->atk; atkmin = st->dex*(80+wlv*20)/100, capped to atkmax
    #      max roll = atkmax-1 (NOT atkmax) because rnd()%(n) gives [0, n-1]
    #   2. Overrefine bonus:   rnd()%sd->right_weapon.overrefine+1  (if overrefine > 0)
    #      range [1, overrefine]; TODO: populate weapon.overrefine once status.c logic is researched
    #   3. Arrow ATK (bows):   rnd()%sd->bonus.arrow_atk           (out of scope, no bow model yet)
    # FIXME: Hercules applies SizeFix inside battle_calc_base_damage2 (line ~663) before batk is
    # added. This pipeline applies SizeFix as a separate step after batk. Pre-existing architecture
    # mismatch — do not fix here.

    @staticmethod
    def calculate(status: StatusData,
                  weapon: Weapon,
                  build: PlayerBuild,
                  result: DamageResult) -> DamageRange:
        """Computes the initial DamageRange and logs the Base Damage step."""
        wlv = weapon.level                              # wa->wlv from inventory_data->wlv
        atkmax = weapon.atk                             # wa->atk

        # PC normal-attack atkmin: st->dex scaled by weapon level
        atkmin = status.dex * (80 + wlv * 20) // 100
        if atkmin > atkmax:
            atkmin = atkmax                             # cap — mirrors Hercules guard

        # SC_MAXIMIZEPOWER: collapses atkmin to atkmax (no weapon ATK variance)
        # battle.c: if (sc && sc->data[SC_MAXIMIZEPOWER]) atkmin = atkmax;
        if "SC_MAXIMIZEPOWER" in build.active_status_levels:
            atkmin = atkmax

        # Main weapon ATK range
        # battle.c: damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;
        # rnd()%(n) gives [0, n-1], so total roll is [atkmin, atkmax-1] when atkmax > atkmin
        if atkmax > atkmin:
            w_min = atkmin
            w_max = atkmax - 1          # ← atkmax-1, NOT atkmax
            w_avg = atkmin + (atkmax - atkmin - 1) // 2
        else:
            w_min = w_max = w_avg = atkmin

        dmg = DamageRange(w_min, w_max, w_avg)

        # Overrefine bonus: rnd()%overrefine+1 → range [1, overrefine]
        # battle.c: if (sd->right_weapon.overrefine) damage += rnd()%sd->right_weapon.overrefine+1;
        if weapon.overrefine > 0:
            or_avg = (weapon.overrefine + 1) // 2
            dmg = dmg.add_range(1, weapon.overrefine, or_avg)

        # batk is deterministic
        dmg = dmg.add(status.batk)

        # Refine bonus is deterministic
        refine_bonus = loader.get_refine_bonus(weapon.level, weapon.refine)
        dmg = dmg.add(refine_bonus)

        overrefine_note = (f" + overrefine [1,{weapon.overrefine}] avg {(weapon.overrefine+1)//2}"
                           if weapon.overrefine > 0 else "")
        result.add_step(
            name="Base Damage",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=1.0,
            note=(f"Weapon ATK [{w_min},{w_max}]"
                  + overrefine_note
                  + f" + BATK {status.batk} + Refine {refine_bonus}"),
            formula=(f"atkmin={atkmin} atkmax={atkmax} → range [{w_min},{w_max}], "
                     f"avg={w_avg}, +batk {status.batk}, +refine {refine_bonus}"),
            hercules_ref="battle.c: battle_calc_base_damage2 ~line 607\n"
                         "battle.c: damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;\n"
                         "battle.c: damage += st->batk;\n"
                         "battle.c: if (sd->right_weapon.overrefine) damage += rnd()%sd->right_weapon.overrefine+1;"
        )
        return dmg
