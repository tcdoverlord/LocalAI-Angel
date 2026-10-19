import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import webbrowser

APP_TITLE = "LocalAI-Angel Control Center"
BG = "#0b1220"
PANEL = "#111c2e"
PANEL_ALT = "#17243a"
TEXT = "#e8f0ff"
MUTED = "#9eb0cc"
BLUE = "#3b82f6"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"

class AngelControlCenter:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("760x600")
        self.root.minsize(680, 560)
        self.root.configure(bg=BG)
        self.project_dir = self._find_project_dir()
        self._build_ui()
        self.refresh_files()

    def _find_project_dir(self):
        # When packaged as a one-file EXE, __file__ may point into a temporary
        # extraction directory. Locate the repository beside the EXE instead.
        anchor = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        required = ("INSTALL_ANGEL_V1.0.0.bat", "START_ANGEL.bat", "STOP_ANGEL.bat")
        for folder in (anchor, *anchor.parents):
            if all((folder / name).is_file() for name in required):
                return folder
        return anchor

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG, padx=24, pady=22)
        header.pack(fill="x")
        tk.Label(header, text="LOCALAI-ANGEL", bg=BG, fg=TEXT,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(header, text="CONTROL CENTER  •  Install, start, and stop your local AI stack",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.root, bg=PANEL, padx=20, pady=18,
                        highlightbackground="#263752", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 14))

        tk.Label(body, text="Stack actions", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(body, text="Each action runs your existing BAT file in its own console window so you can see progress and errors.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=650,
                 justify="left").pack(anchor="w", pady=(5, 16))

        self.install_btn = self._action_button(body, "INSTALL / REPAIR",
            "First-time setup or rebuild/repair an existing installation",
            AMBER, lambda: self.run_script("INSTALL_ANGEL_V1.0.0.bat"))
        self.start_btn = self._action_button(body, "START ANGEL",
            "Start the complete LocalAI-Angel Compose stack",
            GREEN, lambda: self.run_script("START_ANGEL.bat"))
        self.stop_btn = self._action_button(body, "STOP ANGEL",
            "Stop services without deleting persistent data or model volumes",
            RED, lambda: self.run_script("STOP_ANGEL.bat"))

        divider = tk.Frame(body, bg="#263752", height=1)
        divider.pack(fill="x", pady=16)
        tk.Label(body, text="Quick links", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        links = tk.Frame(body, bg=PANEL)
        links.pack(fill="x")
        self._link_button(links, "Angel Home Base", "http://127.0.0.1:8765/").pack(side="left", padx=(0, 8))
        self._link_button(links, "LocalAI", "http://127.0.0.1:8080/").pack(side="left", padx=(0, 8))
        self._link_button(links, "Angel Nexus", "http://127.0.0.1:8877/").pack(side="left")

        footer = tk.Frame(self.root, bg=BG, padx=24, pady=0)
        footer.pack(fill="x", pady=(0, 18))
        self.status = tk.Label(footer, text="Checking required files…", bg=BG, fg=MUTED,
                               font=("Segoe UI", 9), anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        tk.Button(footer, text="Refresh", command=self.refresh_files, bg=PANEL_ALT, fg=TEXT,
                  activebackground=BLUE, activeforeground="white", relief="flat",
                  padx=14, pady=7, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="right")

    def _action_button(self, parent, title, description, color, command):
        outer = tk.Frame(parent, bg=PANEL_ALT, padx=12, pady=10)
        outer.pack(fill="x", pady=5)
        button = tk.Button(outer, text=title, command=command, bg=color, fg="white",
                           activebackground=color, activeforeground="white", relief="flat",
                           width=19, pady=10, cursor="hand2", font=("Segoe UI", 10, "bold"))
        button.pack(side="left", padx=(0, 14))
        text_box = tk.Frame(outer, bg=PANEL_ALT)
        text_box.pack(side="left", fill="x", expand=True)
        tk.Label(text_box, text=description, bg=PANEL_ALT, fg=TEXT,
                 font=("Segoe UI", 10, "bold"), anchor="w", wraplength=390,
                 justify="left").pack(anchor="w")
        tk.Label(text_box, text="Runs the matching script from the application folder.",
                 bg=PANEL_ALT, fg=MUTED, font=("Segoe UI", 8), anchor="w").pack(anchor="w", pady=(3, 0))
        return button

    def _link_button(self, parent, label, url):
        return tk.Button(parent, text=label, command=lambda: webbrowser.open(url),
                         bg=PANEL_ALT, fg=TEXT, activebackground=BLUE,
                         activeforeground="white", relief="flat", padx=12, pady=8,
                         cursor="hand2", font=("Segoe UI", 9))

    def refresh_files(self):
        required = ["docker-compose.yaml", "docker-compose.nexus.override.yaml",
                    "docker-compose.angel-harness.yaml", "INSTALL_ANGEL_V1.0.0.bat",
                    "START_ANGEL.bat", "STOP_ANGEL.bat"]
        missing = [name for name in required if not (self.project_dir / name).is_file()]
        if missing:
            self.status.configure(text="Missing files: " + ", ".join(missing), fg="#fca5a5")
            for button, script in [(self.install_btn, "INSTALL_ANGEL_V1.0.0.bat"),
                                   (self.start_btn, "START_ANGEL.bat"),
                                   (self.stop_btn, "STOP_ANGEL.bat")]:
                button.configure(state="normal" if (self.project_dir / script).is_file() else "disabled")
        else:
            self.status.configure(text=f"Ready  •  Project folder: {self.project_dir}", fg="#86efac")
            self.install_btn.configure(state="normal")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")

    def run_script(self, filename):
        script = self.project_dir / filename
        if not script.is_file():
            messagebox.showerror("Script not found", f"Could not find:\n{script}\n\nPlace the Control Center beside the three BAT files in the LocalAI-Angel repository folder.")
            self.refresh_files()
            return
        if filename == "INSTALL_ANGEL_V1.0.0.bat":
            confirmed = messagebox.askyesno("Install / Repair LocalAI-Angel",
                "This runs the install/repair script and may rebuild Docker images.\n\n"
                "It is intended to preserve existing data/model volumes, but image builds can take time. Continue?")
            if not confirmed:
                return
        try:
            # Windows already knows how to launch .bat files. Using startfile
            # avoids cmd.exe /k quoting issues with paths and nested quotes.
            os.startfile(str(script))
            self.status.configure(text=f"Opened {filename} in its own command window.", fg="#93c5fd")
        except Exception as exc:
            messagebox.showerror("Could not launch script", str(exc))

if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconname("Angel Control Center")
    except Exception:
        pass
    app = AngelControlCenter(root)
    root.mainloop()
