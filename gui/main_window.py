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

        ctk.CTkButton(btn_frame, text="Test Status Calculator (Phase 1)",
                      command=self.test_status, width=280).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Test LK Bash",
                      command=self.test_pipeline, width=280).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Test Spear Peco",
                      command=self.test_spear_peco, width=280).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Toggle Theme (Groundwork Test)",
                      command=self.toggle_theme, width=280,
                      fg_color="#1f538d", hover_color="#14375f").pack(side="left", padx=5)

        self.tree_frame = ctk.CTkFrame(results_tab)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(self.tree_frame,
                                 columns=("value", "modifier", "note", "formula", "hercules_ref"),
                                 show="tree headings",
                                 height=28)
        self.tree.heading("#0", text="Step / Section")
        self.tree.heading("value", text="Value")
        self.tree.heading("modifier", text="Modifier")
        self.tree.heading("note", text="Note / Details")
        self.tree.heading("formula", text="Formula")
        self.tree.heading("hercules_ref", text="Hercules Ref")

        self.tree.column("#0", width=380, stretch=True)
        self.tree.column("value", width=110, stretch=True, anchor="center")
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

    def test_status(self):
        build = loader.get_test_preset_build("knight_bash_test")
        status = StatusCalculator(self.battle_config).calculate(build)

        msg = f"✅ Status Calculator Test (Phase 1)\n\n" \
              f"BATK     : {status.batk}\n" \
              f"Hard DEF : {status.def_}\n" \
              f"Soft DEF : {status.def2}\n" \
              f"CRI      : {status.cri / 10:.1f}%\n" \
              f"HIT      : {status.hit}\n" \
              f"FLEE     : {status.flee}"
        self.status_label.configure(text=msg)

    def test_pipeline(self):
        build = loader.get_test_preset_build("knight_bash_test")
        weapon = loader.get_test_preset_weapon("knight_bash_weapon")
        skill = loader.get_test_preset_skill_instance("knight_bash_skill")
        target = loader.get_test_preset_target("porcellio_test")

        status = StatusCalculator(self.battle_config).calculate(build)

        result = BattlePipeline(self.battle_config).calculate(status, weapon, skill, target, build)
        skill_data = loader.get_skill(skill.id) or {"name": "SM_BASH", "note": ""}

        self.clear_tree()
        self._populate_tree(build, status, weapon, skill, skill_data, target, result)

    def test_spear_peco(self):
        build = loader.get_test_preset_build("spear_peco_test")
        weapon = loader.get_test_preset_weapon("spear_peco_weapon")
        skill = loader.get_test_preset_skill_instance("spear_peco_skill")
        target = loader.get_test_preset_target("earth_lv3_test")

        status = StatusCalculator(self.battle_config).calculate(build)

        result = BattlePipeline(self.battle_config).calculate(status, weapon, skill, target, build)
        skill_data = loader.get_skill(skill.id) or {"name": "SM_BASH", "note": ""}

        self.clear_tree()
        self._populate_tree(build, status, weapon, skill, skill_data, target, result)

    def _populate_tree(self, build: PlayerBuild, status: StatusData, weapon: Weapon,
                       skill: SkillInstance, skill_data: dict, target: Target, result: DamageResult):
        """Exact 5-section hierarchy mirroring future battle_calc_weapon_attack order."""

        # 1. RAW INPUTS
        inputs_id = self.tree.insert("", tk.END, text="=== RAW INPUTS FROM JSON FILES ===", open=True)
        self.tree.insert(inputs_id, tk.END, text="bonus_batk", values=(build.bonus_batk, "", "← gear/cards/foods/SC bonus"))
        self.tree.insert(inputs_id, tk.END, text="base_str / bonus_str", values=(f"{build.base_str} / {build.bonus_str}", "", ""))
        self.tree.insert(inputs_id, tk.END, text="equip_def (raw)", values=(build.equip_def, "", "Hard DEF before clamp"))
        self.tree.insert(inputs_id, tk.END, text="base_vit", values=(build.base_vit, "", ""))
        self.tree.insert(inputs_id, tk.END, text="Weapon", values=(weapon.atk, f"+{weapon.refine}", f"Lv {weapon.level}"))

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
            self.tree.insert(pipeline_id, tk.END, text=step.name, values=(
                step.value,
                mult_str,
                step.note,
                step.formula,
                step.hercules_ref
            ))

        # 5. FINAL
        final_id = self.tree.insert("", tk.END, text="=== FINAL RESULT ===", open=True)
        self.tree.insert(final_id, tk.END, text="Min / Max / Avg Damage", 
                         values=(f"{result.min_damage} / {result.max_damage} / {result.avg_damage}", "", "placeholder – crit/variance next"))

        self.tree.item(pipeline_id, open=True)
        self.tree.item(final_id, open=True)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()