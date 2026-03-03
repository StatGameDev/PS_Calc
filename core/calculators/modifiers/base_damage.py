from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.target import Target
from core.models.skill import SkillInstance
from core.models.damage import DamageRange, DamageResult
from core.data_loader import loader


class BaseDamage:
    """Exact port of battle_calc_base_damage2 — includes the internal SizeFix application
    (before batk is added) exactly as Hercules does it.
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
    #      range [1, overrefine]; computed by loader.get_overrefine(wlv, refine)
    #      status.c: wd->overrefine = refine->get_randombonus_max(wlv, r) / 100;
    #   3. Arrow ATK (bows):   rnd()%sd->bonus.arrow_atk           (out of scope, no bow model yet)
    # SizeFix is applied INSIDE this function before st->batk is added (battle.c lines 659-664).

    @staticmethod
    def calculate(status: StatusData,
                  weapon: Weapon,
                  build: PlayerBuild,
                  target: Target,
                  skill: SkillInstance,
                  result: DamageResult) -> DamageRange:
        """Computes the initial DamageRange, applies SizeFix internally before batk,
        and logs both the Size Fix and Base Damage steps."""
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
        # status.c: wd->overrefine = refine->get_randombonus_max(wlv, r) / 100;
        # Suppressed when weapon.refineable is False (item_db: Refine: false).
        if weapon.refineable:
            overrefine = loader.get_overrefine(weapon.level, weapon.refine)
            if overrefine > 0:
                or_avg = (overrefine + 1) // 2
                dmg = dmg.add_range(1, overrefine, or_avg)
        else:
            overrefine = 0

        # Size Fix — applied inside battle_calc_base_damage2 for PC, BEFORE batk is added.
        # battle.c lines 659-664:
        #   if (!(sd->special_state.no_sizefix || (flag&8)))
        #       damage = damage * sd->right_weapon.atkmods[t_size] / 100;
        if not build.no_sizefix and not skill.ignore_size_fix:
            size_mult = loader.get_size_fix_multiplier(weapon.weapon_type, target.size)
            dmg = dmg.scale(size_mult, 100)
        else:
            size_mult = 100

        result.add_step(
            name="Size Fix",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=size_mult / 100.0,
            note=f"{weapon.weapon_type} vs {target.size} target → {size_mult}% (applied before BATK)",
            formula=f"weapon_atk * {size_mult} // 100   (size_fix table[{target.size}][{weapon.weapon_type}])",
            hercules_ref="battle.c lines 659-664: inside battle_calc_base_damage2 (before st->batk is added)\n"
                         "if (!(sd->special_state.no_sizefix || (flag&8)))\n"
                         "    damage = damage * sd->right_weapon.atkmods[t_size] / 100;"
        )

        # batk is deterministic — added AFTER sizefix in Hercules
        dmg = dmg.add(status.batk)

        # Refine bonus is deterministic
        refine_bonus = loader.get_refine_bonus(weapon.level, weapon.refine)
        dmg = dmg.add(refine_bonus)

        overrefine_note = (f" + overrefine [1,{overrefine}] avg {(overrefine+1)//2}"
                           if overrefine > 0 else "")
        result.add_step(
            name="Base Damage",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=1.0,
            note=(f"Weapon ATK [{w_min},{w_max}] ×{size_mult}%"
                  + overrefine_note
                  + f" + BATK {status.batk} + Refine {refine_bonus}"),
            formula=(f"atkmin={atkmin} atkmax={atkmax} → [{w_min},{w_max}]*{size_mult}% "
                     f"+ batk {status.batk} + refine {refine_bonus}"),
            hercules_ref="battle.c: battle_calc_base_damage2 ~line 607\n"
                         "battle.c: damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;\n"
                         "battle.c: [size fix applied — lines 659-664]\n"
                         "battle.c: damage += st->batk;\n"
                         "battle.c: if (sd->right_weapon.overrefine) damage += rnd()%sd->right_weapon.overrefine+1;"
        )
        return dmg
