#!/usr/bin/env python
"""
tools/import_item_db.py

One-shot scraper: reads Hercules/db/pre-re/item_db.conf and writes
core/data/pre-re/db/item_db.json.

Types scraped:
  IT_WEAPON (708)  — weapons (Subtype W_*); all fields
  IT_ARMOR  (1431) — armor, shields, headgear, garment, shoes, accessories
  IT_CARD   (538)  — cards; loc identifies which slot accepts the card
  IT_AMMO   (83)   — arrows, bolts, bullets, cannon balls (Subtype A_*)

Types skipped (not equippable player gear):
  IT_CASH, IT_USABLE, IT_HEALING, IT_PETEGG, IT_PETARMOR, IT_DELAYCONSUME

Usage:
    python tools/import_item_db.py           # write to output path
    python tools/import_item_db.py --dry-run # print sample, do not write

Run from the PS_Calc/ project root. No external dependencies — stdlib only.

Schema notes:
  - All entries include: id, aegis_name, name, type, buy, sell, weight,
    equip_level, loc (list), upper, job, gender, script.
  - IT_WEAPON adds: atk, level, weapon_type, element, slots, refineable, range.
  - IT_ARMOR adds:  def, slots, refineable, view_sprite,
                    on_equip_script, on_unequip_script.
  - IT_AMMO adds:   atk, subtype, element.
  - IT_CARD adds nothing beyond shared fields.
  - loc is always a list (single string normalized to one-element list).
  - element derived from 'bonus bAtkEle,Ele_*' in Script (IT_WEAPON, IT_AMMO only).
  - buy null when absent; sell = explicit Sell or buy//2 or null.
  - Refine: absent → true (Hercules default).
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — relative to project root (run from PS_Calc/)
# ---------------------------------------------------------------------------
CONF_PATH = Path("Hercules/db/pre-re/item_db.conf")
OUT_PATH  = Path("core/data/pre-re/db/item_db.json")

# ---------------------------------------------------------------------------
# Types to include vs skip
# ---------------------------------------------------------------------------
EQUIP_TYPES = {"IT_WEAPON", "IT_ARMOR", "IT_CARD", "IT_AMMO"}
SKIP_TYPES  = {
    "IT_CASH", "IT_USABLE", "IT_HEALING",
    "IT_PETEGG", "IT_PETARMOR", "IT_DELAYCONSUME", "IT_ETC",
}

# ---------------------------------------------------------------------------
# Subtype → weapon_type string (W_* → human-readable)
# Must match strings in size_fix.json and mastery_weapon_map.json.
# Source: Hercules/src/map/pc.h W_* enum + size_fix.txt column headers.
# ---------------------------------------------------------------------------
WEAPON_SUBTYPE_MAP: dict[str, str] = {
    "W_1HSWORD": "1HSword",
    "W_2HSWORD": "2HSword",
    "W_1HSPEAR": "1HSpear",
    "W_2HSPEAR": "2HSpear",
    "W_1HAXE":   "1HAxe",
    "W_2HAXE":   "2HAxe",
    "W_MACE":    "Mace",
    "W_2HMACE":  "2HMace",
    "W_STAFF":   "Staff",
    "W_2HSTAFF": "2HStaff",
    "W_BOW":     "Bow",
    "W_KATAR":   "Katar",
    "W_KNUCKLE": "Knuckle",
    "W_MUSICAL": "MusicalInstrument",
    "W_WHIP":    "Whip",
    "W_BOOK":    "Book",
    "W_DAGGER":  "Knife",
    "W_REVOLVER":"Revolver",
    "W_RIFLE":   "Rifle",
    "W_SHOTGUN": "Shotgun",
    "W_GATLING": "Gatling",
    "W_GRENADE": "Grenade",
    "W_HUUMA":   "Fuuma",
}

# ---------------------------------------------------------------------------
# Element name → integer
# Must match DataLoader.get_element_name() in core/data_loader.py.
# Source: Hercules/src/map/map.h ELE_* enum.
# ---------------------------------------------------------------------------
ELEMENT_MAP: dict[str, int] = {
    "Neutral": 0,
    "Water":   1,
    "Earth":   2,
    "Fire":    3,
    "Wind":    4,
    "Poison":  5,
    "Holy":    6,
    "Dark":    7,
    "Ghost":   8,
    "Undead":  9,
}


# ---------------------------------------------------------------------------
# Entry block extractor
# ---------------------------------------------------------------------------

def extract_entries(text: str) -> list[str]:
    """
    Extract all top-level { ... } entry blocks from the item_db list.

    Uses a character-level state machine to skip:
    - // line comments  (may contain { } characters)
    - <" ... "> script blocks  (may contain { } characters)

    This avoids the need for an external libconfig parser and is robust
    against Hercules' non-standard <" ... "> heredoc extension.
    """
    entries: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        # Skip // line comment at top level
        if text[i] == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue

        if text[i] == "{":
            # Found start of an entry block — track depth until closing }
            start = i
            depth = 1
            i += 1
            while i < n and depth > 0:
                # Skip // comment inside entry
                if text[i] == "/" and i + 1 < n and text[i + 1] == "/":
                    while i < n and text[i] != "\n":
                        i += 1
                    continue
                # Skip <" ... "> script block — do not count braces inside
                if text[i] == "<" and i + 1 < n and text[i + 1] == '"':
                    i += 2
                    while i < n:
                        if text[i] == '"' and i + 1 < n and text[i + 1] == ">":
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
# Field helpers
# ---------------------------------------------------------------------------

def extract_script_text(entry: str, field_name: str = "Script") -> str:
    """Return raw text inside <field_name>: <\" ... \"> or empty string."""
    match = re.search(rf'{field_name}:\s*<"\s*(.*?)\s*">', entry, re.DOTALL)
    return match.group(1) if match else ""


def parse_loc(entry: str) -> list[str]:
    """
    Parse Loc field — returns a list always.
    Handles both string form:  Loc: "EQP_ARMOR"
    and array form:            Loc: ["EQP_HEAD_LOW", "EQP_HEAD_MID"]
    """
    array_match = re.search(r'Loc:\s*\[([^\]]+)\]', entry)
    if array_match:
        return re.findall(r'"([^"]+)"', array_match.group(1))
    str_match = re.search(r'Loc:\s*"([^"]+)"', entry)
    return [str_match.group(1)] if str_match else []


def parse_buy_sell(entry: str) -> tuple[int | None, int | None]:
    """Returns (buy, sell). sell inferred as buy//2 when absent."""
    buy_match = re.search(r"\bBuy:\s*(\d+)", entry)
    buy = int(buy_match.group(1)) if buy_match else None
    sell_match = re.search(r"\bSell:\s*(\d+)", entry)
    if sell_match:
        sell = int(sell_match.group(1))
    elif buy is not None:
        sell = buy // 2
    else:
        sell = None
    return buy, sell


# ---------------------------------------------------------------------------
# Hercules job name → set of job IDs in PS_Calc (build_header.py _JOB_NAMES).
# Base-class names include all promoted descendants (Hercules inheritance).
# Source: Hercules PC class hierarchy; confirmed against build_header.py.
# ---------------------------------------------------------------------------
_HERCULES_JOB_TO_IDS: dict[str, frozenset] = {
    # Base and 2nd-job classes — Hercules inheritance: base name includes all
    # promoted descendants. IDs match Hercules constants.conf Job_* values.
    "Novice":         frozenset({0}),
    "Swordsman":      frozenset({1, 7, 14, 4008, 4015}),
    "Magician":       frozenset({2, 9, 16, 4010, 4017}),
    "Archer":         frozenset({3, 11, 19, 20, 4012, 4020, 4021}),
    "Acolyte":        frozenset({4, 8, 15, 4009, 4016}),
    "Merchant":       frozenset({5, 10, 18, 4011, 4019}),
    "Thief":          frozenset({6, 12, 17, 4013, 4018}),
    "Knight":         frozenset({7, 4008}),
    "Priest":         frozenset({8, 4009}),
    "Wizard":         frozenset({9, 4010}),
    "Blacksmith":     frozenset({10, 4011}),
    "Hunter":         frozenset({11, 4012}),
    "Assassin":       frozenset({12, 4013}),
    "Crusader":       frozenset({14, 4015}),
    "Monk":           frozenset({15, 4016}),
    "Sage":           frozenset({16, 4017}),
    "Rogue":          frozenset({17, 4018}),
    "Alchemist":      frozenset({18, 4019}),
    "Bard":           frozenset({19, 4020}),
    "Dancer":         frozenset({20, 4021}),
    # Extended pre-renewal classes with their proper Hercules job IDs.
    "Gunslinger":     frozenset({24}),
    "Ninja":          frozenset({25}),
    "Taekwon":        frozenset({4046}),
    "Star_Gladiator": frozenset({4047}),
    "Soul_Linker":    frozenset({4049}),
    "Gangsi":         frozenset({4050}),
    "Death_Knight":   frozenset({4051}),
    "Dark_Collector": frozenset({4052}),
    "Kagerou":        frozenset({4211}),
    "Rebellion":      frozenset({4215}),
    "Summoner":       frozenset({4218}),
}


def parse_job_list(entry: str) -> list[int]:
    """
    Parse Job: { Name: true ... } block into a sorted list of job IDs.

    Returns [] when the item is equippable by all jobs (no Job block, or All: true).
    Returns a sorted list of job IDs when the item has specific job restrictions.
    Promoted classes are included via _HERCULES_JOB_TO_IDS inheritance mapping.
    """
    block_match = re.search(r'Job:\s*\{([^}]+)\}', entry, re.DOTALL)
    if not block_match:
        return []
    names = re.findall(r'(\w+):\s*true', block_match.group(1))
    if not names or "All" in names:
        return []
    ids: set[int] = set()
    for name in names:
        ids |= _HERCULES_JOB_TO_IDS.get(name, frozenset())
    return sorted(ids)


def parse_refineable(entry: str) -> bool:
    """Refine: absent → true (Hercules default). Only false is ever explicit."""
    refine_match = re.search(r"\bRefine:\s*(false|true)\b", entry, re.IGNORECASE)
    return refine_match.group(1).lower() != "false" if refine_match else True


def parse_atk_element(script_text: str) -> int:
    """Extract element integer from 'bonus bAtkEle,Ele_<Name>' in script."""
    ele_match = re.search(r"bonus\s+bAtkEle\s*,\s*Ele_(\w+)", script_text)
    return ELEMENT_MAP.get(ele_match.group(1), 0) if ele_match else 0


def parse_common_fields(entry: str, item_id: int, item_type: str) -> dict:
    """Fields shared across all equippable types."""
    aegis_match = re.search(r'AegisName:\s*"([^"]+)"', entry)
    aegis_name  = aegis_match.group(1) if aegis_match else ""

    name_match = re.search(r'\bName:\s*"([^"]+)"', entry)
    name       = name_match.group(1) if name_match else ""

    buy, sell = parse_buy_sell(entry)

    weight_match = re.search(r"\bWeight:\s*(\d+)", entry)
    weight = int(weight_match.group(1)) if weight_match else 0

    equiplv_match = re.search(r"\bEquipLv:\s*(\d+)", entry)
    equip_level = int(equiplv_match.group(1)) if equiplv_match else 0

    upper_match = re.search(r'Upper:\s*"([^"]+)"', entry)
    upper = upper_match.group(1) if upper_match else None

    gender_match = re.search(r'Gender:\s*"([^"]+)"', entry)
    gender = gender_match.group(1) if gender_match else None

    script_text = extract_script_text(entry, "Script")
    script = script_text if script_text else None

    return {
        "id":          item_id,
        "aegis_name":  aegis_name,
        "name":        name,
        "type":        item_type,
        "buy":         buy,
        "sell":        sell,
        "weight":      weight,
        "equip_level": equip_level,
        "loc":         parse_loc(entry),
        "upper":       upper,
        "job":         parse_job_list(entry),
        "gender":      gender,
        "script":      script,
    }


# ---------------------------------------------------------------------------
# Per-type parsers
# ---------------------------------------------------------------------------

def parse_weapon(entry: str, item_id: int) -> dict | None:
    """IT_WEAPON — requires a known W_* Subtype."""
    subtype_match = re.search(r'Subtype:\s*"(W_\w+)"', entry)
    if not subtype_match:
        return None
    raw_subtype = subtype_match.group(1)
    weapon_type = WEAPON_SUBTYPE_MAP.get(raw_subtype)
    if weapon_type is None:
        print(f"WARNING: Unknown Subtype {raw_subtype!r} (id={item_id}) — skipped.",
              file=sys.stderr)
        return None

    base = parse_common_fields(entry, item_id, "IT_WEAPON")

    atk_match  = re.search(r"\bAtk:\s*(\d+)", entry)
    wlv_match  = re.search(r"\bWeaponLv:\s*(\d+)", entry)
    slots_match = re.search(r"\bSlots:\s*(\d+)", entry)
    range_match = re.search(r"\bRange:\s*(\d+)", entry)

    script_text = extract_script_text(entry, "Script")

    base.update({
        "atk":         int(atk_match.group(1))  if atk_match  else 0,
        "level":       int(wlv_match.group(1))  if wlv_match  else 1,
        "weapon_type": weapon_type,
        "element":     parse_atk_element(script_text),
        "slots":       int(slots_match.group(1)) if slots_match else 0,
        "refineable":  parse_refineable(entry),
        "range":       int(range_match.group(1)) if range_match else 0,
    })
    return base


def parse_armor(entry: str, item_id: int) -> dict:
    """IT_ARMOR — body armor, shields, headgear, garment, shoes, accessories."""
    base = parse_common_fields(entry, item_id, "IT_ARMOR")

    def_match     = re.search(r"\bDef:\s*(\d+)", entry)
    slots_match   = re.search(r"\bSlots:\s*(\d+)", entry)
    sprite_match  = re.search(r"\bViewSprite:\s*(\d+)", entry)

    on_equip_text   = extract_script_text(entry, "OnEquipScript")
    on_unequip_text = extract_script_text(entry, "OnUnequipScript")

    base.update({
        "def":               int(def_match.group(1))    if def_match    else 0,
        "slots":             int(slots_match.group(1))  if slots_match  else 0,
        "refineable":        parse_refineable(entry),
        "view_sprite":       int(sprite_match.group(1)) if sprite_match else 0,
        "on_equip_script":   on_equip_text   if on_equip_text   else None,
        "on_unequip_script": on_unequip_text if on_unequip_text else None,
    })
    return base


def parse_card(entry: str, item_id: int) -> dict:
    """IT_CARD — cards; loc identifies which slot they go in."""
    return parse_common_fields(entry, item_id, "IT_CARD")


def parse_ammo(entry: str, item_id: int) -> dict:
    """IT_AMMO — arrows, bolts, bullets, cannon balls (Subtype A_*)."""
    base = parse_common_fields(entry, item_id, "IT_AMMO")

    subtype_match = re.search(r'Subtype:\s*"(A_\w+)"', entry)
    subtype = subtype_match.group(1) if subtype_match else ""

    atk_match = re.search(r"\bAtk:\s*(\d+)", entry)
    script_text = extract_script_text(entry, "Script")

    base.update({
        "atk":     int(atk_match.group(1)) if atk_match else 0,
        "subtype": subtype,
        "element": parse_atk_element(script_text),
    })
    return base


# ---------------------------------------------------------------------------
# Entry dispatcher
# ---------------------------------------------------------------------------

def parse_entry(entry: str) -> dict | None:
    """Dispatch to the correct per-type parser. Returns None for skipped types."""
    type_match = re.search(r'Type:\s*"(IT_\w+)"', entry)
    if not type_match:
        return None
    item_type = type_match.group(1)

    if item_type in SKIP_TYPES or item_type not in EQUIP_TYPES:
        return None

    id_match = re.search(r"\bId:\s*(\d+)", entry)
    if not id_match:
        return None
    item_id = int(id_match.group(1))

    if item_type == "IT_WEAPON":
        return parse_weapon(entry, item_id)
    if item_type == "IT_ARMOR":
        return parse_armor(entry, item_id)
    if item_type == "IT_CARD":
        return parse_card(entry, item_id)
    if item_type == "IT_AMMO":
        return parse_ammo(entry, item_id)
    return None  # unreachable given EQUIP_TYPES guard


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Expected counts from: grep -c '"IT_<TYPE>"' Hercules/db/pre-re/item_db.conf
EXPECTED_COUNTS = {
    "IT_WEAPON": 708,
    "IT_ARMOR":  1431,
    "IT_CARD":   538,
    "IT_AMMO":   83,
}


def main(dry_run: bool = False) -> None:
    if not CONF_PATH.exists():
        sys.exit(f"ERROR: {CONF_PATH} not found. Run from PS_Calc/ root.")

    print(f"Reading {CONF_PATH} ...")
    text = CONF_PATH.read_text(encoding="utf-8")

    print("Extracting entry blocks ...")
    entries = extract_entries(text)
    print(f"  Total blocks found: {len(entries)}")

    items: dict[str, dict] = {}
    skipped = 0
    counts: dict[str, int] = {}

    for entry in entries:
        result = parse_entry(entry)
        if result is None:
            skipped += 1
        else:
            items[str(result["id"])] = result
            t = result["type"]
            counts[t] = counts.get(t, 0) + 1

    print(f"  Entries parsed: {len(items)}")
    for t, n in sorted(counts.items()):
        expected = EXPECTED_COUNTS.get(t, "?")
        flag = "" if n == expected else f"  *** EXPECTED {expected} ***"
        print(f"    {t}: {n}{flag}")
    print(f"  Entries skipped: {skipped}")

    for t, expected in EXPECTED_COUNTS.items():
        actual = counts.get(t, 0)
        if actual != expected:
            print(
                f"WARNING: {t} count mismatch — expected {expected}, got {actual}.",
                file=sys.stderr,
            )

    output = {
        "_source":    "Scraped from Hercules/db/pre-re/item_db.conf",
        "_scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_note": (
            "Types: IT_WEAPON (Subtype W_*), IT_ARMOR, IT_CARD, IT_AMMO (Subtype A_*). "
            "Skipped: IT_CASH, IT_USABLE, IT_HEALING, IT_PETEGG, IT_PETARMOR, IT_DELAYCONSUME. "
            "loc is always a list (single-string Loc normalized to one-element list). "
            "element derived from 'bonus bAtkEle,Ele_*' in Script (IT_WEAPON, IT_AMMO only). "
            "buy null when absent; sell = explicit Sell field, or buy//2, or null. "
            "Refine: absent → refineable=true (Hercules default). "
            "equip_level 0 when absent. upper null = ITEMUPPER_ALL. "
            "job = sorted list of job IDs (int); [] = equippable by all classes. "
            "Promoted classes included via Hercules base-class inheritance (e.g. Knight: true → [7,23]). "
            "gender null = any. on_equip_script/on_unequip_script null when absent (IT_ARMOR). "
            "IT_WEAPON.range = Range field (0 if absent). "
            "IT_ARMOR.view_sprite = ViewSprite field (0 if absent). "
            "IT_AMMO.subtype = raw A_* string from Subtype field."
        ),
        "items": items,
    }

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(items)} items to {OUT_PATH}")
        sample_keys = list(items.keys())[:3]
        for k in sample_keys:
            print(f"  {k}: {items[k]}")
        return

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nWrote {len(items)} items to {OUT_PATH}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
