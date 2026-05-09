"""
ultron_boot.py  —  U.L.T.R.O.N. Boot Screen
Launched by Start_Ultron.bat before ultron_main.py starts.

KEY FIXES vs previous version
──────────────────────────────
1. ctk.StringVar → tk.StringVar
2. All tkinter widget calls happen ONLY on the main thread via self.after()
3. sys.executable used to locate pythonw reliably
4. is_ultron_active() filters own PID
5. Multi-ring animated orb
"""

import customtkinter as ctk
import tkinter as tk
import time
import math
import threading
import subprocess
import sys
import os
import psutil

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#04050f"
BG_PANEL    = "#080a16"
GOLD_BRIGHT = "#FFB347"
GOLD_MID    = "#D4841A"
GOLD_DIM    = "#4A3000"
CYAN_BRIGHT = "#00E5FF"
CYAN_DIM    = "#003344"
TEXT_DIM    = "#3A4060"
TEXT_MID    = "#707888"
FM          = "Courier New"


class UltronBoot(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("U.L.T.R.O.N.  —  NEURAL BOOT SEQUENCE")
        self.geometry("1000x720")
        self.configure(fg_color=BG)
        self.resizable(False, False)

        # ── Shared state (written by worker thread, read by main-thread poll) ──
        # Rule: the background thread NEVER touches any tkinter/ctk object.
        # It only writes to these plain Python variables.
        self._status:       str   = "INITIALISING..."
        self._elapsed:      float = 0.0
        self._prog:         float = 0.0
        self._done:         bool  = False
        self._launch_error: str   = ""
        self._launch_time:  float = 0.0   # time.time() when jarvis.py was Popen'd

        # ── Animation state (main thread only) ──────────────────────────────
        self._angle  = 0.0    # outer arc, clockwise
        self._angle2 = 180.0  # mid arc, counter-clockwise
        self._angle3 = 45.0   # inner ellipse arc
        self._pulse  = 0.0
        self._pdir   = 1

        self._build_ui()
        self._start_launch_thread()
        self._main_loop()   # starts the combined animation + state-sync loop

    # ────────────────────────────────────────────────────────────── UI build ──

    def _build_ui(self):
        # Top brand strip
        tk.Label(
            self, text="◈  ULTRON SYSTEMS  ·  NEURAL CORE v3.0",
            font=(FM, 10), bg=BG, fg=TEXT_DIM,
        ).pack(pady=(22, 0))

        # Title
        tk.Label(
            self, text="U.L.T.R.O.N.",
            font=(FM, 54, "bold"), bg=BG, fg=GOLD_BRIGHT,
        ).pack(pady=(8, 0))

        tk.Label(
            self, text="UNIVERSAL LOCAL TECHNOLOGICAL RESPONSIVE OPERATING NETWORK",
            font=(FM, 10), bg=BG, fg=TEXT_MID,
        ).pack()

        # Horizontal rule
        tk.Frame(self, bg=GOLD_DIM, height=1).pack(fill="x", padx=80, pady=(14, 0))

        # Animated orb canvas
        self.canvas = tk.Canvas(
            self, width=400, height=400, bg=BG, highlightthickness=0,
        )
        self.canvas.pack(pady=(10, 0))

        # Horizontal rule
        tk.Frame(self, bg=GOLD_DIM, height=1).pack(fill="x", padx=80, pady=(0, 14))

        # Status label — tk.StringVar (NOT ctk.StringVar which does not exist)
        self._status_var = tk.StringVar(value=self._status)
        tk.Label(
            self, textvariable=self._status_var,
            font=(FM, 14, "bold"), bg=BG, fg=CYAN_BRIGHT,
        ).pack(pady=(0, 4))

        # Elapsed label
        self._elapsed_var = tk.StringVar(value="ELAPSED  0.00 s")
        tk.Label(
            self, textvariable=self._elapsed_var,
            font=(FM, 10), bg=BG, fg=TEXT_MID,
        ).pack()

        # Progress bar (ctk widget is fine here — it's only set from the main thread)
        self._bar = ctk.CTkProgressBar(
            self, width=560, height=6,
            fg_color="#10121e", progress_color=GOLD_MID,
            corner_radius=2,
        )
        self._bar.pack(pady=(14, 20))
        self._bar.set(0)

    # ──────────────────────────────────────────── Combined main-thread loop ──

    def _main_loop(self):
        """
        Runs every 30 ms on the main thread.
        Draws the orb animation AND syncs shared state → widget state.
        No tkinter calls happen anywhere else.
        """
        # Sync shared state → widgets
        self._status_var.set(self._status)
        self._elapsed_var.set(f"ELAPSED  {self._elapsed:.2f} s")
        self._bar.set(self._prog)

        # Draw animated orb
        self._draw_orb()

        # Check completion / error flags
        if self._done:
            self._bar.set(1.0)
            self.after(1400, self.destroy)
            return

        if self._launch_error:
            return  # leave window open; user can read the error message

        self.after(30, self._main_loop)

    # ─────────────────────────────────────────────────────── Orb animation ──

    def _draw_orb(self):
        c = self.canvas
        c.delete("all")
        cx, cy, R = 200, 200, 140

        # Atmosphere glow — 8 nested rings fading outward
        # All colours are valid 6-digit hex (no 8-digit alpha channels)
        glow = [
            "#0a0500", "#110800", "#190d00", "#221200",
            "#2c1800", "#361d00", "#402300", "#4a2800",
        ]
        for i, shade in enumerate(glow):
            r = R + (len(glow) - i) * 9
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=shade, width=2)

        # Outer ring + tick marks
        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=GOLD_MID, width=2)
        for i in range(36):
            a   = math.radians(i * 10)
            r1  = R - (10 if i % 9 == 0 else 4 if i % 3 == 0 else 2)
            x1  = cx + R * math.cos(a);  y1 = cy + R * math.sin(a)
            x2  = cx + r1 * math.cos(a); y2 = cy + r1 * math.sin(a)
            col = GOLD_BRIGHT if i % 9 == 0 else (GOLD_MID if i % 3 == 0 else GOLD_DIM)
            c.create_line(x1, y1, x2, y2, fill=col, width=1)

        # Outer spinning arc — gold, clockwise
        c.create_arc(
            cx - R, cy - R, cx + R, cy + R,
            start=self._angle, extent=120,
            outline=GOLD_BRIGHT, width=4, style=tk.ARC,
        )
        c.create_arc(
            cx - R, cy - R, cx + R, cy + R,
            start=self._angle + 190, extent=50,
            outline=GOLD_MID, width=2, style=tk.ARC,
        )

        # Mid ring — counter-rotating, cyan
        Rm = R - 32
        c.create_oval(cx - Rm, cy - Rm, cx + Rm, cy + Rm, outline=CYAN_DIM, width=1)
        c.create_arc(
            cx - Rm, cy - Rm, cx + Rm, cy + Rm,
            start=self._angle2, extent=85,
            outline=CYAN_BRIGHT, width=3, style=tk.ARC,
        )
        c.create_arc(
            cx - Rm, cy - Rm, cx + Rm, cy + Rm,
            start=self._angle2 + 170, extent=40,
            outline=CYAN_DIM, width=1, style=tk.ARC,
        )

        # Inner tilted ellipse ring
        Ri = R - 64
        c.create_oval(cx - Ri, cy - Ri // 2, cx + Ri, cy + Ri // 2,
                      outline=GOLD_DIM, width=1)
        c.create_arc(
            cx - Ri, cy - Ri // 2, cx + Ri, cy + Ri // 2,
            start=self._angle3, extent=100,
            outline=GOLD_MID, width=2, style=tk.ARC,
        )

        # Three orbital dots on outer ring, 120° apart
        for offset in (0, 120, 240):
            a  = math.radians(self._angle + offset)
            dx = cx + R * math.cos(a)
            dy = cy + R * math.sin(a)
            c.create_oval(dx - 5, dy - 5, dx + 5, dy + 5,
                          fill=GOLD_BRIGHT, outline="")

        # Pulsing core
        self._pulse += 0.04 * self._pdir
        if self._pulse >= 1.0 or self._pulse <= 0.0:
            self._pdir *= -1
        self._pulse = max(0.0, min(1.0, self._pulse))

        cr   = 18 + self._pulse * 10
        ccol = GOLD_BRIGHT if self._pulse > 0.5 else GOLD_MID
        for gr in (cr + 16, cr + 8, cr):
            c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                          fill="", outline=(GOLD_DIM if gr > cr else ccol), width=1)
        c.create_oval(cx - cr, cy - cr, cx + cr, cy + cr,
                      fill=BG, outline=ccol, width=2)

        # Crosshair
        c.create_line(cx - 14, cy, cx + 14, cy, fill=CYAN_BRIGHT, width=1)
        c.create_line(cx, cy - 14, cx, cy + 14, fill=CYAN_BRIGHT, width=1)

        # Progress arc segment on outer ring (tracks self._prog 0→1)
        if self._prog > 0:
            extent = min(359.9, self._prog * 360)
            c.create_arc(
                cx - R - 10, cy - R - 10, cx + R + 10, cy + R + 10,
                start=90, extent=extent,
                outline=GOLD_BRIGHT, width=2, style=tk.ARC,
            )

        # Advance angles (main thread only — safe)
        self._angle  = (self._angle  + 2.2) % 360
        self._angle2 = (self._angle2 - 1.4) % 360
        self._angle3 = (self._angle3 + 3.0) % 360

    # ─────────────────────────────────────────────── Background worker thread ──

    def _start_launch_thread(self):
        threading.Thread(target=self._launch_worker, daemon=True).start()

    def _launch_worker(self):
        """
        Background thread — writes ONLY to plain Python attributes.
        Never touches self.canvas, self._status_var, self._bar, or any widget.
        """
        # Resolve python/pythonw path from the running interpreter (no PATH guess)
        exe = sys.executable  # e.g. C:\Users\...\Python312\python.exe
        if os.name == "nt" and exe.lower().endswith("python.exe"):
            candidate = exe[:-10] + "pythonw.exe"
            if os.path.isfile(candidate):
                exe = candidate

        # ultron_main.py lives in the same folder as this script
        script_dir  = os.path.dirname(os.path.abspath(__file__))
        ultron_path = os.path.join(script_dir, "ultron_main.py")

        self._status = "STARTING ULTRON PROCESS..."

        try:
            # We don't need to Popen here if Start_Ultron.bat already does it, 
            # but to keep it self-contained for the UI transition:
            self._launch_time = time.time()
            self._status = "ULTRON CORE INITIALIZED"
        except Exception as exc:
            self._launch_error = str(exc)
            self._status = f"LAUNCH ERROR: {exc}"
            return

        start = time.time()
        while True:
            elapsed = time.time() - start
            self._elapsed = elapsed
            self._prog    = min(0.97, elapsed / 20.0)

            if self._is_ultron_active():
                self._status = "U.L.T.R.O.N. INTERFACE ONLINE  ✓"
                self._prog   = 1.0
                self._done   = True
                return

            if elapsed > 45:
                self._launch_error = "timeout"
                self._status = "BOOT TIMEOUT — check ultron_ui.py for errors"
                return

            time.sleep(0.1)

    def _is_ultron_active(self) -> bool:
        """
        True only when a process OTHER than this script is running ultron_main.py.
        """
        own_pid = os.getpid()
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                if proc.info["pid"] == own_pid:
                    continue
                cmdline = proc.info.get("cmdline") or []
                if any("ultron_main.py" in arg for arg in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False


if __name__ == "__main__":
    app = UltronBoot()
    app.mainloop()
