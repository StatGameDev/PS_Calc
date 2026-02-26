import customtkinter as ctk

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RO Pre-Renewal Damage Calculator — Hercules Accurate")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        for name in ["Character", "Weapon", "Skill", "Target", "Results"]:
            tab = self.tabview.add(name)
            ctk.CTkLabel(tab, text=f"📋 {name} Tab — Inputs will go here", font=("", 18)).pack(pady=40)

        # Quick test
        btn = ctk.CTkButton(self.tabview.tab("Results"), text="🚀 Test Status Calculation", command=self.test_status)
        btn.pack(pady=30)

    def test_status(self):
        from core.config import BattleConfig
        from core.models.build import PlayerBuild
        from core.calculators.status_calculator import StatusCalculator

        build = PlayerBuild(
            base_level=99,
            base_str=120,
            bonus_str=40,
            base_dex=90,
            bonus_batk=80,
            is_ranged=False
        )
        status = StatusCalculator(BattleConfig()).calculate(build)

        msg = f"✅ Status Calculated (exact Hercules pre-ren)\n\n" \
              f"BATK : {status.batk}\n" \
              f"DEF  : {status.def_} (hard) + {status.def2} (soft)\n" \
              f"CRI  : {status.cri / 10:.1f}%\n" \
              f"HIT  : {status.hit}\n" \
              f"FLEE : {status.flee}"

        ctk.CTkLabel(self.tabview.tab("Results"), text=msg, font=("", 16)).pack(pady=20)