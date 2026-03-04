#!/usr/bin/env python3
"""tools/import_rocalc_saves.py  (v2)

Convert rocalc localStorage saves to PS_Calc build JSON files.

Uses the confirmed save format from rocalc's SaveLocal() in foot_2025-08-10.js.
Resolves equipment by:
  1. Looking up m_Item array indices from rocalc_files/item_2025-08-10.js
  2. Cross-referencing item names against Hercules item_db.json by name
  3. Reporting card names from rocalc_files/card_2025-08-10.js

Confirmed field map (array version 2):
  [0]  = 2 (format version)
  [1]  = character name (string)
  [2]  = rocalc job ID
  [3]  = job level
  [4]  = base level
  [5]  = adopted flag
  [6]  = base STR
  [7]  = base AGI
  [8]  = base VIT
  [9]  = base DEX
  [10] = base INT
  [11] = base LUK
  [12] = weapon element (0=no override; 1-9=element; >9=endow/buff, treat as null)
  [13] = weapon1 saved subtype (m_Item[weapon1][1] at save time)
  [14] = weapon1 m_Item index
  [15] = weapon1 refine level
  [16..19] = weapon1 card m_Card indices (4 slots)
  [20] = weapon2 saved subtype (dual-wield only)
  [21] = weapon2 m_Item index (0 if no dual-wield)
  [22] = weapon2 refine
  [23..26] = weapon2 card m_Card indices
  [27] = ammo m_Item index
  [28] = head_upper m_Item index
  [29] = head_upper card m_Card index
  [30] = head_upper refine
  [31] = head_mid m_Item index
  [32] = head_mid card m_Card index
  [33] = head_lower m_Item index  (no card, no refine)
  [34] = shield m_Item index
  [35] = shield card m_Card index
  [36] = shield refine
  [37] = armor m_Item index
  [38] = armor card m_Card index
  [39] = armor refine
  [40] = garment m_Item index
  [41] = garment card m_Card index
  [42] = garment refine
  [43] = footwear m_Item index
  [44] = footwear card m_Card index
  [45] = footwear refine
  [46] = accessory1 m_Item index
  [47] = accessory1 card m_Card index
  [48] = accessory2 m_Item index
  [49] = accessory2 card m_Card index
"""

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Raw rocalc localStorage data — one JSON array string per slot
# ---------------------------------------------------------------------------
SAVES = {
    "Slotnum00": '[2,"AK77 Hunter",10,50,99,0,1,77,4,56,6,10,95,10,31,1,1,1,0,0,0,0,0,0,0,0,0,0,15,155,0,4,259,0,1418,305,0,0,291,183,4,315,78,4,318,0,4,338,395,721,0,0,0,0,0,0,10,10,10,10,5,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,35,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"33","0","0","0",0,0,0,1,0,"175",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,20,0,23,0,0,0,10,0,20,0,23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"0","0",10,null,false,true,false,false,false,false,"0","10",0,0,0,0]',
    "Slotnum01": '[2,"DD Sin",8,50,99,0,99,80,3,52,2,1,0,1,9,7,3,3,3,0,1,3,10,1,1,1,1,0,661,0,4,385,0,1523,305,0,0,294,183,4,522,267,6,321,304,9,341,101,341,101,0,0,0,0,10,10,5,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,29,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"33","1","0","0",0,0,0,1,0,"43",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,20,0,23,0,0,0,10,0,20,0,23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"0","0",10,null,false,true,false,false,false,false,"0","10",0,0,0,0]',
    "Slotnum02": '[2,"Nat Crit Sin",8,50,99,0,80,99,6,22,8,40,0,11,480,9,156,328,233,287,0,0,0,0,0,0,0,0,155,0,4,385,0,1418,305,0,0,294,183,4,312,402,9,781,89,4,338,103,338,103,0,0,0,0,10,10,0,0,10,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,45,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"33","1","0","0",0,0,0,1,0,"455",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,20,0,23,0,0,0,10,0,20,0,23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"0","0",10,null,false,true,false,false,false,false,"0","10",0,0,0,0]',
    "Slotnum03": '[2,"Agi BS",12,50,99,0,96,91,7,38,1,1,2,7,67,7,31,31,0,0,0,0,0,0,0,0,0,0,1300,0,4,267,0,268,305,0,0,301,133,7,312,403,9,324,129,8,329,487,329,487,0,0,0,0,10,1,1,10,5,1,5,5,0,0,0,0,0,0,0,0,0,0,0,10,10,5,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,29,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"20","1","0","0",0,0,65,10,0,"399",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,20,0,23,0,0,0,10,0,20,0,23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"0","0",10,null,false,true,false,false,false,false,"0","10",0,0,0,0]',
    "Slotnum04": '[2,"Combo Monk",15,50,99,0,93,84,4,50,18,1,1,13,123,10,14,14,30,30,0,0,0,0,0,0,0,0,661,0,4,385,0,1049,691,154,4,295,136,7,522,267,6,323,0,7,341,101,725,0,0,0,0,0,5,10,10,7,10,5,0,0,0,0,0,0,0,0,0,0,0,0,0,10,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,29,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"20","1","0","0",0,0,0,1,0,"79",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,20,0,23,0,0,0,10,0,20,0,23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"0","0",10,null,false,true,false,false,false,false,"0","10",0,0,0,0]',
    "Slotnum05": '[2,"IP Rogue",14,50,99,0,75,97,2,62,1,1,3,1,388,4,0,0,0,0,0,0,0,0,0,0,0,0,155,0,4,385,0,270,308,154,4,288,0,7,699,0,7,321,228,9,338,101,338,101,0,0,0,0,10,10,10,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"20","1","0","0",0,0,0,1,0,"282",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,0,20,0,23,0,0,0,10,0,20,0,23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,10,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,"0","0",10,null,false,true,false,false,false,false,"0","10",0,0,0,0]',
}

# ---------------------------------------------------------------------------
# Job ID mapping: rocalc → Hercules
# ---------------------------------------------------------------------------
ROCALC_TO_HERCULES_JOB = {
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7,
    8: 12,   # Assassin  → JOB_ASSASSIN = 12
    10: 11,  # Hunter    → JOB_HUNTER   = 11
    12: 10,  # Blacksmith→ JOB_BLACKSMITH= 10
    14: 17,  # Rogue     → JOB_ROGUE    = 17
    15: 15,  # Monk      → JOB_MONK     = 15
}

JOB_NAMES = {
    0: "Novice", 1: "Swordsman", 2: "Mage", 3: "Archer", 4: "Acolyte",
    5: "Merchant", 6: "Thief", 7: "Knight", 8: "Priest", 9: "Wizard",
    10: "Blacksmith", 11: "Hunter", 12: "Assassin", 14: "Crusader",
    15: "Monk", 16: "Sage", 17: "Rogue", 18: "Alchemist",
}

# m_Item indices that represent "no item" in a slot
NO_ITEM = {0, 268, 279, 305, 311, 317, 326}

# rocalc weapon subtype → readable label
WTYPE_LABEL = {
    1: "Dagger", 2: "1HSword", 3: "2HSword", 4: "1HAxe", 5: "2HAxe",
    6: "Mace", 7: "2HAxeMace", 8: "Rod", 9: "2HStaff", 10: "Bow",
    11: "Katar", 12: "Katar2", 13: "Knuckle", 14: "Musical", 15: "Whip", 16: "Book",
}

# Expected m_Item subtype for each armor slot (for version-mismatch detection)
SLOT_SUBTYPE = {
    "head_upper": 50, "head_mid": 51, "head_lower": 52,
    "armor": 60, "shield": 61, "garment": 62,
    "footwear": 63, "accessory1": 64, "accessory2": 64,
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def parse_js_array(filepath: str, var_name: str) -> dict:
    """Parse a JS array variable into {entry[0]: entry} dict.

    Strips trailing // comments by cutting at the last ']' on each line.
    Skips lines that fail to parse (multiline strings, etc.).
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    m = re.search(rf"{re.escape(var_name)}\s*=\s*\[", content)
    if not m:
        raise ValueError(f"{var_name} not found in {filepath}")
    result = {}
    for line in content[m.end():].split("\n"):
        s = line.strip().lstrip(",")
        if s.startswith("]"):
            break
        if not s.startswith("["):
            continue
        end = s.rfind("]")
        if end == -1:
            continue
        try:
            entry = json.loads(s[: end + 1])
            if isinstance(entry, list) and len(entry) > 0:
                result[entry[0]] = entry
        except json.JSONDecodeError:
            pass
    return result


def load_item_db(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw["items"].items()}


def item_name(m_item: dict, idx) -> str | None:
    """Get item name from m_Item. Returns None if idx is a sentinel or not found."""
    if not isinstance(idx, int) or idx in NO_ITEM:
        return None
    e = m_item.get(idx)
    if not e or len(e) <= 8:
        return None
    n = e[8]
    if isinstance(n, str) and n.startswith("(no "):
        return None
    return n if isinstance(n, str) else None


def item_subtype(m_item: dict, idx) -> int | None:
    """Get m_Item subtype (weapon category or armor slot type). None if not found."""
    if not isinstance(idx, int):
        return None
    e = m_item.get(idx)
    return e[1] if e and len(e) > 1 and isinstance(e[1], int) else None


def get_card_name(m_card: dict, idx) -> str | None:
    """Get card name from m_Card. Returns None for 0/missing, fallback label otherwise."""
    if not isinstance(idx, int) or idx <= 0:
        return None
    e = m_card.get(idx)
    if not e or len(e) < 3:
        return f"rocalc_card_{idx}"
    return e[2] if isinstance(e[2], str) else f"rocalc_card_{idx}"


def resolve(name: str | None, lookup: dict) -> int | None:
    """Look up Hercules item ID by name (case-insensitive). Returns None on miss."""
    if not name:
        return None
    return lookup.get(name.lower())


def decode_char(slot_name: str, arr: list, m_item: dict, m_card: dict, lookup: dict) -> tuple:
    """Parse one rocalc array → (build_dict, summary_row)."""
    name = arr[1]
    rocalc_job = arr[2]
    job_level = arr[3]
    base_level = arr[4]
    str_ = arr[6]; agi = arr[7]; vit = arr[8]
    dex = arr[9];  int_ = arr[10]; luk = arr[11]

    herc_job = ROCALC_TO_HERCULES_JOB.get(rocalc_job, rocalc_job)
    job_label = JOB_NAMES.get(herc_job, f"job{rocalc_job}")

    # ---- Weapon 1 ----
    elem_raw = arr[12]
    w1_saved_type = arr[13]
    w1_idx = arr[14]
    w1_refine = arr[15]
    w1_cards = [get_card_name(m_card, arr[i]) for i in range(16, 20)
                if isinstance(arr[i], int) and arr[i] > 0]
    w1_name = item_name(m_item, w1_idx)
    w1_actual_type = item_subtype(m_item, w1_idx)
    w1_type_ok = w1_actual_type is None or w1_actual_type == w1_saved_type
    w1_id = resolve(w1_name, lookup)
    weapon_element = elem_raw if isinstance(elem_raw, int) and 1 <= elem_raw <= 9 else None

    # ---- Weapon 2 (dual-wield) ----
    w2_idx = arr[21]
    has_w2 = isinstance(w2_idx, int) and w2_idx not in NO_ITEM
    w2_id = w2_refine = w2_name = w2_cards = w2_saved_type = None
    w2_type_ok = True
    if has_w2:
        w2_saved_type = arr[20]
        w2_refine = arr[22]
        w2_cards = [get_card_name(m_card, arr[i]) for i in range(23, 27)
                    if isinstance(arr[i], int) and arr[i] > 0]
        w2_name = item_name(m_item, w2_idx)
        w2_actual_type = item_subtype(m_item, w2_idx)
        w2_type_ok = w2_actual_type is None or w2_actual_type == w2_saved_type
        w2_id = resolve(w2_name, lookup)

    # ---- Ammo ----
    ammo_name = item_name(m_item, arr[27])
    ammo_id = resolve(ammo_name, lookup)

    # ---- Armor slots: (slot_name, item_pos, card_pos, refine_pos) ----
    ARMOR_LAYOUT = [
        ("head_upper", 28, 29, 30),
        ("head_mid",   31, 32, None),
        ("head_lower", 33, None, None),
        ("shield",     34, 35, 36),
        ("armor",      37, 38, 39),
        ("garment",    40, 41, 42),
        ("footwear",   43, 44, 45),
        ("accessory1", 46, 47, None),
        ("accessory2", 48, 49, None),
    ]
    slots = {}
    for sname, ipos, cpos, rpos in ARMOR_LAYOUT:
        idx = arr[ipos] if ipos < len(arr) else 0
        s_name = item_name(m_item, idx)
        actual_st = item_subtype(m_item, idx)
        type_ok = actual_st is None or actual_st == SLOT_SUBTYPE.get(sname)
        cval = arr[cpos] if cpos is not None and cpos < len(arr) else 0
        slots[sname] = {
            "rocalc_idx": idx,
            "name": s_name,
            "id": resolve(s_name, lookup),
            "refine": arr[rpos] if rpos is not None and rpos < len(arr) else 0,
            "card": get_card_name(m_card, cval),
            "type_ok": type_ok,
        }

    # ---- Assemble equipped / refine dicts ----
    equipped = {
        "right_hand": w1_id,
        "left_hand":  w2_id if has_w2 else None,
        "ammo":       ammo_id,
    }
    for sname, sd in slots.items():
        equipped[sname] = sd["id"]

    refine_d = {"right_hand": w1_refine}
    if has_w2:
        refine_d["left_hand"] = w2_refine
    for sname, sd in slots.items():
        if sd["refine"]:
            refine_d[sname] = sd["refine"]

    # ---- _import_notes ----
    notes = {}

    def weapon_note(slot, wname, wtype_code, wrefine, wcards, widx, type_ok, wid):
        if not wname:
            return
        n = {
            "rocalc_name": wname,
            "rocalc_idx": widx,
            "type": WTYPE_LABEL.get(wtype_code, f"type{wtype_code}"),
            "refine": wrefine,
        }
        if wcards:
            n["cards"] = wcards
        if not type_ok:
            n["warning"] = "item DB version drift — weapon type is reliable, item name may not be"
        if wid is None:
            n["status"] = "unresolved"
        notes[slot] = n

    weapon_note("right_hand", w1_name, w1_saved_type, w1_refine, w1_cards, w1_idx, w1_type_ok, w1_id)
    if has_w2:
        weapon_note("left_hand", w2_name, w2_saved_type, w2_refine, w2_cards, w2_idx, w2_type_ok, w2_id)

    for sname, sd in slots.items():
        if not sd["name"]:
            continue
        n = {"rocalc_name": sd["name"], "rocalc_idx": sd["rocalc_idx"]}
        if sd["refine"]:
            n["refine"] = sd["refine"]
        if sd["card"]:
            n["card"] = sd["card"]
        if not sd["type_ok"]:
            n["warning"] = "item DB version drift — slot type mismatch; name may not be reliable"
        if sd["id"] is None:
            n["status"] = "unresolved"
        notes[sname] = n

    # ---- _todo: items that need manual resolution ----
    todo = []
    if w1_name and w1_id is None:
        todo.append({
            "slot": "right_hand",
            "rocalc_name": w1_name,
            "rocalc_idx": w1_idx,
            "type": WTYPE_LABEL.get(w1_saved_type, f"type{w1_saved_type}"),
            "note": "type mismatch — verify item name" if not w1_type_ok
                    else "name not in Hercules item_db",
        })
    if has_w2 and w2_name and w2_id is None:
        todo.append({
            "slot": "left_hand",
            "rocalc_name": w2_name,
            "rocalc_idx": w2_idx,
            "note": "name not in Hercules item_db",
        })
    for sname, sd in slots.items():
        if sd["name"] and sd["id"] is None:
            todo.append({
                "slot": sname,
                "rocalc_name": sd["name"],
                "rocalc_idx": sd["rocalc_idx"],
                "note": "item DB version drift — verify item name" if not sd["type_ok"]
                        else "name not in Hercules item_db",
            })

    build = {
        "_import": (
            f"Imported from rocalc localStorage {slot_name}. "
            "base_stats are accurate. Equipment cross-referenced by name "
            "against Hercules item_db — see _import_notes and _todo."
        ),
        "_rocalc_job_id": rocalc_job,
        "name": name,
        "job_id": herc_job,
        "base_level": base_level,
        "job_level": job_level,
        "base_stats": {
            "str": str_, "agi": agi, "vit": vit,
            "int": int_, "dex": dex, "luk": luk,
        },
        "bonus_stats": {
            "str": 0, "agi": 0, "vit": 0, "int": 0,
            "dex": 0, "luk": 0, "hit": 0, "flee": 0, "cri": 0, "batk": 0,
        },
        "target_mob_id": None,
        "equipped": equipped,
        "refine": refine_d,
        "weapon_element": weapon_element,
        "active_buffs": {},
        "mastery_levels": {},
        "flags": {
            "is_ranged_override": None,
            "is_riding_peco": False,
            "no_sizefix": False,
        },
        "_import_notes": notes,
    }
    if todo:
        build["_todo"] = todo

    # Summary row
    n_filled = (1 if w1_name else 0) + (1 if has_w2 and w2_name else 0) + \
               sum(1 for sd in slots.values() if sd["name"])
    n_unresolved = len(todo)
    summary = [
        slot_name, name, job_label, f"Lv{base_level}/{job_level}",
        f"STR{str_}/AGI{agi}/VIT{vit}/INT{int_}/DEX{dex}/LUK{luk}",
        f"{n_filled - n_unresolved} matched, {n_unresolved} unresolved",
    ]
    return build, summary


def main():
    root = Path(__file__).parent.parent
    rocalc_dir = root / "rocalc_files"
    item_db_path = root / "core" / "data" / "pre-re" / "db" / "item_db.json"
    saves_dir = root / "saves"

    print(f"Parsing rocalc files from {rocalc_dir} ...")
    m_item = parse_js_array(str(rocalc_dir / "item_2025-08-10.js"), "m_Item")
    m_card = parse_js_array(str(rocalc_dir / "card_2025-08-10.js"), "m_Card")
    print(f"  m_Item: {len(m_item)} entries,  m_Card: {len(m_card)} entries")

    print(f"Loading Hercules item_db ...")
    item_db = load_item_db(str(item_db_path))
    lookup = {v["name"].lower(): k for k, v in item_db.items() if "name" in v}
    print(f"  {len(item_db)} items, {len(lookup)} name entries\n")

    summaries = []
    for slot_name, raw in SAVES.items():
        arr = json.loads(raw)
        build, summary = decode_char(slot_name, arr, m_item, m_card, lookup)

        filename = slug(arr[1]) + ".json"
        out = saves_dir / filename
        with open(out, "w", encoding="utf-8") as f:
            json.dump(build, f, indent=2, ensure_ascii=False)
        print(f"  [{slot_name}] {arr[1]}  ->  saves/{filename}")

        for sname, info in build.get("_import_notes", {}).items():
            ok = "status" not in info
            sym = "+" if ok else "!"
            warn = " [MISMATCH]" if "warning" in info else ""
            rname = info.get("rocalc_name", "?")
            refine_str = f" +{info['refine']}" if info.get("refine") else ""
            cards = info.get("cards") or ([info["card"]] if "card" in info else [])
            card_str = f" [{', '.join(str(c) for c in cards)}]" if cards else ""
            print(f"    [{sym}] {sname:<12} {rname}{refine_str}{card_str}{warn}")
        print()

        summaries.append(summary)

    # Summary table
    header = ["Slot", "Name", "Class", "Level", "Stats", "Equipment"]
    widths = [max(len(header[i]), max(len(r[i]) for r in summaries)) + 2
              for i in range(len(header))]
    sep = "=" * sum(widths)
    fmt = "".join(f"{{:<{w}}}" for w in widths)
    print(f"\n{sep}\nIMPORT SUMMARY\n{sep}")
    print(fmt.format(*header))
    print("-" * sum(widths))
    for r in summaries:
        print(fmt.format(*r))
    print(sep)


if __name__ == "__main__":
    main()
