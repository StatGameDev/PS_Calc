import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from core.config import BattleConfig
from gui.app_config import AppConfig
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.skill import SkillInstance
from core.models.target import Target
from core.models.damage import DamageResult
from core.calculators.status_calculator import StatusCalculator
from core.calculators.battle_pipeline import BattlePipeline
from core.data_loader import loader
from core.build_manager import BuildManager

SAVES_DIR = "saves"
_DEFAULT_SKILL = SkillInstance(id=5, level=10)  # SM_BASH Lv10 — placeholder until skill selector is built


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RO Pre-Renewal Damage Calculator — Hercules Accurate")
        self.geometry("1250x900")

        # Two clearly separated configs
        self.battle_config = BattleConfig()   # mechanics only
        self.app_config = AppConfig()         # UI only

        # Theme applied once at startup (best practice)
        self.set_theme(self.app_config.appearance_mode, self.app_config.color_theme)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        for name in ["Character", "Weapon", "Skill", "Target", "Results"]:
            self.tabview.add(name)
            if name != "Results":
                ctk.CTkLabel(self.tabview.tab(name),
                             text=f"📋 {name} Tab (inputs coming in later phases)",
                             font=("", 18)).pack(pady=40)

        # === RESULTS TAB ===
        results_tab = self.tabview.tab("Results")

        btn_frame = ctk.CTkFrame(results_tab)
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(btn_frame, text="Build:").pack(side="left", padx=(5, 2))

        self._build_names = self._scan_builds()
        self._build_var = ctk.StringVar(value=self._build_names[0] if self._build_names else "")
        self._build_menu = ctk.CTkOptionMenu(
            btn_frame,
            variable=self._build_var,
            values=self._build_names if self._build_names else ["(no builds found)"],
            width=220,
        )
        self._build_menu.pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="Refresh", command=self._refresh_builds,
                      width=80).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Run", command=self._run_build,
                      width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Toggle Theme",
                      command=self.toggle_theme, width=140,
                      fg_color="#1f538d", hover_color="#14375f").pack(side="left", padx=5)

        self.tree_frame = ctk.CTkFrame(results_tab)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(self.tree_frame,
                                 columns=("value", "modifier", "note", "formula", "hercules_ref"),
                                 show="tree headings",
                                 height=28)
        self.tree.heading("#0", text="Step / Section")
        self.tree.heading("value", text="Min / Avg / Max")
        self.tree.heading("modifier", text="Modifier")
        self.tree.heading("note", text="Note / Details")
        self.tree.heading("formula", text="Formula")
        self.tree.heading("hercules_ref", text="Hercules Ref")

        self.tree.column("#0", width=380, stretch=True)
        self.tree.column("value", width=180, stretch=True, anchor="center")
        self.tree.column("modifier", width=90, stretch=True, anchor="center")
        self.tree.column("note", width=260, stretch=True)
        self.tree.column("formula", width=320, stretch=True)
        self.tree.column("hercules_ref", width=520, stretch=True)

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.status_label = ctk.CTkLabel(results_tab, text="", font=("", 13), justify="left")
        self.status_label.pack(pady=8, padx=20, fill="x")

    # ------------------------------------------------------------------
    # Build list helpers
    # ------------------------------------------------------------------
    def _scan_builds(self) -> list[str]:
        names = BuildManager.list_builds(SAVES_DIR)
        return sorted(names) if names else []

    def _refresh_builds(self):
        names = self._scan_builds()
        self._build_names = names
        self._build_menu.configure(values=names if names else ["(no builds found)"])
        if names:
            self._build_var.set(names[0])

    # ------------------------------------------------------------------
    # Run selected build
    # ------------------------------------------------------------------
    def _run_build(self):
        name = self._build_var.get()
        if not name or name == "(no builds found)":
            self.status_label.configure(text="No build selected.")
            return

        path = f"{SAVES_DIR}/{name}.json"
        try:
            build = BuildManager.load_build(path)
        except Exception as exc:
            self.status_label.configure(text=f"Failed to load build: {exc}")
            return

        item_id = build.equipped.get("right_hand")
        refine  = build.refine_levels.get("right_hand", 0)
        weapon  = BuildManager.resolve_weapon(item_id, refine, build.weapon_element)

        if build.target_mob_id is not None:
            target = loader.get_monster(build.target_mob_id)
        else:
            target = Target()  # neutral default — no target configured

        skill = _DEFAULT_SKILL
        status = StatusCalculator(self.battle_config).calculate(build, weapon)
        result = BattlePipeline(self.battle_config).calculate(status, weapon, skill, target, build)
        skill_data = loader.get_skill(skill.id) or {"name": f"Skill {skill.id}", "note": ""}

        mob_info = ""
        if build.target_mob_id is not None:
            mob_entry = loader.get_monster_data(build.target_mob_id)
            if mob_entry:
                mob_info = f"  |  Target: {mob_entry['name']} (ID {build.target_mob_id})"

        pure_batk = status.batk - build.bonus_batk
        self.status_label.configure(
            text=(
                f"Build: {build.name}{mob_info}\n"
                f"BATK {status.batk}  (pure {pure_batk} + bonus {build.bonus_batk})  |  "
                f"Hard DEF {status.def_}  |  Soft DEF {status.def2}  |  "
                f"CRI {status.cri / 10:.1f}%  |  HIT {status.hit}  |  FLEE {status.flee}"
            )
        )

        self.clear_tree()
        self._populate_tree(build, status, weapon, skill, skill_data, target, result)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def set_theme(self, appearance: str, color_theme: str):
        """Central theme switcher — called once at startup + on toggle."""
        ctk.set_appearance_mode(appearance)
        ctk.set_default_color_theme(color_theme)
        self.apply_treeview_style(appearance)
        self.update_idletasks()  # force immediate redraw

    def apply_treeview_style(self, appearance: str):
        style = ttk.Style()
        style.theme_use("default")

        if appearance.lower() == "dark":
            bg = "#2a2d2e"
            fg = "#ffffff"
            heading_bg = "#1f2329"
            selected_bg = "#22559b"
        else:
            bg = "#f0f0f0"
            fg = "#000000"
            heading_bg = "#e0e0e0"
            selected_bg = "#0078d4"

        style.configure("Treeview",
                        background=bg,
                        foreground=fg,
                        fieldbackground=bg,
                        rowheight=65)
        style.configure("Treeview.Heading",
                        background=heading_bg,
                        foreground=fg)
        style.map("Treeview",
                  background=[("selected", selected_bg)],
                  foreground=[("selected", "#ffffff")])

    def toggle_theme(self):
        """Now correctly toggles between dark and light."""
        current = ctk.get_appearance_mode().lower()
        new_mode = "light" if current == "dark" else "dark"
        self.set_theme(new_mode, self.app_config.color_theme)
        self.app_config.appearance_mode = new_mode

    def clear_tree(self):
        """Clear before re-populating — prevents duplicate rows on repeated tests."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _populate_tree(self, build: PlayerBuild, status: StatusData, weapon: Weapon,
                       skill: SkillInstance, skill_data: dict, target: Target, result: DamageResult):
        """Exact 5-section hierarchy mirroring future battle_calc_weapon_attack order."""

        # 1. RAW INPUTS
        inputs_id = self.tree.insert("", tk.END, text="=== RAW INPUTS FROM JSON FILES ===", open=True)
        self.tree.insert(inputs_id, tk.END, text="bonus_batk", values=(build.bonus_batk, "", "← gear/cards/foods/SC bonus"))
        self.tree.insert(inputs_id, tk.END, text="base_str / bonus_str", values=(f"{build.base_str} / {build.bonus_str}", "", ""))
        self.tree.insert(inputs_id, tk.END, text="equip_def (raw)", values=(build.equip_def, "", "Hard DEF before clamp"))
        self.tree.insert(inputs_id, tk.END, text="base_vit", values=(build.base_vit, "", ""))
        item_id = build.equipped.get("right_hand")
        weapon_label = f"Weapon — {weapon.aegis_name}" if weapon.aegis_name else "Weapon (Unarmed)"
        weapon_details = (f"ID {item_id}  ·  ATK {weapon.atk}  ·  Lv{weapon.level}"
                          f"  ·  {weapon.weapon_type}"
                          + ("" if weapon.refineable else "  ·  NOT refineable"))
        self.tree.insert(inputs_id, tk.END, text=weapon_label,
                         values=(weapon_details, f"+{weapon.refine}", ""))

        # 2. STATUS
        status_id = self.tree.insert("", tk.END, text="=== STATUS CALCULATOR (status_calc_pc / status_calc_misc) ===", open=True)
        pure_batk = status.batk - build.bonus_batk
        self.tree.insert(status_id, tk.END, text="Pure stat BATK (STR quadratic + DEX/LUK)", values=(pure_batk, "", ""))
        self.tree.insert(status_id, tk.END, text="+ bonus_batk", values=(build.bonus_batk, "", ""))
        self.tree.insert(status_id, tk.END, text="→ Total BATK", values=(status.batk, "", ""))
        self.tree.insert(status_id, tk.END, text="Hard DEF (def1)", values=(status.def_, "", "equipment only"))
        self.tree.insert(status_id, tk.END, text="Soft DEF (vit_def)", values=(status.def2, "", "VIT + bonus_def2"))

        # 3. SKILL
        skill_id = self.tree.insert("", tk.END, text="=== SKILL FROM skills.json ===", open=True)
        self.tree.insert(skill_id, tk.END, text=f"{skill_data.get('name', 'Unknown')} (ID {skill.id}) Lv {skill.level}",
                         values=("", "", skill_data.get("note", "")))

        # 4. PIPELINE
        pipeline_id = self.tree.insert("", tk.END, text="=== BATTLE PIPELINE STEPS (battle_calc_weapon_attack) ===", open=True)
        for step in result.steps:
            mult_str = f"×{step.multiplier:.2f}" if step.multiplier != 1.0 else ""
            has_variance = step.min_value != step.max_value
            val_str = f"{step.min_value} / {step.value} / {step.max_value}" if has_variance else str(step.value)
            self.tree.insert(pipeline_id, tk.END, text=step.name, values=(
                val_str,
                mult_str,
                step.note,
                step.formula,
                step.hercules_ref
            ))

        # 5. FINAL
        final_id = self.tree.insert("", tk.END, text="=== FINAL RESULT ===", open=True)
        self.tree.insert(final_id, tk.END, text="Min / Avg / Max Damage",
                         values=(f"{result.min_damage} / {result.avg_damage} / {result.max_damage}", "", ""))

        self.tree.item(pipeline_id, open=True)
        self.tree.item(final_id, open=True)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
