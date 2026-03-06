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

    # Hercules battle_calc_base_damage2 computation order for PC attacks:
    #   1. Weapon ATK range:   rnd() % (atkmax - atkmin) + atkmin  → [atkmin, atkmax-1]
    #      atkmax = wa->atk; atkmin = st->dex*(80+wlv*20)/100, capped to atkmax
    #   2. SizeFix:            damage * atkmods[t_size] / 100  (weapon ATK only)
    #   3. batk:               damage += st->batk
    #   4. Refine bonus:       damage += sd->right_weapon.atk2   (deterministic)
    #   5. Overrefine:         damage += rnd()%sd->right_weapon.overrefine+1  (if overrefine > 0)

    @staticmethod
    def calculate(status: StatusData,
                  weapon: Weapon,
                  build: PlayerBuild,
                  target: Target,
                  skill: SkillInstance,
                  result: DamageResult,
                  is_crit: bool = False) -> DamageRange:
        """Computes the initial DamageRange, applies SizeFix internally before batk,
        and logs Weapon ATK Range, Size Fix, and Base Damage steps.

        is_crit=True forces damage = atkmax (battle.c:648-651, flag&1 path):
            if (!(flag&1))
                damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;
            else
                damage = atkmax;
        Overrefine still randomizes on crit (no flag&1 guard on that block).
        """
        wlv = weapon.level                              # wa->wlv from inventory_data->wlv
        atkmax = weapon.atk                             # wa->atk

        # SC_IMPOSITIO: flat weapon ATK bonus per level (val2 = level * 5)
        # status.c #ifndef RENEWAL ~line 4562: watk += sc->data[SC_IMPOSITIO]->val2
        imp_lv = build.active_status_levels.get("SC_IMPOSITIO", 0)
        if imp_lv:
            atkmax += imp_lv * 5
            result.add_step(
                name="SC_IMPOSITIO",
                value=imp_lv * 5,
                note=f"SC_IMPOSITIO Lv{imp_lv}: +{imp_lv * 5} weapon ATK",
                formula=f"level * 5 = {imp_lv} * 5 = {imp_lv * 5}",
                hercules_ref="status.c #ifndef RENEWAL ~line 4562: watk += sc->data[SC_IMPOSITIO]->val2",
            )

        # Arrow ATK: bow-type weapons add ammo ATK to weapon ATK
        # battle.c: sd->arrow_atk contributes to weapon ATK for arrow attacks
        if weapon.weapon_type == "Bow":
            ammo_id = build.equipped.get("ammo")
            if ammo_id is not None:
                ammo = loader.get_item(ammo_id)
                if ammo and ammo.get("type") == "IT_AMMO":
                    arrow_atk = ammo.get("atk", 0)
                    if arrow_atk:
                        atkmax += arrow_atk
                        result.add_step(
                            name="Arrow ATK",
                            value=arrow_atk,
                            note=f"Ammo ID {ammo_id}: +{arrow_atk} ATK added to weapon ATK",
                            formula=f"atkmax += ammo.atk = {arrow_atk}",
                            hercules_ref="battle.c: sd->arrow_atk contributes to weapon ATK for bow attacks",
                        )

        # PC normal-attack atkmin: st->dex scaled by weapon level
        # battle.c:635: atkmin = atkmin*(80 + wlv*20)/100  (verified A7 — correct)
        atkmin = status.dex * (80 + wlv * 20) // 100
        if atkmin > atkmax:
            atkmin = atkmax                             # cap — mirrors Hercules guard

        # SC_MAXIMIZEPOWER: collapses atkmin to atkmax (no weapon ATK variance)
        # battle.c: if (sc && sc->data[SC_MAXIMIZEPOWER]) atkmin = atkmax;
        maximize_active = "SC_MAXIMIZEPOWER" in build.active_status_levels
        if maximize_active:
            atkmin = atkmax

        # Main weapon ATK range
        # Normal: rnd()%(atkmax-atkmin) + atkmin → [atkmin, atkmax-1]
        # Crit (flag&1): damage = atkmax  (no roll, always max)
        if is_crit:
            w_min = w_max = w_avg = atkmax
        elif atkmax > atkmin:
            w_min = atkmin
            w_max = atkmax - 1          # ← atkmax-1, NOT atkmax
            w_avg = atkmin + (atkmax - atkmin - 1) // 2
        else:
            w_min = w_max = w_avg = atkmin

        # Step: Weapon ATK Range — value immediately before SizeFix is applied
        crit_note = "  (CRIT: forced to atkmax — no roll)" if is_crit else ""
        maximize_note = "  (SC_MAXIMIZEPOWER: collapsed to atkmax)" if maximize_active else ""
        result.add_step(
            name="Weapon ATK Range",
            value=w_avg,
            min_value=w_min,
            max_value=w_max,
            note=f"atkmin={atkmin}  atkmax={atkmax}{crit_note}{maximize_note}",
            formula=(f"CRIT: damage = atkmax = {atkmax}" if is_crit
                     else f"atkmin = dex*{80+wlv*20}//100 = {atkmin};  range = [atkmin, atkmax-1]"),
            hercules_ref=("battle.c battle_calc_base_damage2 ~line 648: if(flag&1) damage = atkmax;"
                          if is_crit else
                          "battle.c battle_calc_base_damage2 ~line 652:\n"
                          "damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;")
        )

        dmg = DamageRange(w_min, w_max, w_avg)

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

        # Overrefine bonus: rnd()%overrefine+1 → range [1, overrefine]
        # Added LAST in battle_calc_base_damage2 — after sizefix and batk.
        # NOTE: atk2 (deterministic refine bonus) is NOT part of battle_calc_base_damage2.
        # It is added in battle_calc_weapon_attack AFTER defense (lines 5803-5805).
        # It is handled by RefineFix in the pipeline.
        # battle.c: if (sd->right_weapon.overrefine) damage += rnd()%sd->right_weapon.overrefine+1;
        # status.c: wd->overrefine = refine->get_randombonus_max(wlv, r) / 100;
        # Suppressed when weapon.refineable is False (item_db: Refine: false).
        if weapon.refineable:
            overrefine = loader.get_overrefine(weapon.level, weapon.refine)
            if overrefine > 0:
                or_avg = (overrefine + 1) // 2
                dmg = dmg.add_range(1, overrefine, or_avg)
                result.add_step(
                    name="Overrefine Bonus",
                    value=or_avg,
                    min_value=1,
                    max_value=overrefine,
                    note=f"Stochastic: rnd()%{overrefine}+1 → [1,{overrefine}]  avg≈{or_avg}",
                    formula=f"rnd()%{overrefine}+1",
                    hercules_ref="battle.c battle_calc_base_damage2:\n"
                                 "if (sd->right_weapon.overrefine)\n"
                                 "    damage += rnd()%sd->right_weapon.overrefine+1;\n"
                                 "status.c: wd->overrefine = refine->get_randombonus_max(wlv, r) / 100;",
                )
            else:
                result.add_step(
                    name="Overrefine Bonus",
                    value=0,
                    note="No overrefine (refine too low for random bonus)",
                    formula="0",
                    hercules_ref="battle.c: overrefine block skipped (sd->right_weapon.overrefine == 0)",
                )
        else:
            overrefine = 0
            result.add_step(
                name="Overrefine Bonus",
                value=0,
                note="Suppressed — weapon is not refineable (item_db Refine: false)",
                formula="0",
                hercules_ref="battle.c: overrefine block skipped (weapon not refineable)",
            )

        result.add_step(
            name="Base Damage",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=1.0,
            note=(f"Weapon ATK [{w_min},{w_max}] ×{size_mult}%"
                  f" + BATK {status.batk}"
                  + (f" + Overrefine [1,{overrefine}]" if overrefine > 0 else "")),
            formula=(f"atkmin={atkmin} atkmax={atkmax} → [{w_min},{w_max}]*{size_mult}% "
                     f"+ batk {status.batk}"
                     + (f" + rnd()%{overrefine}+1" if overrefine > 0 else "")),
            hercules_ref="battle.c: battle_calc_base_damage2 ~line 607\n"
                         "battle.c: damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;\n"
                         "battle.c: [size fix applied — lines 659-664]\n"
                         "battle.c: damage += st->batk;\n"
                         "battle.c: if (sd->right_weapon.overrefine) damage += rnd()%sd->right_weapon.overrefine+1;"
        )
        return dmg
