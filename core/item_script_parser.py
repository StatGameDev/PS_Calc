"""
D5 — Item script parser.
Parses Hercules AtCommands-style scripts: bonus/bonus2/bonus3 calls.

Only bonus types relevant to the damage calculator or tooltips are handled.
Unknown types produce an ItemEffect with description="[{bonus_type} effect]".

Source: Hercules/src/map/script.c (bonus registration table)
"""
from __future__ import annotations

import re
from typing import Optional

from core.models.item_effect import ItemEffect

# ---------------------------------------------------------------------------
# Constants for known enum string values
# ---------------------------------------------------------------------------

_RACE_NAMES: dict[str, str] = {
    "RC_Formless": "Formless", "RC_Undead": "Undead", "RC_Brute": "Brute",
    "RC_Plant": "Plant", "RC_Insect": "Insect", "RC_Fish": "Fish",
    "RC_Demon": "Demon", "RC_DemiHuman": "Demi-Human", "RC_Angel": "Angel",
    "RC_Dragon": "Dragon", "RC_Boss": "Boss monsters",
    "RC_NonBoss": "Normal monsters", "RC_All": "all races",
}

_ELEMENT_NAMES: dict[str, str] = {
    "Ele_Neutral": "Neutral", "Ele_Water": "Water", "Ele_Earth": "Earth",
    "Ele_Fire": "Fire", "Ele_Wind": "Wind", "Ele_Poison": "Poison",
    "Ele_Holy": "Holy", "Ele_Dark": "Dark", "Ele_Ghost": "Ghost",
    "Ele_Undead": "Undead", "Ele_All": "all elements",
}

_SIZE_NAMES: dict[str, str] = {
    "Size_Small": "Small", "Size_Medium": "Medium", "Size_Large": "Large",
    "Size_All": "all sizes",
}

# Status effect IDs → readable name (subset; full list in status.h)
_STATUS_NAMES: dict[str, str] = {
    "SC_POISON": "Poison", "SC_SILENCE": "Silence", "SC_BLIND": "Blind",
    "SC_SLEEP": "Sleep", "SC_STUN": "Stun", "SC_CURSE": "Curse",
    "SC_FREEZE": "Freeze", "SC_STONE": "Stone", "SC_BLEEDING": "Bleeding",
    "SC_CONFUSION": "Confusion",
}

# Class_* values used in bSubClass / bAddDamageClass
_CLASS_NAMES: dict[str, str] = {
    "Class_Normal": "Normal monsters", "Class_Boss": "Boss monsters",
    "Class_Guardian": "Guardians", "Class_All": "all monster types",
}

# ---------------------------------------------------------------------------
# Description templates
# ---------------------------------------------------------------------------
# bonus (arity 1): bonus_type → lambda(param) → str
# bonus2 (arity 2): bonus_type → lambda(p1, p2) → str
# bonus3 (arity 3): bonus_type → lambda(p1, p2, p3) → str

def _stat_desc(stat_name: str):
    return lambda v: f"STR +{v}." if v > 0 else f"{stat_name} {v}."

_BONUS1_TEMPLATES: dict[str, object] = {
    "bStr":    lambda v: f"STR +{v}." if v > 0 else f"STR {v}.",
    "bAgi":    lambda v: f"AGI +{v}." if v > 0 else f"AGI {v}.",
    "bVit":    lambda v: f"VIT +{v}." if v > 0 else f"VIT {v}.",
    "bInt":    lambda v: f"INT +{v}." if v > 0 else f"INT {v}.",
    "bDex":    lambda v: f"DEX +{v}." if v > 0 else f"DEX {v}.",
    "bLuk":    lambda v: f"LUK +{v}." if v > 0 else f"LUK {v}.",
    "bAllStats": lambda v: f"All Stats +{v}." if v > 0 else f"All Stats {v}.",
    "bBaseAtk": lambda v: f"ATK +{v}." if v > 0 else f"ATK {v}.",
    "bMatk":   lambda v: f"MATK +{v}." if v > 0 else f"MATK {v}.",
    "bHit":    lambda v: f"HIT +{v}." if v > 0 else f"HIT {v}.",
    "bFlee":   lambda v: f"FLEE +{v}." if v > 0 else f"FLEE {v}.",
    "bFlee2":  lambda v: f"Perfect Dodge +{v}." if v > 0 else f"Perfect Dodge {v}.",
    "bCritical": lambda v: f"CRIT +{v}." if v > 0 else f"CRIT {v}.",
    "bCritAtkRate": lambda v: f"Critical damage +{v}%." if v > 0 else f"Critical damage {v}%.",
    "bMaxHP":  lambda v: f"MaxHP +{v}." if v > 0 else f"MaxHP {v}.",
    "bMaxSP":  lambda v: f"MaxSP +{v}." if v > 0 else f"MaxSP {v}.",
    "bMaxHPrate": lambda v: f"MaxHP +{v}%." if v > 0 else f"MaxHP {v}%.",
    "bMaxSPrate": lambda v: f"MaxSP +{v}%." if v > 0 else f"MaxSP {v}%.",
    "bDef":    lambda v: f"DEF +{v}." if v > 0 else f"DEF {v}.",
    "bMdef":   lambda v: f"MDEF +{v}." if v > 0 else f"MDEF {v}.",
    "bAspdRate": lambda v: f"ASPD +{v}%." if v > 0 else f"ASPD {v}%.",
    "bAspd":   lambda v: f"ASPD +{v} (flat)." if v > 0 else f"ASPD {v} (flat).",
    "bMatkRate": lambda v: f"MATK +{v}%." if v > 0 else f"MATK {v}%.",
    "bLongAtkRate": lambda v: f"Long-range damage +{v}%." if v > 0 else f"Long-range damage {v}%.",
    "bShortWeaponDamageReturn": lambda v: f"Reflects {v}% melee physical damage back to attacker.",
    "bCastrate": lambda v: f"Casting time {'reduced' if v < 0 else 'increased'} by {abs(v)}%.",
    "bDelayrate": lambda v: f"After-cast delay {'reduced' if v < 0 else 'increased'} by {abs(v)}%.",
    "bHPrecovRate": lambda v: f"Natural HP recovery +{v}%." if v > 0 else f"Natural HP recovery {v}%.",
    "bSPrecovRate": lambda v: f"Natural SP recovery +{v}%." if v > 0 else f"Natural SP recovery {v}%.",
    "bUseSPrate": lambda v: f"SP consumption {'reduced' if v < 0 else 'increased'} by {abs(v)}%.",
    "bHealPower": lambda v: f"Heal effectiveness +{v}%.",
    "bSpeedRate": lambda v: f"Movement speed +{v}%." if v > 0 else f"Movement speed {v}%.",
    "bSplashRange": lambda v: f"Attack splash range +{v} cells.",
    "bSPDrainValue": lambda v: f"Drains {v} SP per physical hit.",
    "bBreakArmorRate": lambda v: f"{v/100:.0f}% chance to break the target's armor per hit.",
    "bBreakWeaponRate": lambda v: f"{v/100:.0f}% chance to break the target's weapon per hit.",
    "bDefEle":  lambda v: f"Changes armor element to {_ELEMENT_NAMES.get(str(v), str(v))}.",
    "bAtkEle":  lambda v: f"Changes weapon element to {_ELEMENT_NAMES.get(str(v), str(v))}.",
    "bUnbreakableWeapon": lambda _v: "Weapon cannot be broken.",
    "bUnbreakableHelm": lambda _v: "Headgear cannot be broken.",
    "bIgnoreDefRace": lambda v: f"Ignores DEF of {_RACE_NAMES.get(str(v), str(v))}.",
    "bNearAtkDef":   lambda v: f"Near-range damage resistance +{v}%.",
    "bLongAtkDef":   lambda v: f"Long-range damage resistance +{v}%.",
    "bMagicDefRate": lambda v: f"Magic damage reduction +{v}%.",
    "bAtkRate":      lambda v: f"Physical ATK +{v}%.",
}

def _race(v: str) -> str:
    return _RACE_NAMES.get(v, v)

def _ele(v: str) -> str:
    return _ELEMENT_NAMES.get(v, v)

def _size(v: str) -> str:
    return _SIZE_NAMES.get(v, v)

def _cls(v: str) -> str:
    return _CLASS_NAMES.get(v, v)

_BONUS2_TEMPLATES: dict[str, object] = {
    "bAddRace":     lambda r, v: f"Increases physical damage against {_race(r)} by {v}%.",
    "bSubEle":      lambda e, v: f"Reduces damage from {_ele(e)}-element attacks by {v}%." if v > 0 else f"Increases damage from {_ele(e)}-element attacks by {abs(v)}%.",
    "bSubRace":     lambda r, v: f"Reduces damage from {_race(r)} by {v}%." if v > 0 else f"Increases damage from {_race(r)} by {abs(v)}%.",
    "bAddSize":     lambda s, v: f"Increases physical damage against {_size(s)} monsters by {v}%.",
    "bSubSize":     lambda s, v: f"Reduces damage from {_size(s)} monsters by {v}%.",
    "bAddEle":      lambda e, v: f"Increases physical damage against {_ele(e)}-element monsters by {v}%.",
    "bMagicAddRace": lambda r, v: f"Increases magic damage against {_race(r)} by {v}%.",
    "bIgnoreDefRate": lambda r, v: f"Ignores {v}% of {_race(r)} DEF.",
    "bIgnoreMdefRate": lambda r, v: f"Ignores {v}% of {_race(r)} MDEF.",
    "bCriticalAddRace": lambda r, v: f"CRIT rate +{v} against {_race(r)}.",
    "bExpAddRace":  lambda r, v: f"EXP gain +{v}% from {_race(r)}.",
    "bResEff":      lambda sc, v: f"Increases resistance to {_STATUS_NAMES.get(sc, sc)} by {v//100}%.",
    "bAddEff":      lambda sc, v: f"{v//10:.0f}% chance to inflict {_STATUS_NAMES.get(sc, sc)} on hit.",
    "bAddEffWhenHit": lambda sc, v: f"{v//10:.0f}% chance to inflict {_STATUS_NAMES.get(sc, sc)} when hit.",
    "bAddEff2":     lambda sc, v: f"{v//10:.0f}% chance to self-inflict {_STATUS_NAMES.get(sc, sc)} on hit.",
    "bSkillAtk":    lambda sk, v: f"Increases {sk} damage by {v}%.",
    "bAddDamageClass": lambda cls_, v: f"Increases damage against {_cls(cls_)} by {v}%.",
    "bSPGainRace":  lambda r, v: f"Gains {v} SP per kill of {_race(r)}.",
    "bCastrate":    lambda sk, v: f"{'Reduces' if v < 0 else 'Increases'} {sk} cast time by {abs(v)}%.",
    "bAddItemHealRate": lambda _id, v: f"Increases healing from items by {v}%.",
    "bWeaponComaRace": lambda r, v: f"{v//10:.0f}% chance to inflict Coma on {_race(r)} per hit.",
    "bHPDrainRate": lambda v1, v2: f"Drains {v2} HP per {v1} physical hits.",
    "bHPLossRate":  lambda v1, v2: f"Loses {v1} HP every {v2//1000:.0f} seconds.",
    "bAddMonsterDropItem": lambda _id, v: f"Monsters drop an item at {v/100:.2f}% rate.",
    "bSPDrainRate": lambda v1, v2: f"Drains {v2} SP per {v1} physical hits.",
    "bAddSkillBlow": lambda sk, v: f"{sk} knocks enemies back {v} cells.",
}

_BONUS3_TEMPLATES: dict[str, object] = {
    "bAutoSpell": lambda sk, lv, v: f"{v//10:.0f}% chance to auto-cast {sk} Lv.{lv} on physical attack.",
    "bAutoSpellWhenHit": lambda sk, lv, v: f"{v//10:.0f}% chance to auto-cast {sk} Lv.{lv} when hit.",
    "bAddEffOnSkill": lambda sk, sc, v: f"{v//10:.0f}% chance to inflict {_STATUS_NAMES.get(sc, sc)} on {sk} hit.",
    "bAddEff":    lambda sc, v1, v2: f"[Conditional] {v1//10:.0f}% chance to inflict {_STATUS_NAMES.get(sc, sc)}.",
    "bSubEle":    lambda e, v, _flag: f"Reduces {_ele(e)}-element damage by {v}% (conditional).",
    "bAddMonsterDropItem": lambda _id, v, _ty: f"Monsters drop an item at {v/100:.2f}% rate (type-conditional).",
    "bAddClassDropItem":   lambda cls_, v, _ty: f"{_cls(cls_)} drop an item at {v/100:.2f}% rate.",
    "bAddEffWhenHit": lambda sc, v1, _flag: f"[Conditional] {v1//10:.0f}% chance to inflict {_STATUS_NAMES.get(sc, sc)} when hit.",
    "bSPDrainRate": lambda v1, v2, _flag: f"Drains {v2} SP per {v1} hits (conditional).",
}

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Matches: bonus bXxx,val | bonus2 bXxx,a,b | bonus3 bXxx,a,b,c
# Also handles: bonus bXxx val  (space-separated)
_BONUS_RE = re.compile(
    r'\bbonus(2|3)?\s+'       # "bonus", "bonus2", or "bonus3"
    r'(b\w+)'                  # bonus type e.g. bStr
    r'(?:[,\s](.+?))?'         # optional params (lazy, to next semicolon or end)
    r'(?=;|$)',                # lookahead: ends at semicolon or EOL
    re.MULTILINE,
)


def _coerce(s: str):
    """Try to convert a param string to int; leave as str if not numeric."""
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        return s


def parse_script(script: str) -> list[ItemEffect]:
    """Parse a Hercules item script string into a list of ItemEffect objects."""
    if not script:
        return []

    effects: list[ItemEffect] = []

    for m in _BONUS_RE.finditer(script):
        arity_suffix = m.group(1)  # None, "2", or "3"
        arity = int(arity_suffix) if arity_suffix else 1
        bonus_type = m.group(2)
        raw_params = m.group(3) or ""

        # Split params on comma; first param for arity-1 may be the only token
        parts = [p.strip() for p in raw_params.split(",") if p.strip()]
        params = [_coerce(p) for p in parts]

        description = _make_description(bonus_type, arity, params)

        effects.append(ItemEffect(
            bonus_type=bonus_type,
            arity=arity,
            params=params,
            description=description,
        ))

    return effects


def _make_description(bonus_type: str, arity: int, params: list) -> str:
    try:
        if arity == 1:
            tmpl = _BONUS1_TEMPLATES.get(bonus_type)
            if tmpl and params:
                return tmpl(params[0])
        elif arity == 2:
            tmpl = _BONUS2_TEMPLATES.get(bonus_type)
            if tmpl and len(params) >= 2:
                return tmpl(*params[:2])
        else:  # arity == 3
            tmpl = _BONUS3_TEMPLATES.get(bonus_type)
            if tmpl and len(params) >= 3:
                return tmpl(*params[:3])
    except Exception:
        pass  # malformed param — fall through to default

    return f"[{bonus_type} effect]"
