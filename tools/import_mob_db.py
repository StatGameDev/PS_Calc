#!/usr/bin/env python
"""
tools/import_mob_db.py

One-shot scraper: reads Hercules/db/pre-re/mob_db.conf and writes
core/data/pre-re/db/mob_db.json.

Usage:
    python tools/import_mob_db.py           # write to output path
    python tools/import_mob_db.py --dry-run # print sample, do not write

Run from the PS_Calc/ project root. No external dependencies — stdlib only.
"""
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — relative to project root (run from PS_Calc/)
# ---------------------------------------------------------------------------
CONF_PATH = Path("Hercules/db/pre-re/mob_db.conf")
OUT_PATH = Path("core/data/pre-re/db/mob_db.json")

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
    Extract all top-level { ... } entry blocks from the mob_db list.

    Uses a character-level state machine to skip:
    - /* ... */ block comments  (used for commented-out entries like /*{ ... }*/)
    - // line comments          (may contain { } characters)

    mob_db.conf does not use <" ... "> heredoc script blocks (unlike item_db.conf),
    so that special case is not needed here.
    """
    entries: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        # Skip /* ... */ block comment at top level
        if text[i] == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i < n:
                if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    i += 2
                    break
                i += 1
            continue

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
                # Skip /* ... */ inside entry
                if text[i] == "/" and i + 1 < n and text[i + 1] == "*":
                    i += 2
                    while i < n:
                        if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                            i += 2
                            break
                        i += 1
                    continue
                # Skip // comment inside entry
                if text[i] == "/" and i + 1 < n and text[i + 1] == "/":
                    while i < n and text[i] != "\n":
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


def parse_entry(entry: str) -> dict | None:
    """
    Parse a single mob entry block. Returns a populated dict or None on parse failure.

    Fields extracted:
      id, sprite_name, name, level, hp, def_, mdef, vit,
      atk_min, atk_max, size, race, element, element_level, is_boss
    """
    # --- Mandatory: Id ---
    id_match = re.search(r"\bId:\s*(\d+)", entry)
    if not id_match:
        return None
    mob_id = int(id_match.group(1))

    # --- SpriteName ---
    sprite_match = re.search(r'SpriteName:\s*"([^"]+)"', entry)
    sprite_name = sprite_match.group(1) if sprite_match else ""

    # --- Name ---
    name_match = re.search(r'\bName:\s*"([^"]+)"', entry)
    name = name_match.group(1) if name_match else ""

    # --- Lv (default 1) ---
    lv_match = re.search(r"\bLv:\s*(\d+)", entry)
    level = int(lv_match.group(1)) if lv_match else 1

    # --- Hp (default 1) ---
    hp_match = re.search(r"\bHp:\s*(\d+)", entry)
    hp = int(hp_match.group(1)) if hp_match else 1

    # --- Def (default 0) ---
    def_match = re.search(r"\bDef:\s*(\d+)", entry)
    def_ = int(def_match.group(1)) if def_match else 0

    # --- Mdef (default 0) ---
    mdef_match = re.search(r"\bMdef:\s*(\d+)", entry)
    mdef = int(mdef_match.group(1)) if mdef_match else 0

    # --- Stats.Vit (default 0) ---
    # Use re.DOTALL to span the Stats: { ... } block
    vit_match = re.search(r"Stats:\s*\{[^}]*?Vit:\s*(\d+)", entry, re.DOTALL)
    vit = int(vit_match.group(1)) if vit_match else 0

    # --- Attack: [min, max] (default [0, 0]) ---
    atk_match = re.search(r"Attack:\s*\[(\d+),\s*(\d+)\]", entry)
    atk_min = int(atk_match.group(1)) if atk_match else 0
    atk_max = int(atk_match.group(2)) if atk_match else 0

    # --- Size: "Size_X" (default Small per Hercules schema) ---
    size_match = re.search(r'Size:\s*"Size_(\w+)"', entry)
    size = size_match.group(1) if size_match else "Small"

    # --- Race: "RC_X" (default Formless per Hercules schema) ---
    race_match = re.search(r'Race:\s*"RC_(\w+)"', entry)
    race = race_match.group(1) if race_match else "Formless"

    # --- Element: ("Ele_X", level) (default Neutral/1) ---
    ele_match = re.search(r'Element:\s*\("Ele_(\w+)",\s*(\d+)\)', entry)
    if ele_match:
        ele_name = ele_match.group(1)
        ele_level = int(ele_match.group(2))
        element = ELEMENT_MAP.get(ele_name, 0)
        # Clamp element level: level 0 is invalid for attr_fix table (levels 1-4).
        # A handful of entries in pre-re mob_db use level 0 — treat as 1.
        element_level = max(1, ele_level)
    else:
        element = 0        # Neutral
        element_level = 1

    # --- Mode.Boss (default false) ---
    # Use re.DOTALL to span the Mode: { ... } block
    boss_match = re.search(r"Mode:\s*\{[^}]*?Boss:\s*true", entry, re.DOTALL)
    is_boss = boss_match is not None

    return {
        "id":            mob_id,
        "sprite_name":   sprite_name,
        "name":          name,
        "level":         level,
        "hp":            hp,
        "def_":          def_,
        "mdef":          mdef,
        "vit":           vit,
        "atk_min":       atk_min,
        "atk_max":       atk_max,
        "size":          size,
        "race":          race,
        "element":       element,
        "element_level": element_level,
        "is_boss":       is_boss,
    }


def main(dry_run: bool = False) -> None:
    if not CONF_PATH.exists():
        sys.exit(f"ERROR: {CONF_PATH} not found. Run from PS_Calc/ root.")

    print(f"Reading {CONF_PATH} ...")
    text = CONF_PATH.read_text(encoding="utf-8")

    print("Extracting entry blocks ...")
    entries = extract_entries(text)
    print(f"  Total blocks found: {len(entries)}")

    mobs: dict[str, dict] = {}
    failed = 0

    for entry in entries:
        result = parse_entry(entry)
        if result is None:
            failed += 1
            print(f"WARNING: Failed to parse entry block (no Id?): {entry[:80]!r}", file=sys.stderr)
        else:
            mobs[str(result["id"])] = result

    print(f"  Mob entries parsed: {len(mobs)}")
    if failed:
        print(f"  Failed to parse: {failed}", file=sys.stderr)

    # Sanity check — update this constant after the first successful run.
    # Source count: grep -c "^	Id:" Hercules/db/pre-re/mob_db.conf (includes commented entries)
    # Actual uncommented count is determined by the scraper itself.
    EXPECTED_MOB_COUNT = 1007  # verified: 1084 tab-indented Id: lines minus ~77 commented-out entries
    if len(mobs) != EXPECTED_MOB_COUNT:
        print(
            f"WARNING: Expected {EXPECTED_MOB_COUNT} mobs, got {len(mobs)}. "
            "Update EXPECTED_MOB_COUNT in scraper after verifying output.",
            file=sys.stderr,
        )

    output = {
        "_source": "Scraped from Hercules/db/pre-re/mob_db.conf",
        "_note": (
            "All fields needed for pipeline (def_, vit, size, race, element, element_level, "
            "is_boss, level) plus display fields (hp, mdef, atk_min, atk_max, sprite_name, name). "
            "element_level 0 clamped to 1 (invalid for attr_fix table). "
            "Commented-out entries (/* ... */) are excluded."
        ),
        "mobs": mobs,
    }

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(mobs)} mobs to {OUT_PATH}")
        sample_keys = list(mobs.keys())[:5]
        for k in sample_keys:
            print(f"  {k}: {mobs[k]}")
        return

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nWrote {len(mobs)} mobs to {OUT_PATH}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
