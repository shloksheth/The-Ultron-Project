"""
ultron_ui.py  —  U.L.T.R.O.N. Personal Assistant UI
Adapted from J.A.R.V.I.S. UI
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import math
import psutil
import threading
import queue
import time
from ultron_brain import UltronBrain
from voice_service import VoiceService
from credentials_manager import CredentialManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ───────────────────────────────────────────────────────────────────
BG_ROOT    = "#07080f"   # window background
BG_PANEL   = "#0d0f1b"  # sidebar / right panel
BG_CARD    = "#111525"  # card / info-strip background
BG_HOVER   = "#181d30"  # sidebar row hover
GOLD_BRIGHT= "#FFB347"
GOLD_MID   = "#D4841A"
GOLD_DIM   = "#4A3000"
CYAN_BRIGHT= "#00E5FF"
CYAN_DIM   = "#003344"
GREEN      = "#00FF88"
TEXT_HI    = "#EEE8D8"
TEXT_MID   = "#7A8898"
TEXT_DIM   = "#354050"
RULE       = "#1A1F32"
FM         = "Courier New"   # monospace, ships on Windows / macOS / Linux


class UltronUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("U.L.T.R.O.N. | PERSONAL ASSISTANT")
        self.geometry("1280x760")
        self.configure(fg_color=BG_ROOT)
        self.resizable(False, False)

        # Orb animation state
        self._a1    = 0.0    # outer arc, clockwise
        self._a2    = 180.0  # mid ring arc, counter-clockwise
        self._a3    = 60.0   # inner ellipse arc
        self._pulse = 0.0
        self._pdir  = 1

        # System Integration
        self.brain = UltronBrain()
        self.voice = VoiceService()
        self.creds_manager = CredentialManager()
        self.command_queue = self.voice.command_queue

        self._build()
        self._start_orb()
        self._start_wave()
        self._start_stats_loop()
        self._start_voice_integration()

    # ═══════════════════════════════════════════════════════ Layout builder ══

    def _build(self):
        # ── Right panel ─────────────────────────────────────────────────────
        right = tk.Frame(self, bg=BG_PANEL, width=248)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._fill_right(right)

        # ── Left sidebar ─────────────────────────────────────────────────────
        left = tk.Frame(self, bg=BG_PANEL, width=224)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._fill_left(left)

        # ── Bottom command bar ───────────────────────────────────────────────
        bottom = tk.Frame(self, bg=BG_ROOT, height=64)
        bottom.pack(side="bottom", fill="x")
        bottom.pack_propagate(False)
        self._fill_bottom(bottom)

        # ── Main content (fills the remaining centre) ────────────────────────
        main = tk.Frame(self, bg=BG_PANEL)
        main.pack(side="left", fill="both", expand=True)
        self._fill_main(main)

    # ═══════════════════════════════════════════════════════════ Left sidebar ══

    def _fill_left(self, parent):
        tk.Frame(parent, bg=GOLD_MID, height=2).pack(fill="x")

        tk.Label(
            parent, text="U.L.T.R.O.N.",
            font=(FM, 18, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(pady=(20, 0))
        tk.Label(
            parent, text="HYDRA CORE",
            font=(FM, 7), bg=BG_PANEL, fg=TEXT_DIM,
        ).pack()

        tk.Frame(parent, bg=RULE, height=1).pack(fill="x", padx=20, pady=(14, 18))

        nav = [
            ("◈", "DASHBOARD", True),
            ("◉", "LOGS",      False),
            ("◎", "BROWSER",   False),
            ("◇", "NETWORK",   False),
            ("◆", "AI CORE",   False),
            ("◊", "SETTINGS",  False),
        ]
        for icon, label, active in nav:
            self._nav_row(parent, icon, label, active)

        tk.Frame(parent, bg=RULE, height=1).pack(
            side="bottom", fill="x", padx=20, pady=(0, 8),
        )
        tk.Label(
            parent, text="NEURAL CORE v3.0",
            font=(FM, 7), bg=BG_PANEL, fg=TEXT_DIM,
        ).pack(side="bottom", pady=(0, 6))

    def _nav_row(self, parent, icon: str, label: str, active: bool):
        row_bg  = BG_CARD if active else BG_PANEL
        fg      = GOLD_BRIGHT if active else TEXT_MID
        bar_col = GOLD_BRIGHT if active else BG_PANEL

        row = tk.Frame(parent, bg=row_bg, cursor="hand2")
        row.pack(fill="x", padx=10, pady=2)

        tk.Frame(row, bg=bar_col, width=3).pack(side="left", fill="y")

        tk.Label(row, text=icon,  font=(FM, 12),      bg=row_bg, fg=fg).pack(
            side="left", padx=(12, 6), pady=11,
        )
        tk.Label(row, text=label, font=(FM, 11, "bold"), bg=row_bg, fg=fg).pack(
            side="left",
        )

        if active:
            return

        def _enter(e):
            row.configure(bg=BG_HOVER)
            for w in row.winfo_children():
                if isinstance(w, tk.Label):
                    w.configure(bg=BG_HOVER, fg=CYAN_BRIGHT)

        def _leave(e):
            row.configure(bg=BG_PANEL)
            for w in row.winfo_children():
                if isinstance(w, tk.Label):
                    w.configure(bg=BG_PANEL, fg=TEXT_MID)

        for widget in [row] + row.winfo_children():
            widget.bind("<Enter>", _enter)
            widget.bind("<Leave>", _leave)

    # ════════════════════════════════════════════════════════════ Right panel ══

    def _fill_right(self, parent):
        tk.Frame(parent, bg=GOLD_MID, height=2).pack(fill="x")

        tk.Label(
            parent, text="SYSTEM STATUS",
            font=(FM, 11, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(pady=(20, 10))

        tk.Frame(parent, bg=RULE, height=1).pack(fill="x", padx=14, pady=(0, 10))

        self.stats_labels = {}
        for name, key, color in [
            ("CPU LOAD", "cpu", GREEN),
            ("MEM USAGE", "mem", CYAN_BRIGHT),
        ]:
            self.stats_labels[key] = self._stat_card(parent, name, "0 %", color)

        tk.Frame(parent, bg=RULE, height=1).pack(fill="x", padx=14, pady=(14, 10))

        tk.Label(
            parent, text="NEURAL FEED",
            font=(FM, 11, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(pady=(0, 10))

        # Log container
        self.log_box = tk.Text(
            parent, bg=BG_CARD, fg=TEXT_MID, font=(FM, 8),
            relief="flat", bd=0, padx=10, pady=10, state="disabled"
        )
        self.log_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _stat_card(self, parent, name: str, val: str, color: str):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill="x", padx=14, pady=3)
        tk.Frame(card, bg=color, width=3).pack(side="left", fill="y")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(side="left", fill="both", expand=True, padx=10, pady=7)
        tk.Label(inner, text=name, font=(FM, 8),           bg=BG_CARD, fg=TEXT_DIM, anchor="w").pack(fill="x")
        vlbl = tk.Label(inner, text=val,  font=(FM, 11, "bold"),  bg=BG_CARD, fg=color,    anchor="w")
        vlbl.pack(fill="x")
        return vlbl

    # ══════════════════════════════════════════════════════════ Main content ══

    def _fill_main(self, parent):
        header = tk.Frame(parent, bg=BG_PANEL, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Frame(header, bg=GOLD_DIM, height=1).pack(side="bottom", fill="x")

        tk.Label(
            header,
            text="U.L.T.R.O.N.  |  INTERFACE",
            font=(FM, 13, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(side="left", padx=28, pady=14)

        tk.Label(
            header, text="●  ACTIVE  |  ONLINE",
            font=(FM, 10), bg=BG_PANEL, fg=GREEN,
        ).pack(side="right", padx=28)

        centre = tk.Frame(parent, bg=BG_PANEL)
        centre.pack(fill="both", expand=True)

        orb_wrap = tk.Frame(centre, bg=BG_PANEL)
        orb_wrap.pack(pady=(16, 4))
        self._canvas = tk.Canvas(
            orb_wrap, width=290, height=290, bg=BG_PANEL, highlightthickness=0,
        )
        self._canvas.pack()

        h = datetime.now().hour
        if   h < 12: tod = "MORNING"
        elif h < 17: tod = "AFTERNOON"
        else:        tod = "EVENING"

        self.greeting_lbl = tk.Label(
            centre, text=f"GOOD {tod},  SIR.",
            font=(FM, 24, "bold"), bg=BG_PANEL, fg=TEXT_HI,
        )
        self.greeting_lbl.pack(pady=(4, 2))
        self.clock_lbl = tk.Label(
            centre,
            text=datetime.now().strftime("%H:%M:%S  ·  %A,  %B %d  %Y").upper(),
            font=(FM, 10), bg=BG_PANEL, fg=TEXT_MID,
        )
        self.clock_lbl.pack()

        tk.Frame(centre, bg=RULE, height=1).pack(fill="x", padx=28, pady=(14, 0))
        info = tk.Frame(centre, bg=BG_CARD)
        info.pack(fill="x", padx=28)
        tk.Frame(centre, bg=RULE, height=1).pack(fill="x", padx=28)

        # Browser Preview Area
        self.browser_frame = tk.Frame(info, bg=BG_CARD, height=150)
        self.browser_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.browser_status = tk.Label(self.browser_frame, text="BROWSER IDLE", font=(FM, 10), bg=BG_CARD, fg=TEXT_DIM)
        self.browser_status.pack(expand=True)
        self.browser_image_lbl = tk.Label(self.browser_frame, bg=BG_CARD)
        # self.browser_image_lbl will be updated with screenshots

    # ═════════════════════════════════════════════════════════ Bottom bar ══

    def _fill_bottom(self, parent):
        tk.Frame(parent, bg=GOLD_DIM, height=1).pack(fill="x")
        inner = tk.Frame(parent, bg=BG_ROOT)
        inner.pack(fill="both", expand=True, padx=20)

        tk.Label(
            inner, text="●  LISTENING",
            font=(FM, 10), bg=BG_ROOT, fg=GREEN,
        ).pack(side="left", pady=18)

        self._wave_lbl = tk.Label(
            inner, text="▁ ▂ ▄ ▅ ▆ ▅ ▄ ▂ ▁",
            font=(FM, 16), bg=BG_ROOT, fg=CYAN_BRIGHT,
        )
        self._wave_lbl.pack(side="left", padx=18)

        border = tk.Frame(inner, bg=GOLD_DIM, padx=1, pady=1)
        border.pack(side="right", pady=13)
        entry_bg = tk.Frame(border, bg=BG_CARD)
        entry_bg.pack()
        self._entry = tk.Entry(
            entry_bg, bg=BG_CARD, fg=TEXT_HI,
            font=(FM, 11), insertbackground=GOLD_BRIGHT,
            relief="flat", bd=0, width=44,
        )
        self._entry.pack(padx=12, pady=9)

        placeholder = "Enter command..."
        self._entry.insert(0, placeholder)
        self._entry.configure(fg=TEXT_DIM)

        def _focus_in(e):
            if self._entry.get() == placeholder:
                self._entry.delete(0, "end")
                self._entry.configure(fg=TEXT_HI)

        def _focus_out(e):
            if not self._entry.get().strip():
                self._entry.insert(0, placeholder)
                self._entry.configure(fg=TEXT_DIM)

        self._entry.bind("<FocusIn>",  _focus_in)
        self._entry.bind("<FocusOut>", _focus_out)
        self._entry.bind("<Return>", lambda e: self._handle_command())

    def _handle_command(self):
        cmd = self._entry.get()
        if cmd and cmd != "Enter command...":
            self.log(f"User: {cmd}", "user")
            self._entry.delete(0, tk.END)
            # Process command in thread
            threading.Thread(target=self._process_command, args=(cmd,), daemon=True).start()

    def _process_command(self, cmd):
        response = self.brain.chat(cmd)
        self.after(0, lambda: self.greeting_lbl.configure(text=response[:50] + "..." if len(response)>50 else response))
        self.log(f"Ultron: {response}", "ai")

        # Handle actions
        clean_response = response
        if "[ACTION:" in response:
            clean_response = response.split("[ACTION:")[0].strip()
            try:
                import json
                action_str = response.split("[ACTION:")[1].split("]")[0]
                action_data = json.loads(action_str)
                self._handle_action(action_data)
            except Exception as e:
                self.log(f"Error parsing action: {e}", "error")

        self.voice.speak(clean_response)

    def _handle_action(self, action):
        atype = action.get("type")
        params = action.get("params", {})

        if atype == "OPEN_URL":
            url = params.get("url")
            self.log(f"Action: Opening {url}")
            # Use webbrowser or automation
            import webbrowser
            webbrowser.open(url)
        elif atype == "DELTAMATH_LOGIN":
            creds = self.creds_manager.get_creds("deltamath")
            if not creds:
                if params.get("username") and params.get("password"):
                    creds = {"username": params.get("username"), "password": params.get("password")}
                else:
                    self.log("Deltamath credentials missing.", "error")
                    self.voice.speak("I don't have your Delta Math credentials yet.")
                    return

            self.log("Action: Initiating Deltamath Login...")
            from automation import run_automation
            self.update_browser('OPENING DELTAMATH...')
            threading.Thread(target=run_automation, args=(creds, self), daemon=True).start()
        # Add more actions as needed

    def _start_voice_integration(self):
        self.voice.start()
        threading.Thread(target=self._voice_command_listener, daemon=True).start()

    def _voice_command_listener(self):
        while True:
            try:
                command = self.command_queue.get(timeout=1)
                self.log(f"Voice: {command}", "user")
                self._process_command(command)
            except queue.Empty:
                continue

    def update_browser(self, status, screenshot_b64=None):
        self.after(0, self._update_browser_ui, status, screenshot_b64)

    def _update_browser_ui(self, status, screenshot_b64):
        self.browser_status.configure(text=status)
        if screenshot_b64:
            from PIL import Image, ImageTk
            import io
            import base64

            img_data = base64.b64decode(screenshot_b64)
            img = Image.open(io.BytesIO(img_data))
            # Resize to fit browser frame
            img = img.resize((200, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            self.browser_image_lbl.configure(image=photo)
            self.browser_image_lbl.image = photo # keep reference
            self.browser_image_lbl.pack(expand=True)
            self.browser_status.pack_forget()
        else:
            self.browser_image_lbl.pack_forget()
            self.browser_status.pack(expand=True)

    def log(self, message, type="system"):
        self.after(0, self._append_log, message, type)

    def _append_log(self, message, type):
        self.log_box.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = TEXT_MID
        if type == "user": color = GOLD_BRIGHT
        elif type == "ai": color = CYAN_BRIGHT
        elif type == "error": color = "#FF4444"

        self.log_box.insert(tk.END, f"[{timestamp}] ", TEXT_DIM)
        self.log_box.insert(tk.END, f"{message}\n", color)
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    # ═════════════════════════════════════════════════════════ Stats Loop ══

    def _start_stats_loop(self):
        def _update():
            # Update Stats
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            self.stats_labels['cpu'].configure(text=f"{cpu} %")
            self.stats_labels['mem'].configure(text=f"{mem} %")

            # Update Clock
            now = datetime.now()
            self.clock_lbl.configure(text=now.strftime("%H:%M:%S  ·  %A,  %B %d  %Y").upper())

            self.after(1000, _update)
        _update()

    # ═════════════════════════════════════════════════════════ Orb animation ══

    def _start_orb(self):
        self._glow = [
            "#0c0600", "#140900", "#1c0d00", "#251200",
            "#2e1700", "#391d00", "#432200", "#4e2800",
        ]
        self._animate_orb()

    def _animate_orb(self):
        c = self._canvas
        c.delete("all")
        cx, cy, R = 145, 145, 118

        for i, shade in enumerate(self._glow):
            r = R + (len(self._glow) - i) * 8
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=shade, width=2)

        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=GOLD_MID, width=2)

        for i in range(24):
            a   = math.radians(i * 15)
            r1  = R - (9 if i % 6 == 0 else 4)
            x1  = cx + R * math.cos(a);  y1 = cy + R * math.sin(a)
            x2  = cx + r1 * math.cos(a); y2 = cy + r1 * math.sin(a)
            col = GOLD_BRIGHT if i % 6 == 0 else GOLD_DIM
            c.create_line(x1, y1, x2, y2, fill=col, width=1)

        c.create_arc(
            cx - R, cy - R, cx + R, cy + R,
            start=self._a1, extent=115,
            outline=GOLD_BRIGHT, width=3, style=tk.ARC,
        )
        c.create_arc(
            cx - R, cy - R, cx + R, cy + R,
            start=self._a1 + 185, extent=55,
            outline=GOLD_MID, width=2, style=tk.ARC,
        )

        Rm = R - 30
        c.create_oval(cx - Rm, cy - Rm, cx + Rm, cy + Rm, outline=CYAN_DIM, width=1)
        c.create_arc(
            cx - Rm, cy - Rm, cx + Rm, cy + Rm,
            start=self._a2, extent=85,
            outline=CYAN_BRIGHT, width=2, style=tk.ARC,
        )

        Ri = R - 56
        c.create_oval(
            cx - Ri, cy - Ri // 2, cx + Ri, cy + Ri // 2,
            outline=GOLD_DIM, width=1,
        )
        c.create_arc(
            cx - Ri, cy - Ri // 2, cx + Ri, cy + Ri // 2,
            start=self._a3, extent=95,
            outline=GOLD_MID, width=2, style=tk.ARC,
        )

        for offset in (0, 120, 240):
            a  = math.radians(self._a1 + offset)
            dx = cx + R * math.cos(a)
            dy = cy + R * math.sin(a)
            c.create_oval(dx - 4, dy - 4, dx + 4, dy + 4,
                          fill=GOLD_BRIGHT, outline="")

        self._pulse += 0.05 * self._pdir
        if self._pulse >= 1.0 or self._pulse <= 0.0:
            self._pdir *= -1
        self._pulse = max(0.0, min(1.0, self._pulse))

        cr   = 16 + self._pulse * 8
        ccol = GOLD_BRIGHT if self._pulse > 0.5 else GOLD_MID
        for gr in (cr + 14, cr + 7, cr):
            c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                          fill="", outline=(GOLD_DIM if gr > cr else ccol), width=1)
        c.create_oval(
            cx - cr, cy - cr, cx + cr, cy + cr,
            fill=BG_PANEL, outline=ccol, width=2,
        )

        c.create_line(cx - 12, cy, cx + 12, cy, fill=CYAN_BRIGHT, width=1)
        c.create_line(cx, cy - 12, cx, cy + 12, fill=CYAN_BRIGHT, width=1)

        self._a1 = (self._a1 + 1.8) % 360
        self._a2 = (self._a2 - 1.2) % 360
        self._a3 = (self._a3 + 2.5) % 360

        self.after(20, self._animate_orb)

    # ═══════════════════════════════════════════════════════ Wave animation ══

    def _start_wave(self):
        waves = [
            "▁ ▂ ▄ ▅ ▆ ▅ ▄ ▂ ▁",
            "▂ ▄ ▅ ▆ ▇ ▆ ▅ ▄ ▂",
            "▄ ▅ ▆ ▇ █ ▇ ▆ ▅ ▄",
            "▂ ▄ ▅ ▆ ▇ ▆ ▅ ▄ ▂",
        ]
        idx = [0]

        def _tick():
            self._wave_lbl.configure(text=waves[idx[0]])
            idx[0] = (idx[0] + 1) % len(waves)
            self.after(200, _tick)

        _tick()


if __name__ == "__main__":
    app = UltronUI()
    app.mainloop()
