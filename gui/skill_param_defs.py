"""Skill parameter descriptors for the Combat Controls section.

Each entry in SKILL_PARAM_REGISTRY declares the runtime inputs a skill needs
beyond its level — things like distance, cart weight, or sphere count.

Adding a new skill with params:
  1. Add an entry here.
  2. Add the calculation lambda to _PARAM_SKILL_RATIO_FNS in skill_ratio.py.
  Nothing else.

Field notes:
  key             Storage key written to build.skill_params.
  label           Text shown next to the widget.
  widget          "combo" | "spin" | "check"
  default         Value used on reset / new build.
  options         combo → list[(display_str, value)]
                  spin  → (min, max, step, suffix_str)
                  check → unused (None)
  mirrors_sc_key  If set: load_build() initialises the widget from
                  build.active_status_levels[mirrors_sc_key] rather than
                  build.skill_params[key]. collect_into() still reads the
                  widget — the combat widget is an independent override.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class SkillParamSpec:
    key: str
    label: str
    widget: str                  # "combo" | "spin" | "check"
    default: Any
    options: Any = None          # see module docstring
    mirrors_sc_key: Optional[str] = None
    # If set: load_build() calls this to compute the initial widget value from
    # the build rather than reading build.skill_params[key] or spec.default.
    # Signature: (build) -> Any  (duck-typed; no PlayerBuild import needed here)
    default_from_build: Optional[Callable] = None


SKILL_PARAM_REGISTRY: dict[str, list[SkillParamSpec]] = {
    # MO_FINGEROFFENSIVE — sphere count at cast time.
    # Initialised from Self Buffs (MO_SPIRITBALL) but independently overrideable.
    # default_from_build mirrors the Self Buffs sphere count, falling back to the
    # Call Spirits mastery level as a proxy for max spheres when MO_SPIRITBALL is unset.
    "MO_FINGEROFFENSIVE": [
        SkillParamSpec(
            key="MO_FINGEROFFENSIVE_spheres",
            label="Spirit Spheres:",
            widget="combo",
            default=1,
            options=[(str(n), n) for n in range(1, 6)],
            mirrors_sc_key="MO_SPIRITBALL",
            default_from_build=lambda b: b.active_status_levels.get(
                "MO_SPIRITBALL", b.mastery_levels.get("MO_CALLSPIRITS", 1)
            ),
        ),
    ],

    # KN_CHARGEATK — cell distance tier selects the ratio multiplier.
    "KN_CHARGEATK": [
        SkillParamSpec(
            key="KN_CHARGEATK_dist",
            label="Distance:",
            widget="combo",
            default=1,
            options=[
                ("1–3 tiles  (×100%)", 1),
                ("4–6 tiles  (×200%)", 4),
                ("7+ tiles   (×300%)", 7),
            ],
        ),
    ],

    # MC_CARTREVOLUTION — cart weight % feeds the ratio formula.
    "MC_CARTREVOLUTION": [
        SkillParamSpec(
            key="MC_CARTREVOLUTION_pct",
            label="Cart weight:",
            widget="spin",
            default=0,
            options=(0, 100, 10, " %"),
        ),
    ],

    # MO_EXTREMITYFIST — current SP at cast time feeds the ratio formula.
    "MO_EXTREMITYFIST": [
        SkillParamSpec(
            key="MO_EXTREMITYFIST_sp",
            label="Current SP:",
            widget="spin",
            default=0,
            options=(0, 9999, 1, ""),
        ),
    ],

    # TK_JUMPKICK — two boolean toggles affect ratio (combo) and a ×2 multiplier (running).
    "TK_JUMPKICK": [
        SkillParamSpec(
            key="TK_JUMPKICK_combo",
            label="Combo Attack",
            widget="check",
            default=False,
        ),
        SkillParamSpec(
            key="TK_JUMPKICK_running",
            label="Running (TK_RUN)",
            widget="check",
            default=False,
        ),
    ],
}
