import time, psutil # type: ignore
import tkinter as tk
from dataclasses import dataclass
from strategy_link import ui_queue
from menu_definitions import make_menus, _ina

@dataclass
class UIState:
    team: str = "BLEUE"
    score_target: int = 142
    score_current: int = 0
    match_running: bool = False
    debug: bool = False

class UIManager:
    def __init__(self, root: tk.Tk, leds, audio, cfg: dict):
        self.root, self.leds, self.audio = root, leds, audio
        self.state = UIState(team=cfg.get("team", "BLEUE"), score_target=int(cfg.get("score_target", 142)))
        self.cfg = cfg
        self._t0 = None

        # Window
        w, h = cfg.get("ui", {}).get("width", 800), cfg.get("ui", {}).get("height", 480)
        root.geometry(f"{w}x{h}")
        root.title("EIRBOT IHM")
        root.configure(bg="#101418")

        # Frames
        self.frame_menu = tk.Frame(root, bg="#101418")
        self.frame_dash = tk.Frame(root, bg="#101418")
        self.frame_menu.pack(fill=tk.BOTH, expand=True)

        # Menu widgets
        self.lbl_title = tk.Label(self.frame_menu, text="", font=("DejaVu Sans", 24, "bold"), fg="#E6EDF3", bg="#101418")
        self.lbl_title.pack(pady=8)
        self.lbl_dyn = tk.Label(self.frame_menu, text="", font=("DejaVu Sans", 14), fg="#AAB2BF", bg="#101418")
        self.lbl_dyn.pack(pady=2)
        self.menu_lines = [tk.Label(self.frame_menu, text="", font=("DejaVu Sans", 20), fg="#C3E88D", bg="#101418", anchor="w") for _ in range(8)]
        for l in self.menu_lines: l.pack(fill=tk.X, padx=24, pady=2)

        # Dashboard widgets
        self.lbl_dash_title = tk.Label(self.frame_dash, text="EIRBOT — DASHBOARD", font=("DejaVu Sans", 26, "bold"), fg="#E6EDF3", bg="#101418")
        self.lbl_dash_title.pack(pady=10)
        self.lbl_dash_team = tk.Label(self.frame_dash, text="", font=("DejaVu Sans", 20), fg="#7BC4FF", bg="#101418")
        self.lbl_dash_team.pack()
        self.lbl_dash_target = tk.Label(self.frame_dash, text="", font=("DejaVu Sans", 20), fg="#F8E16C", bg="#101418")
        self.lbl_dash_target.pack(pady=4)
        self.lbl_dash_score = tk.Label(self.frame_dash, text="", font=("DejaVu Sans", 22), fg="#C3E88D", bg="#101418")
        self.lbl_dash_score.pack(pady=8)
        self.lbl_dash_state = tk.Label(self.frame_dash, text="", font=("DejaVu Sans", 16), fg="#AAB2BF", bg="#101418")
        self.lbl_dash_state.pack(pady=8)

        # Menus
        self.menus = make_menus(self)
        self.menu_stack = ["root"]
        self.cursor = 0
        if self.leds: self.leds.set_team(self.state.team)

        # Start in MENU view
        self.show_menu()

        # Loop timers
        root.after(100, self._poll_queue)
        root.after(200, self._tick)

                # ===== Keyboard navigation =====
        root.bind("<Up>", lambda e: self.nav_up())
        root.bind("<Down>", lambda e: self.nav_down())
        root.bind("<Return>", lambda e: self.nav_select())
        root.bind("<BackSpace>", lambda e: self.nav_back())
        root.bind("<Escape>", lambda e: self.nav_back())
        print("[UI] Contrôles clavier activés (↑ ↓ Entrée Backspace).")


    # ===== Views =====
    def show_menu(self):
        self.frame_dash.pack_forget()
        self.frame_menu.pack(fill=tk.BOTH, expand=True)
        self.render_menu()

    def show_dashboard(self):
        self.frame_menu.pack_forget()
        self.frame_dash.pack(fill=tk.BOTH, expand=True)
        self.render_dashboard()

    # ==== Plots =====
    def show_current_plot(self):
        from plots.current_plot import CurrentPlotWindow
        CurrentPlotWindow(self.root, _ina)

    # ===== Rendering =====
    def render_menu(self):
        key = self.menu_stack[-1]
        m = self.menus[key]
        self.lbl_title.config(text=m.get("title", ""))

        # Dynamic info block
        dyn_lines = []
        if "dynamic" in m:
            try: dyn_lines = list(m["dynamic"]())
            except Exception: dyn_lines = ["(dynamic error)"]
        self.lbl_dyn.config(text="\n".join(dyn_lines))

        items = m.get("items", [])
        for i, lab in enumerate(self.menu_lines):
            if i < len(items):
                text = items[i][0]
                prefix = "› " if i == self.cursor else "  "
                lab.config(text=prefix + text)
            else:
                lab.config(text="")

    def render_dashboard(self):
        self.lbl_dash_team.config(text=f"Équipe : {self.state.team}")
        self.lbl_dash_target.config(text=f"Objectif : {self.state.score_target} pts")
        self.lbl_dash_score.config(text=f"Score actuel : {self.state.score_current}")
        st = "Match en cours…" if self.state.match_running else "En attente"
        if self.state.debug: st += " | DEBUG ON"
        cpu = psutil.cpu_percent(interval=None)
        st += f" | CPU {cpu:.0f}%"
        self.lbl_dash_state.config(text=st)

    # ===== Navigation (GPIO) =====
    def nav_up(self):
        items = self.menus[self.menu_stack[-1]].get("items", [])
        if not items: return
        self.cursor = (self.cursor - 1) % len(items)
        self.render_menu()

    def nav_down(self):
        items = self.menus[self.menu_stack[-1]].get("items", [])
        if not items: return
        self.cursor = (self.cursor + 1) % len(items)
        self.render_menu()

    def nav_select(self):
        items = self.menus[self.menu_stack[-1]].get("items", [])
        if not items: return
        label, cb = items[self.cursor]
        try:
            cb()
        except Exception as e:
            self.lbl_dyn.config(text=f"Erreur action: {e}")
        # Rerender after potential change
        if self.frame_menu.winfo_ismapped():
            self.render_menu()
        else:
            self.render_dashboard()

    def nav_back(self):
        if len(self.menu_stack) > 1:
            self.menu_stack.pop()
            self.cursor = 0
            self.render_menu()
        else:
            # Depuis root: bascule vers dashboard
            self.show_dashboard()

    # ===== Menu helpers =====
    def open_menu(self, key: str):
        self.menu_stack.append(key)
        self.cursor = 0
        self.show_menu()

    # ===== State/actions =====
    def toggle_team(self):
        self.state.team = "JAUNE" if self.state.team == "BLEUE" else "BLEUE"
        if self.leds: self.leds.set_team(self.state.team)
        self.render_menu(); self.render_dashboard()

    def toggle_debug(self):
        self.state.debug = not self.state.debug
        if self.leds: self.leds.set_debug(self.state.debug)
        self.render_menu(); self.render_dashboard()

    def start_match(self):
        if self.state.match_running: return
        self.state.match_running = True
        self._t0 = time.time()
        if self.leds: self.leds.match_start()
        if self.audio: self.audio.stop(); self.audio.play('match', loop=True)
        self.show_dashboard()

    def stop_match(self):
        if not self.state.match_running: return
        self.state.match_running = False
        if self.leds: self.leds.match_stop()
        if self.audio: self.audio.stop(); self.audio.play('end')
        self.show_dashboard()

    def force_end_match(self):
        # même effet que stop, sans check
        self.state.match_running = False
        if self.leds: self.leds.match_stop()
        if self.audio: self.audio.stop(); self.audio.play('end')
        self.show_dashboard()

    def run_actionneur_test(self):
        from esp_test import test_esp32
        self.lbl_dyn.config(text="Test des actionneurs en cours…")
        self.root.update_idletasks()
        try:
            test_esp32()
            self.lbl_dyn.config(text="Actionneurs testés")
        except Exception as e:
            self.lbl_dyn.config(text=f"Erreur test actionneurs : {e}")

    # ===== Background loops =====
    def _tick(self):
        # maj titre avec chrono pendant le match
        if self.state.match_running and self._t0:
            self.root.title(f"EIRBOT IHM — {int(time.time()-self._t0)}s")
        self.root.after(200, self._tick)

    def _poll_queue(self):
        # lit messages stratégie
        try:
            while True:
                msg = ui_queue.get_nowait()
                t = msg.get('type')
                if t == 'score':
                    self.state.score_current = int(msg['value'])
                    self.lbl_dash_score.config(text=f"Score actuel : {self.state.score_current}")
                elif t == 'error' and self.leds:
                    self.leds.set_error(bool(msg['value']))
                elif t == 'end_match':
                    self.force_end_match()
        except Exception:
            pass
        self.root.after(100, self._poll_queue)