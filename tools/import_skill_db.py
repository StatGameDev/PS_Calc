#!/usr/bin/env python3
"""
tools/import_skill_db.py

One-shot scraper: reads Hercules/db/pre-re/skill_db.conf and writes
core/data/pre-re/db/skills.json.

All skill metadata is captured faithfully. Damage ratios are NOT in
skill_db.conf — they live in skill_ratio.py (sourced from Hercules skill.c).

Usage:
    python tools/import_skill_db.py            # write output
    python tools/import_skill_db.py --dry-run  # print sample, no write

Run from the PS_Calc/ project root. No external dependencies — stdlib only.

Schema:
  Per-level-capable fields are stored as list[int|str] of length max_level,
  indexed 0 = Lv1. Flat values are repeated (e.g., [100, 100, ..., 100]).

  Boolean flag blocks (SkillType, DamageType, etc.) are stored as list[str]
  of true-valued key names. Absent = [].

  requirements: always present (defaults to zero/empty).
  unit: null when absent (trap/AoE skills only).
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CONF_PATH = Path("Hercules/db/pre-re/skill_db.conf")
OUT_PATH  = Path("core/data/pre-re/db/skills.json")


# ---------------------------------------------------------------------------
# Entry block extractor (character-level state machine)
# ---------------------------------------------------------------------------

def extract_entries(text: str) -> list[str]:
    """
    Extract all top-level { ... } skill entry blocks from skill_db.

    Handles:
    - // line comments (throughout file)
    - /* ... */ block comments (header documentation at top of file)
    Both comment types are skipped; brace depth is not counted inside them.
    """
    entries: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        # Skip // line comment
        if text[i] == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue

        # Skip /* ... */ block comment (used for the format-doc header only)
        if text[i] == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i < n:
                if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    i += 2
                    break
                i += 1
            continue

        if text[i] == "{":
            start = i
            depth = 1
            i += 1
            while i < n and depth > 0:
                # Skip // inside entry
                if text[i] == "/" and i + 1 < n and text[i + 1] == "/":
                    while i < n and text[i] != "\n":
                        i += 1
                    continue
                # Skip /* */ inside entry (unlikely, but robust)
                if text[i] == "/" and i + 1 < n and text[i + 1] == "*":
                    i += 2
                    while i < n:
                        if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                            i += 2
                            break
                        i += 1
                    continue
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            entries.append(text[start:i])
            continue

        i += 1

    return entries


# ---------------------------------------------------------------------------
# Text masking (prevents nested sub-block fields from being matched at
# the top level, e.g. Unit.Range shadowing the skill's top-level Range).
# ---------------------------------------------------------------------------

def mask_subblocks(text: str, blank_from_depth: int = 1) -> str:
    """
    Replace all content inside { } blocks at or beyond blank_from_depth with spaces.

    blank_from_depth=2: use on a full entry block (outer { } = depth 1, visible;
                        nested blocks at depth 2+ are blanked).
    blank_from_depth=1: use on inner sub-block text (no surrounding braces;
                        any nested per-level or flag block at depth 1+ is blanked).
    """
    result = list(text)
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
            if depth >= blank_from_depth:
                result[i] = " "
        elif ch == "}":
            if depth >= blank_from_depth:
                result[i] = " "
            depth -= 1
        elif depth >= blank_from_depth:
            result[i] = " "
    return "".join(result)


# ---------------------------------------------------------------------------
# Sub-block extractor (depth-tracked; handles nested braces correctly)
# ---------------------------------------------------------------------------

def extract_subblock(text: str, field_name: str) -> str | None:
    """
    Find 'field_name: { ... }' in text and return the inner content.

    Uses depth-tracking rather than regex to correctly handle nested braces
    (e.g., Requirements contains its own nested per-level and flag blocks).
    Returns None if the field is absent.
    """
    m = re.compile(rf"\b{re.escape(field_name)}\s*:\s*\{{").search(text)
    if not m:
        return None
    i = m.end()   # position immediately after the opening {
    depth = 1
    n = len(text)
    while i < n and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[m.end(): i - 1]


# ---------------------------------------------------------------------------
# Per-level value parsers
# ---------------------------------------------------------------------------

def perlevel_int(inner: str, max_level: int, default: int = 0) -> list[int]:
    """Parse 'Lv1: x  Lv2: y  ...' inner text → list[int] of length max_level."""
    result = [default] * max_level
    for m in re.finditer(r"Lv(\d+)\s*:\s*(-?\d+)", inner):
        lv = int(m.group(1))
        if 1 <= lv <= max_level:
            result[lv - 1] = int(m.group(2))
    return result


def perlevel_str(inner: str, max_level: int, default: str = "") -> list[str]:
    """Parse 'Lv1: "val"  Lv2: "val"  ...' inner text → list[str] of length max_level."""
    result = [default] * max_level
    for m in re.finditer(r'Lv(\d+)\s*:\s*"([^"]*)"', inner):
        lv = int(m.group(1))
        if 1 <= lv <= max_level:
            result[lv - 1] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Unified field parsers (per-level block OR flat value)
# ---------------------------------------------------------------------------

def field_int(block: str, top: str, field_name: str, max_level: int,
              default: int = 0) -> list[int]:
    """
    Parse an integer field that may be per-level or flat.

    block: full (unmasked) text — used for per-level sub-block search.
    top:   masked text (mask_subblocks applied) — used for flat value search
           so that nested occurrences (e.g. Unit.Range) are not matched.
    Returns list[int] of length max_level.
    """
    inner = extract_subblock(block, field_name)
    if inner is not None:
        return perlevel_int(inner, max_level, default)
    m = re.search(rf"\b{re.escape(field_name)}\s*:\s*(-?\d+)", top)
    return [int(m.group(1))] * max_level if m else [default] * max_level


def field_str(block: str, top: str, field_name: str, max_level: int,
              default: str = "") -> list[str]:
    """
    Parse a string field that may be per-level or flat.
    Returns list[str] of length max_level.
    """
    inner = extract_subblock(block, field_name)
    if inner is not None:
        return perlevel_str(inner, max_level, default)
    m = re.search(rf'\b{re.escape(field_name)}\s*:\s*"([^"]*)"', top)
    return [m.group(1)] * max_level if m else [default] * max_level


def field_bool(top: str, field_name: str) -> bool:
    """Parse a simple flat boolean field from masked top-level text."""
    m = re.search(rf"\b{re.escape(field_name)}\s*:\s*(true|false)\b", top,
                  re.IGNORECASE)
    return m.group(1).lower() == "true" if m else False


def flag_list(block: str, field_name: str) -> list[str]:
    """
    Parse a boolean flag block → list of true-valued key names.
    Uses extract_subblock (depth-tracked) on the unmasked block.
    Returns [] if the field is absent.
    """
    inner = extract_subblock(block, field_name)
    if inner is None:
        return []
    return re.findall(r"(\w+)\s*:\s*true", inner)


# ---------------------------------------------------------------------------
# Sub-parsers for Requirements and Unit
# ---------------------------------------------------------------------------

def parse_requirements(block: str, max_level: int) -> dict:
    """Parse the Requirements: { ... } sub-block. Returns defaults if absent."""
    req_text = extract_subblock(block, "Requirements")
    empty: dict = {
        "hp_cost":           [0] * max_level,
        "sp_cost":           [0] * max_level,
        "hp_rate_cost":      [0] * max_level,
        "sp_rate_cost":      [0] * max_level,
        "zero_cast_time":    False,
        "weapon_types":      [],
        "ammo_types":        [],
        "ammo_amount":       [0] * max_level,
        "state":             None,
        "spirit_sphere_cost": [0] * max_level,
        "items":             [],
        "equip":             [],
    }
    if req_text is None:
        return empty

    # Masked version — blanks per-level blocks and flag blocks within Requirements,
    # so flat-value searches (State, ZeroCastTime, AmmoTypes "All") are unambiguous.
    req_top = mask_subblocks(req_text, blank_from_depth=1)

    # AmmoTypes: may be a flag block { A_ARROW: true } or the special string "All"
    ammo_all_m = re.search(r'\bAmmoTypes\s*:\s*"All"', req_top)
    if ammo_all_m:
        ammo_types: list[str] = ["All"]
    else:
        ammo_types = flag_list(req_text, "AmmoTypes")

    # Items: { AegisName: amount, ... }  — key is unquoted aegis name, value is int
    items: list[dict] = []
    items_inner = extract_subblock(req_text, "Items")
    if items_inner:
        for m in re.finditer(r"(\w+)\s*:\s*(\d+)", items_inner):
            key = m.group(1)
            if key != "Any":
                items.append({"item": key, "amount": int(m.group(2))})

    # Equip: { AegisName: amount }
    equip: list[str] = []
    equip_inner = extract_subblock(req_text, "Equip")
    if equip_inner:
        equip = [m.group(1) for m in re.finditer(r"(\w+)\s*:\s*\d+", equip_inner)
                 if m.group(1) != "Any"]

    # State: flat string (e.g. "ExplosionSpirits", "Riding") — "None" → null
    state_m = re.search(r'\bState\s*:\s*"([^"]*)"', req_top)
    state: str | None = state_m.group(1) if state_m else None
    if state == "None":
        state = None

    return {
        "hp_cost":           field_int(req_text, req_top, "HPCost", max_level),
        "sp_cost":           field_int(req_text, req_top, "SPCost", max_level),
        "hp_rate_cost":      field_int(req_text, req_top, "HPRateCost", max_level),
        "sp_rate_cost":      field_int(req_text, req_top, "SPRateCost", max_level),
        "zero_cast_time":    field_bool(req_top, "ZeroCastTime"),
        "weapon_types":      flag_list(req_text, "WeaponTypes"),
        "ammo_types":        ammo_types,
        "ammo_amount":       field_int(req_text, req_top, "AmmoAmount", max_level),
        "state":             state,
        "spirit_sphere_cost": field_int(req_text, req_top, "SpiritSphereCost", max_level),
        "items":             items,
        "equip":             equip,
    }


def parse_unit(block: str) -> dict | None:
    """Parse the Unit: { ... } sub-block. Returns None if absent."""
    unit_text = extract_subblock(block, "Unit")
    if unit_text is None:
        return None

    # Mask nested Flag block so Unit-level fields are unambiguous
    unit_top = mask_subblocks(unit_text, blank_from_depth=1)

    # Id: 0x92  or  Id: [ 0x81, 0x80 ]  (hex unit IDs)
    id_arr_m = re.search(r"\bId\s*:\s*\[([^\]]+)\]", unit_top)
    if id_arr_m:
        unit_id: int | list[int] = [int(x.strip(), 0) for x in id_arr_m.group(1).split(",")]
    else:
        id_m = re.search(r"\bId\s*:\s*(0x[0-9a-fA-F]+|\d+)", unit_top)
        unit_id = int(id_m.group(1), 0) if id_m else 0

    layout_m   = re.search(r"\bLayout\s*:\s*(-?\d+)", unit_top)
    range_m    = re.search(r"\bRange\s*:\s*(-?\d+)", unit_top)
    interval_m = re.search(r"\bInterval\s*:\s*(-?\d+)", unit_top)
    target_m   = re.search(r'\bTarget\s*:\s*"([^"]*)"', unit_top)

    return {
        "id":       unit_id,
        "layout":   int(layout_m.group(1))   if layout_m   else 0,
        "range":    int(range_m.group(1))    if range_m    else 0,
        "interval": int(interval_m.group(1)) if interval_m else 0,
        "target":   target_m.group(1)        if target_m   else "None",
        "flag":     flag_list(unit_text, "Flag"),
    }


# ---------------------------------------------------------------------------
# Main entry parser
# ---------------------------------------------------------------------------

def parse_skill(block: str) -> dict | None:
    """
    Parse a single skill entry block. Returns None if Id is missing.

    top = mask_subblocks(block, blank_from_depth=2):
      Blanks all content at depth ≥ 2 (inside nested blocks like SkillType,
      DamageType, Requirements, Unit). Safe for simple field regex searches.
    block (unmasked) is passed to sub-block parsers and flag_list.
    """
    top = mask_subblocks(block, blank_from_depth=2)

    id_m = re.search(r"\bId\s*:\s*(\d+)", top)
    if not id_m:
        return None
    skill_id = int(id_m.group(1))

    name_m  = re.search(r'\bName\s*:\s*"([^"]*)"',        top)
    desc_m  = re.search(r'\bDescription\s*:\s*"([^"]*)"', top)
    sc_m    = re.search(r'\bStatusChange\s*:\s*"([^"]*)"', top)
    maxlv_m = re.search(r"\bMaxLevel\s*:\s*(\d+)",         top)
    hit_m   = re.search(r'\bHit\s*:\s*"([^"]*)"',         top)
    atk_m   = re.search(r'\bAttackType\s*:\s*"([^"]*)"',  top)

    max_level = int(maxlv_m.group(1)) if maxlv_m else 1

    return {
        # ---- Mandatory fields ----
        "id":                     skill_id,
        "name":                   name_m.group(1)  if name_m  else "",
        "max_level":              max_level,
        # ---- Optional fields ----
        "description":            desc_m.group(1)  if desc_m  else None,
        "status_change":          sc_m.group(1)    if sc_m    else None,
        # Range: per-level int or flat; negative = melee range constants
        "range":                  field_int(block, top, "Range", max_level, default=0),
        # Hit type: "BDT_SKILL", "BDT_MULTIHIT", "BDT_NORMAL" (None = BDT_NORMAL)
        "hit":                    hit_m.group(1)   if hit_m   else None,
        # SkillType: Passive/Enemy/Place/Self/Friend/Trap/Item
        "skill_type":             flag_list(block, "SkillType"),
        # SkillInfo: Quest/NPC/Wedding/AllowReproduce/AllowPlagiarism/...
        "skill_info":             flag_list(block, "SkillInfo"),
        # AttackType: "Weapon", "Magic", "Misc", None (= "None")
        "attack_type":            atk_m.group(1)   if atk_m   else None,
        # Element: "Ele_Weapon", "Ele_Fire", "Ele_Neutral", etc. — per-level capable
        "element":                field_str(block, top, "Element", max_level,
                                            default="Ele_Neutral"),
        # DamageType flags: NoDamage, SplashArea, SplitDamage, IgnoreCards,
        #   IgnoreElement, IgnoreDefense, IgnoreFlee, IgnoreDefCards
        "damage_type":            flag_list(block, "DamageType"),
        "splash_range":           field_int(block, top, "SplashRange", max_level),
        # NumberOfHits: positive = counts toward damage; negative = display-only
        "number_of_hits":         field_int(block, top, "NumberOfHits", max_level, default=1),
        "knock_back_tiles":       field_int(block, top, "KnockBackTiles", max_level),
        "interrupt_cast":         field_bool(top, "InterruptCast"),
        "cast_def_rate":          field_int(block, top, "CastDefRate", max_level),
        "skill_instances":        field_int(block, top, "SkillInstances", max_level),
        # Timing (all in ms)
        "cast_time":              field_int(block, top, "CastTime", max_level),
        "after_cast_act_delay":   field_int(block, top, "AfterCastActDelay", max_level),
        "after_cast_walk_delay":  field_int(block, top, "AfterCastWalkDelay", max_level),
        # SkillData1/2: meaning is skill-specific (duration, counter limit, etc.)
        "skill_data1":            field_int(block, top, "SkillData1", max_level),
        "skill_data2":            field_int(block, top, "SkillData2", max_level),
        "cool_down":              field_int(block, top, "CoolDown", max_level),
        # Cast/delay modifier flags
        "cast_time_options":      flag_list(block, "CastTimeOptions"),
        "skill_delay_options":    flag_list(block, "SkillDelayOptions"),
        # Sub-objects
        "requirements":           parse_requirements(block, max_level),
        "unit":                   parse_unit(block),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(dry_run: bool = False) -> None:
    if not CONF_PATH.exists():
        sys.exit(f"ERROR: {CONF_PATH} not found. Run from PS_Calc/ root.")

    print(f"Reading {CONF_PATH} ...")
    text = CONF_PATH.read_text(encoding="utf-8")

    print("Extracting entry blocks ...")
    raw_entries = extract_entries(text)
    print(f"  Total blocks found: {len(raw_entries)}")

    skills: dict[str, dict] = {}
    skipped = 0
    errors  = 0

    for block in raw_entries:
        try:
            result = parse_skill(block)
        except Exception as exc:
            # Surface unexpected parse failures with context
            id_m = re.search(r"\bId\s*:\s*(\d+)", block[:200])
            skill_id_hint = id_m.group(1) if id_m else "?"
            print(f"  WARNING: Parse error on Id={skill_id_hint}: {exc}", file=sys.stderr)
            errors += 1
            continue

        if result is None:
            skipped += 1
        else:
            skills[str(result["id"])] = result

    print(f"  Skills parsed:  {len(skills)}")
    print(f"  Blocks skipped: {skipped}  (no Id field — documentation template)")
    if errors:
        print(f"  Parse errors:   {errors}", file=sys.stderr)

    # Spot-checks
    _check("SM_BASH",    skills.get("5"),  "requirements.sp_cost",  [8,8,8,8,8,15,15,15,15,15])
    _check("SM_MAGNUM",  skills.get("7"),  "element",  ["Ele_Fire"] * 10)
    _check("SM_PROVOKE", skills.get("6"),  "damage_type", ["NoDamage"])
    _check("MO_EXTREMITYFIST", skills.get("271"), "damage_type",
           ["IgnoreDefense", "IgnoreFlee"])

    output = {
        "_source":     "Scraped from Hercules/db/pre-re/skill_db.conf",
        "_scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_note": (
            "Pre-renewal skill metadata. Damage ratios are NOT here — see skill_ratio.py "
            "(sourced from Hercules skill.c). "
            "Per-level fields are list[int|str] of length max_level, index 0 = Lv1. "
            "Flat values are repeated across all levels. "
            "Boolean flag blocks stored as list[str] of true-valued keys ([] if absent). "
            "element default = 'Ele_Neutral'. number_of_hits default = 1. "
            "requirements always present (zeroed/empty defaults). unit null if not a trap/AoE skill. "
            "AmmoTypes 'All' stored as ['All']. Unit.id may be int or list[int] (hex-decoded). "
        ),
        "skills": skills,
    }

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(skills)} skills to {OUT_PATH}")
        for key in ["5", "7", "141"]:
            if key in skills:
                s = skills[key]
                print(f"  id={s['id']} name={s['name']} max_level={s['max_level']}")
                print(f"    sp_cost: {s['requirements']['sp_cost']}")
                print(f"    element: {s['element'][:3]}...")
                print(f"    weapon_types: {s['requirements']['weapon_types'][:4]}...")
        return

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nWrote {len(skills)} skills to {OUT_PATH}")


def _check(label: str, entry: dict | None, field: str, expected) -> None:
    """Print a spot-check result."""
    if entry is None:
        print(f"  SPOT-CHECK {label}: MISSING ENTRY", file=sys.stderr)
        return
    val = entry
    for key in field.split("."):
        val = val.get(key) if isinstance(val, dict) else None
    ok = "OK" if val == expected else f"MISMATCH — got {val!r}"
    print(f"  spot-check {label}.{field}: {ok}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
