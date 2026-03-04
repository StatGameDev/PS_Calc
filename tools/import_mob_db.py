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
from datetime import datetime, timezone
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


def _parse_drops_block(entry: str, block_name: str) -> list[dict]:
    """
    Parse a MvpDrops: { ... } or Drops: { ... } block into a list of
    {"item": str, "chance": int} dicts.

    Line-by-line parsing is required to handle duplicate AegisName keys
    (e.g. Poring has two 'Apple' entries). The (chance, "OptionDropGroup")
    tuple form is absent in pre-re mob_db and is not parsed.
    """
    block_match = re.search(block_name + r':\s*\{([^}]*)\}', entry, re.DOTALL)
    if not block_match:
        return []
    result: list[dict] = []
    for line in block_match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        m = re.match(r'(\w+):\s*(\d+)', line)
        if m:
            result.append({"item": m.group(1), "chance": int(m.group(2))})
    return result


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

    # --- Mode block: sparse dict (only true flags stored) + top-level is_boss ---
    _MODE_FLAGS = [
        "CanMove", "Looter", "Aggressive", "Assist", "CastSensorIdle", "Boss",
        "Plant", "CanAttack", "Detector", "CastSensorChase", "ChangeChase",
        "Angry", "ChangeTargetMelee", "ChangeTargetChase", "TargetWeak", "NoKnockback",
    ]
    mode: dict[str, bool] = {}
    mode_block_match = re.search(r"Mode:\s*\{([^}]*)\}", entry, re.DOTALL)
    if mode_block_match:
        block_text = mode_block_match.group(1)
        for flag in _MODE_FLAGS:
            if re.search(r'\b' + flag + r':\s*true', block_text):
                mode[flag] = True
    is_boss = mode.get("Boss", False)

    # --- JName (alternate display name, default "") ---
    jname_match = re.search(r'JName:\s*"([^"]+)"', entry)
    jname = jname_match.group(1) if jname_match else ""

    # --- Sp, Exp, JExp (default 0) ---
    sp_match   = re.search(r"\bSp:\s*(\d+)", entry)
    exp_match  = re.search(r"\bExp:\s*(\d+)", entry)
    jexp_match = re.search(r"\bJExp:\s*(\d+)", entry)
    sp   = int(sp_match.group(1))   if sp_match   else 0
    exp  = int(exp_match.group(1))  if exp_match  else 0
    jexp = int(jexp_match.group(1)) if jexp_match else 0

    # --- Ranges ---
    arange_match = re.search(r"\bAttackRange:\s*(\d+)", entry)
    vrange_match = re.search(r"\bViewRange:\s*(\d+)", entry)
    crange_match = re.search(r"\bChaseRange:\s*(\d+)", entry)
    attack_range = int(arange_match.group(1)) if arange_match else 1
    view_range   = int(vrange_match.group(1)) if vrange_match else 1
    chase_range  = int(crange_match.group(1)) if crange_match else 1

    # --- Remaining stats from Stats block (Str, Agi, Int, Dex, Luk) ---
    str_match = re.search(r"Stats:\s*\{[^}]*?Str:\s*(\d+)", entry, re.DOTALL)
    agi_match = re.search(r"Stats:\s*\{[^}]*?Agi:\s*(\d+)", entry, re.DOTALL)
    int_match = re.search(r"Stats:\s*\{[^}]*?Int:\s*(\d+)", entry, re.DOTALL)
    dex_match = re.search(r"Stats:\s*\{[^}]*?Dex:\s*(\d+)", entry, re.DOTALL)
    luk_match = re.search(r"Stats:\s*\{[^}]*?Luk:\s*(\d+)", entry, re.DOTALL)
    str_ = int(str_match.group(1)) if str_match else 0
    agi  = int(agi_match.group(1)) if agi_match else 0
    int_ = int(int_match.group(1)) if int_match else 0
    dex  = int(dex_match.group(1)) if dex_match else 0
    luk  = int(luk_match.group(1)) if luk_match else 0

    # --- Timing ---
    ms_match  = re.search(r"\bMoveSpeed:\s*(\d+)", entry)
    ad_match  = re.search(r"\bAttackDelay:\s*(\d+)", entry)
    am_match  = re.search(r"\bAttackMotion:\s*(\d+)", entry)
    dm_match  = re.search(r"\bDamageMotion:\s*(\d+)", entry)
    move_speed    = int(ms_match.group(1))  if ms_match  else 0
    attack_delay  = int(ad_match.group(1))  if ad_match  else 4000
    attack_motion = int(am_match.group(1))  if am_match  else 2000
    damage_motion = int(dm_match.group(1))  if dm_match  else 0

    # --- MVP ---
    mvp_exp_match = re.search(r"\bMvpExp:\s*(\d+)", entry)
    mvp_exp   = int(mvp_exp_match.group(1)) if mvp_exp_match else 0
    mvp_drops = _parse_drops_block(entry, "MvpDrops")
    drops     = _parse_drops_block(entry, "Drops")

    # --- DamageTakenRate (default 100; no actual pre-re entry uses this) ---
    dtr_match = re.search(r"\bDamageTakenRate:\s*(\d+)", entry)
    damage_taken_rate = int(dtr_match.group(1)) if dtr_match else 100

    return {
        # Pipeline fields at top level (backward compatible)
        "id":            mob_id,
        "sprite_name":   sprite_name,
        "name":          name,
        "level":         level,
        "hp":            hp,
        "def_":          def_,
        "mdef":          mdef,
        "atk_min":       atk_min,
        "atk_max":       atk_max,
        "size":          size,
        "race":          race,
        "element":       element,
        "element_level": element_level,
        "is_boss":       is_boss,       # kept at top level for DataLoader backward compat
        # Stats nested dict (mirrors conf structure; vit moved here from top level)
        "stats": {
            "str": str_,
            "agi": agi,
            "vit": vit,
            "int": int_,
            "dex": dex,
            "luk": luk,
        },
        # New display / browser fields
        "jname":             jname,
        "sp":                sp,
        "exp":               exp,
        "jexp":              jexp,
        "attack_range":      attack_range,
        "view_range":        view_range,
        "chase_range":       chase_range,
        "mode":              mode,
        "move_speed":        move_speed,
        "attack_delay":      attack_delay,
        "attack_motion":     attack_motion,
        "damage_motion":     damage_motion,
        "mvp_exp":           mvp_exp,
        "mvp_drops":         mvp_drops,
        "drops":             drops,
        "damage_taken_rate": damage_taken_rate,
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
        "_scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_note": (
            "Pipeline fields (def_, atk_min/max, size, race, element, element_level, is_boss, "
            "level, hp, mdef) at top level for backward compat. Stats in nested 'stats' dict. "
            "mode is a sparse dict (only true flags stored; absence implies false). "
            "drops/mvp_drops stored as [{item, chance}] arrays to handle duplicate AegisName keys. "
            "element_level 0 clamped to 1 (invalid for attr_fix table). "
            "Commented-out entries (/* ... */) excluded. ViewData excluded."
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
