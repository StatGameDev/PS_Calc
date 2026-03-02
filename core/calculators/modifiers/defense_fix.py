from core.models.target import Target
from core.models.damage import DamageResult
from core.models.build import PlayerBuild
from core.config import BattleConfig


class DefenseFix:
    """Exact pre-renewal defense reduction for BF_WEAPON attacks (hard DEF percentage + soft DEF subtraction) with PC vs monster branching, ignore_hard_def support, and full VIT penalty."""
    @staticmethod
    def calculate(target: Target, build: PlayerBuild, current_damage: int, config: BattleConfig, result: DamageResult) -> None:
        """VIT penalty applied to def1/def2 before reduction (exact source position)."""
        def1 = max(0, min(100, target.def_))
        if getattr(build, 'ignore_hard_def', False):
            def1 = 0
            note_def = "Hard DEF ignored"
        else:
            note_def = f"Hard DEF {def1}"

        def2 = max(1, target.vit)

        # VIT penalty (full mechanic – uses target.targeted_count, respects bitmask)
        if config.vit_penalty_type != 0 and (config.vit_penalty_target & (1 if target.is_pc else 2)) != 0:
            target_count = target.targeted_count
            if target_count >= config.vit_penalty_count:
                if getattr(target, 'active_status_levels', {}).get("SC_STEELBODY", 0) == 0:  # immunity if target has SC_STEELBODY
                    penalty = (target_count - (config.vit_penalty_count - 1)) * config.vit_penalty_num
                    if config.vit_penalty_type == 1:
                        def1 = def1 * (100 - penalty) // 100
                        def2 = def2 * (100 - penalty) // 100
                    else:
                        def1 -= penalty
                        def2 -= penalty

        after_hard = current_damage * (100 - def1) // 100

        if target.is_pc:
            # rnd()%variance_max averages (variance_max-1)/2, not variance_max/2
            # Hercules: vit_def = def2/2 + (vit_def>0 ? rnd()%vit_def : 0)
            variance_max = def2 * (def2 - 15) // 150
            avg_vit_def = def2 // 2 + ((variance_max - 1) // 2 if variance_max > 0 else 0)
            note_type = "PC"
        else:
            # rnd()%variance_max averages (variance_max-1)/2, not variance_max/2
            # Hercules: vit_def = def2 + (vit_def>0 ? rnd()%vit_def : 0)
            variance_max = (def2 // 20) * (def2 // 20)
            avg_vit_def = def2 + ((variance_max - 1) // 2 if variance_max > 0 else 0)
            note_type = "monster"

        after_def = after_hard - avg_vit_def
        final_def = max(1, after_def)

        result.add_step(
            name="Defense Fix",
            value=final_def,
            multiplier=1.0,
            note=f"{note_def} → ×{(100-def1)/100:.0%} + Soft DEF avg {avg_vit_def} ({note_type})",
            formula=f"max(1, current * (100 - def1) // 100 - avg_vit_def)",
            hercules_ref="battle.c: defType def1 = status_get_def(target); short def2 = tstatus->def2, vit_def;\n" +
                         "battle.c: if (def1 > 100) def1 = 100;\n" +
                         "battle.c: damage = damage * (100-def1) / 100;\n" +
                         "battle.c: if (!(flag & 1 || flag & 2)) damage -= vit_def;\n" +
                         "battle.c: if (tsd) { vit_def = def2 * (def2 - 15) / 150; vit_def = def2 / 2 + (vit_def > 0 ? rnd() % vit_def : 0); } else { vit_def = (def2 / 20) * (def2 / 20); vit_def = def2 + (vit_def > 0 ? rnd() % vit_def : 0); }\n" +
                         "battle.c: if (battle_config.vit_penalty_type != 0 && (battle_config.vit_penalty_target & bl->type) != 0) { int target_count = unit_counttargeted(bl); if (target_count >= battle_config.vit_penalty_count) { int penalty = ...; if (battle_config.vit_penalty_type == 1) def1 = def1 * (100-penalty)/100; def2 = def2 * (100-penalty)/100; else def1 -= penalty; def2 -= penalty; } }"
        )