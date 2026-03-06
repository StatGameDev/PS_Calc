from core.models.target import Target
from core.models.damage import DamageRange, DamageResult
from core.models.build import PlayerBuild
from core.models.gear_bonuses import GearBonuses
from core.config import BattleConfig

_RACE_TO_RC = {
    "Formless":  "RC_Formless",
    "Undead":    "RC_Undead",
    "Brute":     "RC_Brute",
    "Plant":     "RC_Plant",
    "Insect":    "RC_Insect",
    "Fish":      "RC_Fish",
    "Demon":     "RC_Demon",
    "Demi-Human": "RC_DemiHuman",
    "Angel":     "RC_Angel",
    "Dragon":    "RC_Dragon",
}


class DefenseFix:
    """Exact pre-renewal defense reduction for BF_WEAPON attacks.
    Hard DEF percentage applied first, then soft VIT DEF subtracted.
    Both hard DEF (percentage) and soft DEF (VIT) carry their own variance:
      - Hard DEF is deterministic (percentage of current damage).
      - Soft DEF has a random range; independent of weapon ATK variance so the
        subtraction is crossed: min output = min weapon dmg - max VIT DEF,
        max output = max weapon dmg - min VIT DEF.
    Source: battle.c battle_calc_defense, pre-renewal path (~line 1397)."""

    @staticmethod
    def calculate(target: Target, build: PlayerBuild, gear_bonuses: GearBonuses,
                  dmg: DamageRange, config: BattleConfig, result: DamageResult,
                  is_crit: bool = False) -> DamageRange:
        """VIT penalty applied to def1/def2 before reduction (exact source position).

        On crit, flag.idef = flag.idef2 = 1 (battle.c:4988-4989, #ifndef RENEWAL),
        which makes the defense condition (!flag.idef || !flag.idef2) = false,
        so calc_defense is entirely skipped. DEF values remain available to read
        but neither percentage nor VIT reduction is applied.
        """
        if is_crit:
            result.add_step(
                name="Defense Fix",
                value=dmg.avg,
                min_value=dmg.min,
                max_value=dmg.max,
                multiplier=1.0,
                note=f"BYPASSED — crit sets flag.idef=flag.idef2=1 (DEF {target.def_}, VIT {target.vit} readable but not applied)",
                formula="no change (defense skipped on crit)",
                hercules_ref="battle.c:4988-4989 (#ifndef RENEWAL):\n"
                             "flag.idef = flag.idef2 = flag.hit = 1;\n"
                             "Then: if((!flag.idef || !flag.idef2)) → false → calc_defense not called.",
            )
            return dmg

        def1 = max(0, min(100, target.def_))

        # G5 ignore_def: cards like Thanatos bypass a % of hard DEF
        race_rc = _RACE_TO_RC.get(target.race, "")
        boss_rc = "RC_Boss" if target.is_boss else "RC_NonBoss"
        ignore_pct = (gear_bonuses.ignore_def_rate.get(race_rc, 0)
                      + gear_bonuses.ignore_def_rate.get(boss_rc, 0))
        if getattr(build, "ignore_hard_def", False) or ignore_pct >= 100:
            def1 = 0
            note_def = "Hard DEF ignored (100%)"
        elif ignore_pct > 0:
            def1 = max(0, def1 * (100 - ignore_pct) // 100)
            note_def = f"Hard DEF {target.def_} → {def1} (−{ignore_pct}% ignored)"
        else:
            note_def = f"Hard DEF {def1}"

        def2 = max(1, target.vit)

        # VIT penalty (full mechanic – uses target.targeted_count, respects bitmask)
        if config.vit_penalty_type != 0 and (config.vit_penalty_target & (1 if target.is_pc else 2)) != 0:
            target_count = target.targeted_count
            if target_count >= config.vit_penalty_count:
                if getattr(target, 'active_status_levels', {}).get("SC_STEELBODY", 0) == 0:
                    penalty = (target_count - (config.vit_penalty_count - 1)) * config.vit_penalty_num
                    if config.vit_penalty_type == 1:
                        def1 = def1 * (100 - penalty) // 100
                        def2 = def2 * (100 - penalty) // 100
                    else:
                        def1 -= penalty
                        def2 -= penalty

        # Hard DEF: deterministic percentage — applies uniformly to min/max/avg
        # battle.c: damage = damage * (100-def1) / 100;
        dmg = dmg.scale(100 - def1, 100)

        # Soft VIT DEF: random range — crossed subtraction with weapon ATK variance
        # Weapon ATK variance and VIT DEF variance are independent, so:
        #   worst case (min output) = min weapon damage − max VIT DEF roll
        #   best case  (max output) = max weapon damage − min VIT DEF roll
        if target.is_pc:
            # battle.c: vit_def = def2*(def2-15)/150;
            # battle.c: vit_def = def2/2 + (vit_def>0 ? rnd()%vit_def : 0);
            # rnd()%n gives [0, n-1], so range is [def2/2, def2/2 + variance_max-1]
            variance_max = def2 * (def2 - 15) // 150
            vd_min = def2 // 2
            vd_max = def2 // 2 + (variance_max - 1 if variance_max > 0 else 0)
            # avg of rnd()%n is (n-1)/2; n//2 rounds half-up (C1a fix)
            vd_avg = def2 // 2 + (variance_max // 2 if variance_max > 0 else 0)
            note_type = "PC"
        else:
            # battle.c: vit_def = (def2/20)*(def2/20);
            # battle.c: vit_def = def2 + (vit_def>0 ? rnd()%vit_def : 0);
            # rnd()%n gives [0, n-1], so range is [def2, def2 + variance_max-1]
            variance_max = (def2 // 20) * (def2 // 20)
            vd_min = def2
            vd_max = def2 + (variance_max - 1 if variance_max > 0 else 0)
            # avg of rnd()%n is (n-1)/2; n//2 rounds half-up (C1a fix)
            vd_avg = def2 + (variance_max // 2 if variance_max > 0 else 0)
            note_type = "monster"

        # DamageRange.subtract() applies the crossing:
        #   result.min = self.min - vd_max   (worst case for attacker)
        #   result.max = self.max - vd_min   (best case for attacker)
        dmg = dmg.subtract(vd_min, vd_max, vd_avg)
        dmg = dmg.floor_at(1)

        result.add_step(
            name="Defense Fix",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=1.0,
            note=f"{note_def} → ×{(100-def1)/100:.0%} + Soft DEF [{vd_min},{vd_max}] avg {vd_avg} ({note_type})",
            formula=f"max(1, dmg * (100 - def1) // 100 - vit_def_range [{vd_min},{vd_max}])",
            hercules_ref="battle.c: defType def1 = status_get_def(target); short def2 = tstatus->def2, vit_def;\n"
                         "battle.c: if (def1 > 100) def1 = 100;\n"
                         "battle.c: damage = damage * (100-def1) / 100;\n"
                         "battle.c: if (!(flag & 1 || flag & 2)) damage -= vit_def;\n"
                         "battle.c: if (tsd) { vit_def = def2*(def2-15)/150; vit_def = def2/2 + (vit_def>0 ? rnd()%vit_def : 0); }\n"
                         "battle.c: else { vit_def = (def2/20)*(def2/20); vit_def = def2 + (vit_def>0 ? rnd()%vit_def : 0); }"
        )
        return dmg
