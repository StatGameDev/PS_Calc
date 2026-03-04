#!/usr/bin/env python
"""
tools/import_item_db.py

One-shot scraper: reads Hercules/db/pre-re/item_db.conf and writes
core/data/pre-re/db/item_db.json (IT_WEAPON entries only).

Usage:
    python tools/import_item_db.py           # write to output path
    python tools/import_item_db.py --dry-run # print sample, do not write

Run from the PS_Calc/ project root. No external dependencies — stdlib only.

Note: IT_AMMO (Subtype A_*) is excluded from this pass. Implement a
separate scraper pass for ammo when the ammo system is added.
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
OUT_PATH = Path("core/data/pre-re/db/item_db.json")

# ---------------------------------------------------------------------------
# Subtype → weapon_type string
# Must match the strings in size_fix.json and mastery_weapon_map.json.
# Source: Hercules/src/map/pc.h W_* enum + size_fix.txt column headers.
# ---------------------------------------------------------------------------
SUBTYPE_MAP: dict[str, str] = {
    "W_1HSWORD": "1HSword",
    "W_2HSWORD": "2HSword",
    "W_1HSPEAR": "1HSpear",
    "W_2HSPEAR": "2HSpear",
    "W_1HAXE":   "1HAxe",
    "W_2HAXE":   "2HAxe",
    "W_MACE":    "Mace",
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


def extract_script_content(entry: str) -> str:
    """Return the raw text inside Script: <\" ... \"> or empty string if absent."""
    match = re.search(r'Script:\s*<"\s*(.*?)\s*">', entry, re.DOTALL)
    return match.group(1) if match else ""


def parse_entry(entry: str) -> dict | None:
    """
    Parse a single entry block. Returns a populated dict for IT_WEAPON entries
    with a known W_* Subtype. Returns None for all other entry types.
    """
    # Filter: must be IT_WEAPON
    if not re.search(r'Type:\s*"IT_WEAPON"', entry):
        return None

    # Filter: must have a W_* Subtype (guards against IT_WEAPON without Subtype)
    subtype_match = re.search(r'Subtype:\s*"(W_\w+)"', entry)
    if not subtype_match:
        return None
    raw_subtype = subtype_match.group(1)
    weapon_type = SUBTYPE_MAP.get(raw_subtype)
    if weapon_type is None:
        print(f"WARNING: Unknown Subtype {raw_subtype!r} — entry skipped.", file=sys.stderr)
        return None

    # Mandatory: Id
    id_match = re.search(r"\bId:\s*(\d+)", entry)
    if not id_match:
        return None
    item_id = int(id_match.group(1))

    # Mandatory: AegisName and Name
    aegis_match = re.search(r'AegisName:\s*"([^"]+)"', entry)
    aegis_name = aegis_match.group(1) if aegis_match else ""

    name_match = re.search(r'\bName:\s*"([^"]+)"', entry)
    name = name_match.group(1) if name_match else ""

    # Optional numeric fields — Hercules defaults are 0 / 1 where noted
    atk_match = re.search(r"\bAtk:\s*(\d+)", entry)
    atk = int(atk_match.group(1)) if atk_match else 0  # default 0

    wlv_match = re.search(r"\bWeaponLv:\s*(\d+)", entry)
    level = int(wlv_match.group(1)) if wlv_match else 1  # default 1 (Hercules default)

    weight_match = re.search(r"\bWeight:\s*(\d+)", entry)
    weight = int(weight_match.group(1)) if weight_match else 0

    slots_match = re.search(r"\bSlots:\s*(\d+)", entry)
    slots = int(slots_match.group(1)) if slots_match else 0

    # Refine — boolean, defaults to true in Hercules; only false is ever written explicitly
    refine_match = re.search(r"\bRefine:\s*(false|true)\b", entry, re.IGNORECASE)
    refineable = refine_match.group(1).lower() != "false" if refine_match else True

    # Element — parsed from Script: bonus bAtkEle,Ele_<Name>
    # Absent bAtkEle = Neutral (0). One bAtkEle per IT_WEAPON entry (verified).
    script_text = extract_script_content(entry)
    ele_match = re.search(r"bonus\s+bAtkEle\s*,\s*Ele_(\w+)", script_text)
    element = ELEMENT_MAP.get(ele_match.group(1), 0) if ele_match else 0

    # --- New fields ---

    # Buy price (null for 47 weapons with no shop price)
    buy_match = re.search(r"\bBuy:\s*(\d+)", entry)
    buy = int(buy_match.group(1)) if buy_match else None

    # Sell price: explicit field, or buy//2 if Buy is present, else null
    sell_match = re.search(r"\bSell:\s*(\d+)", entry)
    if sell_match:
        sell = int(sell_match.group(1))
    elif buy is not None:
        sell = buy // 2
    else:
        sell = None

    # Attack range in cells (always present in weapon entries; default 0 per schema)
    range_match = re.search(r"\bRange:\s*(\d+)", entry)
    range_ = int(range_match.group(1)) if range_match else 0

    # Required equip level (EquipLv [min,max] array form confirmed absent in weapon entries)
    equiplv_match = re.search(r"\bEquipLv:\s*(\d+)", entry)
    equip_level = int(equiplv_match.group(1)) if equiplv_match else 0

    # Equip location — "EQP_WEAPON" (1H) or "EQP_ARMS" (2H)
    loc_match = re.search(r'Loc:\s*"([^"]+)"', entry)
    loc = loc_match.group(1) if loc_match else ""

    # Class tier restriction: null = ITEMUPPER_ALL; "ITEMUPPER_UPPER" = transcendent-only; etc.
    upper_match = re.search(r'Upper:\s*"([^"]+)"', entry)
    upper = upper_match.group(1) if upper_match else None

    # Job class restrictions — dict form only (int mask form confirmed absent in weapon entries)
    job_block_match = re.search(r'Job:\s*\{([^}]+)\}', entry, re.DOTALL)
    job: list[str] = []
    if job_block_match:
        job = re.findall(r'(\w+):\s*true', job_block_match.group(1))

    # Gender restriction: null = any; "SEX_MALE" / "SEX_FEMALE" if restricted
    gender_match = re.search(r'Gender:\s*"([^"]+)"', entry)
    gender = gender_match.group(1) if gender_match else None

    # Raw Athena script text (delimiters stripped); null if no Script block
    # element is separately extracted above; script kept for future passive bonus parsing
    # OnEquipScript/OnUnequipScript confirmed absent from all IT_WEAPON entries — omitted
    script = script_text if script_text else None

    return {
        "id":          item_id,
        "aegis_name":  aegis_name,
        "name":        name,
        "atk":         atk,
        "level":       level,
        "weapon_type": weapon_type,
        "element":     element,
        "weight":      weight,
        "slots":       slots,
        "refineable":  refineable,
        "buy":         buy,
        "sell":        sell,
        "range":       range_,
        "equip_level": equip_level,
        "loc":         loc,
        "upper":       upper,
        "job":         job,
        "gender":      gender,
        "script":      script,
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

    for entry in entries:
        result = parse_entry(entry)
        if result is None:
            skipped += 1
        else:
            items[str(result["id"])] = result

    print(f"  IT_WEAPON entries parsed: {len(items)}")
    print(f"  Non-weapon entries skipped: {skipped}")

    # Sanity checks
    expected_weapon_count = 708  # grep -c '"IT_WEAPON"' item_db.conf
    if len(items) != expected_weapon_count:
        print(
            f"WARNING: Expected {expected_weapon_count} weapons, got {len(items)}. "
            "Check for unmapped subtypes above.",
            file=sys.stderr,
        )

    output = {
        "_source": "Scraped from Hercules/db/pre-re/item_db.conf",
        "_scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_note": (
            "IT_WEAPON entries only (Subtype W_*). "
            "element derived from 'bonus bAtkEle,Ele_*' in Script field; absent bAtkEle = Neutral (0). "
            "buy null for 47 weapons with no shop price; sell inferred as buy//2 when absent. "
            "equip_level 0 if absent. upper null = ITEMUPPER_ALL. job [] = all classes. "
            "gender null = any gender. script is raw Athena text (delimiters stripped) or null. "
            "OnEquipScript/OnUnequipScript absent from all IT_WEAPON entries — omitted. "
            "EquipLv [min,max] form and Job int mask absent from all IT_WEAPON entries. "
            "IT_AMMO (Subtype A_*) excluded — implement separately when ammo system is added."
        ),
        "items": items,
    }

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(items)} items to {OUT_PATH}")
        sample_keys = list(items.keys())[:5]
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
