"""
jarvis.py  —  J.A.R.V.I.S. Personal Assistant UI

KEY FIXES vs previous version
──────────────────────────────
1. 8-digit hex crash removed — all colours are valid #RRGGBB
2. Right panel packed BEFORE main so expand=True doesn't steal its width
3. Time-aware greeting (morning / afternoon / evening)
4. Segoe UI → Courier New (cross-platform monospace)
5. Orb: giant "J" replaced with multi-ring Iron Man arc reactor animation
6. Raw tk.Frame / tk.Label used for content so fg/bg are pixel-exact
7. Sidebar hover states wired correctly with event propagation to children
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import math

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


class JarvisUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("J.A.R.V.I.S. | PERSONAL ASSISTANT")
        self.geometry("1280x760")
        self.configure(fg_color=BG_ROOT)
        self.resizable(False, False)

        # Orb animation state — only touched by the main-thread after() loop
        self._a1    = 0.0    # outer arc, clockwise
        self._a2    = 180.0  # mid ring arc, counter-clockwise
        self._a3    = 60.0   # inner ellipse arc
        self._pulse = 0.0
        self._pdir  = 1

        self._build()
        self._start_orb()
        self._start_wave()

    # ═══════════════════════════════════════════════════════ Layout builder ══

    def _build(self):
        """
        Pack order:  right → left → bottom → main
        right and left must be packed before main so that main's expand=True
        only consumes the space left over after the sidebars have been allocated.
        """
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
        # Top gold accent rule
        tk.Frame(parent, bg=GOLD_MID, height=2).pack(fill="x")

        # Brand
        tk.Label(
            parent, text="J.A.R.V.I.S.",
            font=(FM, 18, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(pady=(20, 0))
        tk.Label(
            parent, text="STARK INDUSTRIES",
            font=(FM, 7), bg=BG_PANEL, fg=TEXT_DIM,
        ).pack()

        tk.Frame(parent, bg=RULE, height=1).pack(fill="x", padx=20, pady=(14, 18))

        # Navigation items
        nav = [
            ("◈", "HOME",     True),
            ("◉", "CALENDAR", False),
            ("◎", "TASKS",    False),
            ("◇", "MESSAGES", False),
            ("◆", "SYSTEM",   False),
            ("◊", "DEVICES",  False),
        ]
        for icon, label, active in nav:
            self._nav_row(parent, icon, label, active)

        # Version stamp pinned to bottom
        tk.Frame(parent, bg=RULE, height=1).pack(
            side="bottom", fill="x", padx=20, pady=(0, 8),
        )
        tk.Label(
            parent, text="NEURAL CORE v2.4",
            font=(FM, 7), bg=BG_PANEL, fg=TEXT_DIM,
        ).pack(side="bottom", pady=(0, 6))

    def _nav_row(self, parent, icon: str, label: str, active: bool):
        """A sidebar navigation row with left accent bar and hover effect."""
        row_bg  = BG_CARD if active else BG_PANEL
        fg      = GOLD_BRIGHT if active else TEXT_MID
        bar_col = GOLD_BRIGHT if active else BG_PANEL

        row = tk.Frame(parent, bg=row_bg, cursor="hand2")
        row.pack(fill="x", padx=10, pady=2)

        # 3-pixel left accent bar
        tk.Frame(row, bg=bar_col, width=3).pack(side="left", fill="y")

        tk.Label(row, text=icon,  font=(FM, 12),      bg=row_bg, fg=fg).pack(
            side="left", padx=(12, 6), pady=11,
        )
        tk.Label(row, text=label, font=(FM, 11, "bold"), bg=row_bg, fg=fg).pack(
            side="left",
        )

        if active:
            return  # active row: no hover binding needed

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

        # Bind to the row frame and every child so hover doesn't flicker
        for widget in [row] + row.winfo_children():
            widget.bind("<Enter>", _enter)
            widget.bind("<Leave>", _leave)

    # ════════════════════════════════════════════════════════════ Right panel ══

    def _fill_right(self, parent):
        tk.Frame(parent, bg=GOLD_MID, height=2).pack(fill="x")

        # ── System status ────────────────────────────────────────────────────
        tk.Label(
            parent, text="SYSTEM STATUS",
            font=(FM, 11, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(pady=(20, 10))

        tk.Frame(parent, bg=RULE, height=1).pack(fill="x", padx=14, pady=(0, 10))

        for name, val, color in [
            ("NETWORK", "1 Gbps",   GREEN),
            ("CPU",     "18 %",     GOLD_BRIGHT),
            ("MEMORY",  "45 %",     CYAN_BRIGHT),
            ("UPTIME",  "04:22:18", TEXT_MID),
        ]:
            self._stat_card(parent, name, val, color)

        tk.Frame(parent, bg=RULE, height=1).pack(fill="x", padx=14, pady=(14, 10))

        # ── Home devices ─────────────────────────────────────────────────────
        tk.Label(
            parent, text="HOME CONTROL",
            font=(FM, 11, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(pady=(0, 10))

        for name, detail, color in [
            ("LIGHTS",     "Living Room  ·  60%",  GREEN),
            ("THERMOSTAT", "71 °F  ·  Auto",        CYAN_BRIGHT),
            ("SECURITY",   "Armed  ·  All Clear",    GOLD_BRIGHT),
        ]:
            self._device_card(parent, name, detail, color)

    def _stat_card(self, parent, name: str, val: str, color: str):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill="x", padx=14, pady=3)
        # Left colour accent bar
        tk.Frame(card, bg=color, width=3).pack(side="left", fill="y")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(side="left", fill="both", expand=True, padx=10, pady=7)
        tk.Label(inner, text=name, font=(FM, 8),           bg=BG_CARD, fg=TEXT_DIM, anchor="w").pack(fill="x")
        tk.Label(inner, text=val,  font=(FM, 11, "bold"),  bg=BG_CARD, fg=color,    anchor="w").pack(fill="x")

    def _device_card(self, parent, name: str, detail: str, color: str):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill="x", padx=14, pady=3)
        tk.Frame(card, bg=color, width=3).pack(side="left", fill="y")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        tk.Label(inner, text=name,   font=(FM, 8),    bg=BG_CARD, fg=TEXT_DIM, anchor="w").pack(fill="x")
        tk.Label(inner, text=detail, font=(FM, 10),   bg=BG_CARD, fg=TEXT_HI,  anchor="w").pack(fill="x")

    # ══════════════════════════════════════════════════════════ Main content ══

    def _fill_main(self, parent):
        # ── Header strip ─────────────────────────────────────────────────────
        header = tk.Frame(parent, bg=BG_PANEL, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Frame(header, bg=GOLD_DIM, height=1).pack(side="bottom", fill="x")

        tk.Label(
            header,
            text="J.A.R.V.I.S.  |  PERSONAL ASSISTANT",
            font=(FM, 13, "bold"), bg=BG_PANEL, fg=GOLD_BRIGHT,
        ).pack(side="left", padx=28, pady=14)

        tk.Label(
            header, text="●  ACTIVE  |  ONLINE",
            font=(FM, 10), bg=BG_PANEL, fg=GREEN,
        ).pack(side="right", padx=28)

        # ── Centre content ───────────────────────────────────────────────────
        centre = tk.Frame(parent, bg=BG_PANEL)
        centre.pack(fill="both", expand=True)

        # Orb canvas — centred via a wrapper frame
        orb_wrap = tk.Frame(centre, bg=BG_PANEL)
        orb_wrap.pack(pady=(16, 4))
        self._canvas = tk.Canvas(
            orb_wrap, width=290, height=290, bg=BG_PANEL, highlightthickness=0,
        )
        self._canvas.pack()

        # Time-aware greeting (morning / afternoon / evening)
        h = datetime.now().hour
        if   h < 12: tod = "MORNING"
        elif h < 17: tod = "AFTERNOON"
        else:        tod = "EVENING"

        tk.Label(
            centre, text=f"GOOD {tod},  ALEX.",
            font=(FM, 24, "bold"), bg=BG_PANEL, fg=TEXT_HI,
        ).pack(pady=(4, 2))
        tk.Label(
            centre,
            text=datetime.now().strftime("%H:%M  ·  %A,  %B %d  %Y").upper(),
            font=(FM, 10), bg=BG_PANEL, fg=TEXT_MID,
        ).pack()

        # ── Info strip ───────────────────────────────────────────────────────
        tk.Frame(centre, bg=RULE, height=1).pack(fill="x", padx=28, pady=(14, 0))
        info = tk.Frame(centre, bg=BG_CARD)
        info.pack(fill="x", padx=28)
        tk.Frame(centre, bg=RULE, height=1).pack(fill="x", padx=28)

        # Weather column
        wx = tk.Frame(info, bg=BG_CARD)
        wx.pack(side="left", padx=26, pady=13)
        tk.Label(wx, text="68 °F", font=(FM, 22, "bold"),
                 bg=BG_CARD, fg=TEXT_HI).pack(anchor="w")
        tk.Label(wx, text="Partly Cloudy  ·  London",
                 font=(FM, 9), bg=BG_CARD, fg=TEXT_MID).pack(anchor="w")

        tk.Frame(info, bg=RULE, width=1).pack(side="left", fill="y", pady=8)

        # Upcoming events column
        ev = tk.Frame(info, bg=BG_CARD)
        ev.pack(side="left", padx=26, pady=13)
        tk.Label(ev, text="UPCOMING",
                 font=(FM, 8), bg=BG_CARD, fg=GOLD_DIM).pack(anchor="w")
        for line in ["09:30  Strategy Call", "14:00  Design Review"]:
            tk.Label(ev, text=line, font=(FM, 10, "bold"),
                     bg=BG_CARD, fg=TEXT_HI).pack(anchor="w")

        tk.Frame(info, bg=RULE, width=1).pack(side="left", fill="y", pady=8)

        # Tasks column
        tsk = tk.Frame(info, bg=BG_CARD)
        tsk.pack(side="left", padx=26, pady=13)
        tk.Label(tsk, text="TASKS",
                 font=(FM, 8), bg=BG_CARD, fg=GOLD_DIM).pack(anchor="w")
        for task in ["Review Report", "Send Email", "Schedule Gym"]:
            tk.Label(tsk, text=f"▸  {task}", font=(FM, 10),
                     bg=BG_CARD, fg=TEXT_HI).pack(anchor="w")

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

        # Command entry — gold-bordered custom look
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

        # Placeholder text behaviour
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

    # ═════════════════════════════════════════════════════════ Orb animation ══

    def _start_orb(self):
        """Kick off the main-thread orb animation loop."""
        # Glow shade table — all valid 6-digit hex, no alpha suffix
        self._glow = [
            "#0c0600", "#140900", "#1c0d00", "#251200",
            "#2e1700", "#391d00", "#432200", "#4e2800",
        ]
        self._animate_orb()

    def _animate_orb(self):
        c = self._canvas
        c.delete("all")
        cx, cy, R = 145, 145, 118

        # Atmosphere glow — outermost to innermost, darkest to less-dark
        for i, shade in enumerate(self._glow):
            r = R + (len(self._glow) - i) * 8
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=shade, width=2)

        # Outer structural ring
        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=GOLD_MID, width=2)

        # 24 tick marks (major every 6th, minor others)
        for i in range(24):
            a   = math.radians(i * 15)
            r1  = R - (9 if i % 6 == 0 else 4)
            x1  = cx + R * math.cos(a);  y1 = cy + R * math.sin(a)
            x2  = cx + r1 * math.cos(a); y2 = cy + r1 * math.sin(a)
            col = GOLD_BRIGHT if i % 6 == 0 else GOLD_DIM
            c.create_line(x1, y1, x2, y2, fill=col, width=1)

        # Primary spinning arc — gold, clockwise
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

        # Mid ring — counter-clockwise, cyan
        Rm = R - 30
        c.create_oval(cx - Rm, cy - Rm, cx + Rm, cy + Rm, outline=CYAN_DIM, width=1)
        c.create_arc(
            cx - Rm, cy - Rm, cx + Rm, cy + Rm,
            start=self._a2, extent=85,
            outline=CYAN_BRIGHT, width=2, style=tk.ARC,
        )

        # Inner tilted ellipse ring (squished vertically for depth illusion)
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

        # Three orbital dots on outer ring
        for offset in (0, 120, 240):
            a  = math.radians(self._a1 + offset)
            dx = cx + R * math.cos(a)
            dy = cy + R * math.sin(a)
            c.create_oval(dx - 4, dy - 4, dx + 4, dy + 4,
                          fill=GOLD_BRIGHT, outline="")

        # Pulsing core
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

        # Crosshair at core centre
        c.create_line(cx - 12, cy, cx + 12, cy, fill=CYAN_BRIGHT, width=1)
        c.create_line(cx, cy - 12, cx, cy + 12, fill=CYAN_BRIGHT, width=1)

        # Advance rotation angles
        self._a1 = (self._a1 + 1.8) % 360
        self._a2 = (self._a2 - 1.2) % 360
        self._a3 = (self._a3 + 2.5) % 360

        self.after(20, self._animate_orb)   # ~50 fps

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
    app = JarvisUI()
    app.mainloop()