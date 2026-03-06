from core.models.build import PlayerBuild
from core.models.gear_bonuses import GearBonuses
from core.models.weapon import Weapon
from core.models.target import Target
from core.models.damage import DamageRange, DamageResult

# Map target.race display names → RC_* keys used in GearBonuses dicts
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

# Map target.element int → Ele_* keys
_ELE_TO_KEY = {
    0: "Ele_Neutral", 1: "Ele_Water",  2: "Ele_Earth", 3: "Ele_Fire",
    4: "Ele_Wind",    5: "Ele_Poison", 6: "Ele_Holy",  7: "Ele_Dark",
    8: "Ele_Ghost",   9: "Ele_Undead",
}

# Map target.size display names → Size_* keys
_SIZE_TO_KEY = {
    "Small":  "Size_Small",
    "Medium": "Size_Medium",
    "Large":  "Size_Large",
}


class CardFix:
    """Card and equipment bonus multipliers applied after AttrFix.

    Attacker side: race/element/size damage bonuses from equipped cards/gear.
    Target side (is_pc=True only): sub_ele/sub_size/sub_race resist from
    target's own equipped cards (populated when PvP is wired in Session D).

    Sources: battle.c battle_calc_weapon_attack, bAddRace/bAddEle/bAddSize
    bonus application; bSubEle/bSubRace/bSubSize for PC target reduction.
    G11: bLongAtkRate applied here for ranged attacks only.
    """

    @staticmethod
    def calculate(build: PlayerBuild,
                  gear_bonuses: GearBonuses,
                  weapon: Weapon,
                  target: Target,
                  is_ranged: bool,
                  dmg: DamageRange,
                  result: DamageResult) -> DamageRange:

        # --- Attacker-side bonuses ---
        race_rc  = _RACE_TO_RC.get(target.race, "")
        boss_rc  = "RC_Boss" if target.is_boss else "RC_NonBoss"
        ele_key  = _ELE_TO_KEY.get(target.element, "")
        size_key = _SIZE_TO_KEY.get(target.size, "")

        add_race = gear_bonuses.add_race
        add_ele  = gear_bonuses.add_ele
        add_size = gear_bonuses.add_size

        atk_bonus = (
            add_race.get(race_rc, 0)
            + add_race.get(boss_rc, 0)
            + add_race.get("RC_All", 0)
            + add_ele.get(ele_key, 0)
            + add_ele.get("Ele_All", 0)
            + add_size.get(size_key, 0)
            + add_size.get("Size_All", 0)
            + gear_bonuses.atk_rate                        # bAtkRate flat %
            + (gear_bonuses.long_atk_rate if is_ranged else 0)  # G11
        )

        # --- Target-side reductions (PvP only — all dicts empty for mob targets) ---
        def_pct = 0
        if target.is_pc:
            weapon_ele_key = _ELE_TO_KEY.get(weapon.element, "Ele_Neutral")
            def_pct = (
                target.sub_ele.get(weapon_ele_key, 0)
                + target.sub_ele.get("Ele_All", 0)
                + target.sub_size.get("Size_Medium", 0)   # player attacker = Medium
                + target.sub_race.get("RC_DemiHuman", 0)  # player attacker = Demi-Human
                + (target.long_attack_def_rate if is_ranged else target.near_attack_def_rate)
            )

        net = 100 + atk_bonus - def_pct
        if net != 100:
            dmg = dmg.scale(net, 100)

        result.add_step(
            name="Card Fix",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=net / 100.0,
            note=(f"Race {race_rc}+{add_race.get(race_rc,0)}%"
                  f"  {'Boss' if target.is_boss else 'NonBoss'}+{add_race.get(boss_rc,0)}%"
                  f"  Ele+{add_ele.get(ele_key,0)}%"
                  f"  Size+{add_size.get(size_key,0)}%"
                  f"  AtkRate+{gear_bonuses.atk_rate}%"
                  + (f"  LongAtk+{gear_bonuses.long_atk_rate}%" if is_ranged else "")
                  + (f"  TargetDef-{def_pct}%" if def_pct else "")),
            formula=f"dmg * (100 + {atk_bonus} - {def_pct}) // 100 = dmg * {net} // 100",
            hercules_ref="battle.c: bAddRace/bAddEle/bAddSize bonuses; bLongAtkRate for ranged (G11)",
        )

        return dmg

    @staticmethod
    def calculate_magic(target: Target, magic_ele_name: str,
                        dmg: DamageRange, result: DamageResult) -> DamageRange:
        """BF_MAGIC target-side CardFix (player target only).

        Attacker-side magic bonuses (bAddRace for magic etc.) are #ifdef RENEWAL — skip.
        Target side (is_pc=True only): sub_ele, sub_race (RC_DemiHuman), magic_def_rate.
        Source: pipeline_specs.md BF_MAGIC Outgoing spec.
        """
        if not target.is_pc:
            result.add_step(
                name="Card Fix (Magic)",
                value=dmg.avg, min_value=dmg.min, max_value=dmg.max,
                multiplier=1.0,
                note="target is mob — no magic card resist",
                formula="no change",
                hercules_ref="magic_addrace etc. are #ifdef RENEWAL; target-side only for is_pc",
            )
            return dmg

        # Target-side: sub_ele (magic element), sub_race (attacker=DemiHuman), magic_def_rate
        def_pct = (
            target.sub_ele.get(magic_ele_name, 0)
            + target.sub_ele.get("Ele_All", 0)
            + target.sub_race.get("RC_DemiHuman", 0)   # player attacker race = DemiHuman
            + target.magic_def_rate                     # bMagicDefRate
        )

        net = 100 - def_pct
        if net != 100:
            dmg = dmg.scale(net, 100)

        result.add_step(
            name="Card Fix (Magic)",
            value=dmg.avg, min_value=dmg.min, max_value=dmg.max,
            multiplier=net / 100.0,
            note=(f"Ele({magic_ele_name})-{target.sub_ele.get(magic_ele_name,0)}%"
                  f"  Race(DemiHuman)-{target.sub_race.get('RC_DemiHuman',0)}%"
                  f"  MagicDef-{target.magic_def_rate}%"),
            formula=f"dmg * (100 - {def_pct}) // 100 = dmg * {net} // 100",
            hercules_ref="pipeline_specs.md BF_MAGIC: target-side sub_ele/sub_race/magic_def_rate (is_pc only)",
        )
        return dmg
