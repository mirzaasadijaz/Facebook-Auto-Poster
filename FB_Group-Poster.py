import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import json
import csv
import os
import sys
import random
import time
import traceback
from datetime import datetime

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────────────────────────────────────────
CONFIG_FILE = "fb_poster_config.json"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ──────────────────────────────────────────────────────────────────────────────
# Main App
# ──────────────────────────────────────────────────────────────────────────────
class FacebookPosterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Auto Poster  ·  Developed by Asad Ijaz")
        self.root.geometry("980x820")
        self.root.resizable(True, True)
        self.root.minsize(900, 750)

        # ── State ──────────────────────────────────────────────────────────
        self.email_var        = tk.StringVar()
        self.password_var     = tk.StringVar()
        self.show_pass_var    = tk.BooleanVar(value=False)
        self.login_mode_var   = tk.StringVar(value="auto")   # "auto" | "manual"
        self.anonymous_var    = tk.BooleanVar(value=False)
        self.background_var   = tk.BooleanVar(value=False)
        self.user_data_dir    = tk.StringVar(value=r"C:\selenium_profile")
        self.cooldown_min_var = tk.IntVar(value=45)
        self.cooldown_max_var = tk.IntVar(value=70)

        self.image_paths            = []
        self.groups                 = []
        self.is_running             = False
        self.driver                 = None
        self._stop_event            = threading.Event()
        self._pause_event           = threading.Event()
        self.csv_path               = None
        self.consecutive_errors     = 0   # legacy — kept for general exceptions
        self.consecutive_same_errors = 0  # counts same-type errors in a row
        self.last_error_type        = None  # tracks the type of the last error

        self.success_count = 0
        self.fail_count    = 0

        self._build_ui()
        self._load_config()

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── Colour palette ────────────────────────────────────────────────
        BG        = "#f0f2f5"
        CARD      = "#ffffff"
        ACCENT    = "#1877f2"
        ACCENT2   = "#42b72a"
        DANGER    = "#fa3e3e"
        MUTED     = "#65676b"

        self.root.configure(bg=BG)

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=ACCENT, height=68)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(header, text="Facebook Auto Poster",
                 font=("Segoe UI", 17, "bold"), bg=ACCENT, fg="white"
                 ).pack(side=tk.LEFT, padx=18, pady=10)
        tk.Label(header, text="by Asad Ijaz",
                 font=("Segoe UI", 10), bg=ACCENT, fg="#d0e4ff"
                 ).pack(side=tk.LEFT, pady=10)

        chip_frame = tk.Frame(header, bg=ACCENT)
        chip_frame.pack(side=tk.RIGHT, padx=14)
        self.ok_chip  = tk.Label(chip_frame, text="✅  0", font=("Segoe UI", 10, "bold"),
                                 bg="#2ca52c", fg="white", padx=8, pady=3)
        self.ok_chip.pack(side=tk.LEFT, padx=4)
        self.fail_chip = tk.Label(chip_frame, text="❌  0", font=("Segoe UI", 10, "bold"),
                                  bg=DANGER, fg="white", padx=8, pady=3)
        self.fail_chip.pack(side=tk.LEFT, padx=4)

        # ── Progress bar ──────────────────────────────────────────────────
        prog_frame = tk.Frame(self.root, bg=BG)
        prog_frame.pack(fill=tk.X, side=tk.TOP, padx=12, pady=(8, 0))

        self.progress_label = tk.Label(prog_frame, text="Idle", font=("Segoe UI", 9),
                                       bg=BG, fg=MUTED)
        self.progress_label.pack(anchor="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Blue.Horizontal.TProgressbar",
                        troughcolor="#dde1e7", background=ACCENT,
                        lightcolor=ACCENT, darkcolor=ACCENT)

        self.progress = ttk.Progressbar(prog_frame, style="Blue.Horizontal.TProgressbar",
                                        mode="determinate", length=400)
        self.progress.pack(fill=tk.X, pady=(2, 4))

        # ── Status bar — packed FIRST at BOTTOM so it's always visible ────
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.root, textvariable=self.status_var,
                 bg="#dde1e7", fg=MUTED, anchor="w",
                 font=("Segoe UI", 9), relief=tk.SUNKEN, padx=8
                 ).pack(fill=tk.X, side=tk.BOTTOM)

        # ── Action bar — packed SECOND at BOTTOM so it stays above status ─
        action_bar = tk.Frame(self.root, bg=BG, pady=6)
        action_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=12)

        btn_cfg = dict(font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                       cursor="hand2", bd=0, padx=14, pady=7)

        self.start_btn = tk.Button(action_bar, text="▶  Start Posting",
                                   command=self.start_posting,
                                   bg=ACCENT2, fg="white", **btn_cfg)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = tk.Button(action_bar, text="■  Stop",
                                  command=self.stop_posting,
                                  bg="#e4e6eb", fg="#333", state=tk.DISABLED, **btn_cfg)
        self.stop_btn.pack(side=tk.LEFT)

        self.pause_btn = tk.Button(action_bar, text="⏸  Pause",
                                   command=self.toggle_pause,
                                   bg="#e4e6eb", fg="#333", state=tk.DISABLED, **btn_cfg)
        self.pause_btn.pack(side=tk.LEFT, padx=6)

        # Social icons — in action bar (right side), no more floating place()
        self._build_social_icons(action_bar, BG)

        tk.Button(action_bar, text="💾  Export Log",
                  command=self.export_log,
                  bg="#e4e6eb", fg="#333", **btn_cfg
                  ).pack(side=tk.RIGHT)

        tk.Button(action_bar, text="🗑  Clear Log",
                  command=self.clear_log,
                  bg="#e4e6eb", fg="#333", **btn_cfg
                  ).pack(side=tk.RIGHT, padx=6)

        # ── Notebook — fills ALL remaining space between progress and action bar
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=12, pady=(4, 0))

        self._build_main_tab(nb, CARD, BG, MUTED)
        self._build_settings_tab(nb, CARD, BG)

    # ──────────────────────────────────────────────────────────────────────
    def _build_main_tab(self, nb, CARD, BG, MUTED):
        tab = tk.Frame(nb, bg=BG)
        nb.add(tab, text="  🏠  Main  ")

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        # ── LEFT — scrollable so credential fields never push buttons off ──
        left_outer = tk.LabelFrame(tab, text=" Credentials & Post ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=CARD, fg="#1877f2")
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        left_outer.rowconfigure(0, weight=1)
        left_outer.columnconfigure(0, weight=1)

        # Canvas + scrollbar inside the LabelFrame
        _canvas = tk.Canvas(left_outer, bg=CARD, highlightthickness=0)
        _vsb    = tk.Scrollbar(left_outer, orient="vertical", command=_canvas.yview)
        _canvas.configure(yscrollcommand=_vsb.set)
        _vsb.grid(row=0, column=1, sticky="ns")
        _canvas.grid(row=0, column=0, sticky="nsew")

        left = tk.Frame(_canvas, bg=CARD, padx=12, pady=10)
        _win = _canvas.create_window((0, 0), window=left, anchor="nw")

        def _on_frame_configure(e):
            _canvas.configure(scrollregion=_canvas.bbox("all"))
        def _on_canvas_configure(e):
            _canvas.itemconfig(_win, width=e.width)
        def _on_mousewheel(e):
            _canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        left.bind("<Configure>", _on_frame_configure)
        _canvas.bind("<Configure>", _on_canvas_configure)
        _canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ── Login Mode ────────────────────────────────────────────────────
        mode_frame = tk.LabelFrame(left, text=" Login Mode ", bg=CARD, font=("Segoe UI", 9))
        mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        tk.Radiobutton(mode_frame, text="🤖  Auto Login  (enter email & password)",
                       variable=self.login_mode_var, value="auto",
                       command=self._on_login_mode_change,
                       bg=CARD, font=("Segoe UI", 9)
                       ).pack(anchor="w", padx=8, pady=2)
        tk.Radiobutton(mode_frame, text="👤  Manual Login  (you log in yourself in Chrome)",
                       variable=self.login_mode_var, value="manual",
                       command=self._on_login_mode_change,
                       bg=CARD, font=("Segoe UI", 9)
                       ).pack(anchor="w", padx=8, pady=2)

        # ── Credentials (shown only in auto mode) ─────────────────────────
        self._cred_frame = tk.Frame(left, bg=CARD)
        self._cred_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        tk.Label(self._cred_frame, text="Email:", bg=CARD, font=("Segoe UI", 9)
                 ).grid(row=0, column=0, sticky="w", pady=4)
        tk.Entry(self._cred_frame, textvariable=self.email_var, width=32,
                 font=("Segoe UI", 9)
                 ).grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        tk.Label(self._cred_frame, text="Password:", bg=CARD, font=("Segoe UI", 9)
                 ).grid(row=1, column=0, sticky="w", pady=4)
        pass_frame = tk.Frame(self._cred_frame, bg=CARD)
        pass_frame.grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        self.pass_entry = tk.Entry(pass_frame, textvariable=self.password_var,
                                   show="*", width=26, font=("Segoe UI", 9))
        self.pass_entry.pack(side=tk.LEFT)
        tk.Checkbutton(pass_frame, text="Show", variable=self.show_pass_var,
                       command=self._toggle_pass, bg=CARD,
                       font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=4)

        self._cred_frame.columnconfigure(1, weight=1)

        # ── Options ───────────────────────────────────────────────────────
        opt_frame = tk.LabelFrame(left, text=" Options ", bg=CARD, font=("Segoe UI", 9))
        opt_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        tk.Checkbutton(opt_frame, text="Post Anonymously",
                       variable=self.anonymous_var, bg=CARD,
                       font=("Segoe UI", 9)).pack(anchor="w", padx=6, pady=2)
        tk.Checkbutton(opt_frame, text="Use Background Image  (≤125 chars)",
                       variable=self.background_var, bg=CARD,
                       font=("Segoe UI", 9)).pack(anchor="w", padx=6, pady=2)

        # Post text
        tk.Label(left, text="Post Text:", bg=CARD,
                 font=("Segoe UI", 9, "bold")).grid(row=3, column=0, columnspan=2,
                                                     sticky="w", pady=(8, 2))
        self.post_text = scrolledtext.ScrolledText(left, width=38, height=10,
                                                   wrap=tk.WORD, font=("Segoe UI", 9))
        self.post_text.grid(row=4, column=0, columnspan=2, pady=4, sticky="ew")

        # Char counter
        self.char_count_var = tk.StringVar(value="0 chars")
        tk.Label(left, textvariable=self.char_count_var, bg=CARD,
                 fg=MUTED, font=("Segoe UI", 8)).grid(row=5, column=0, columnspan=2, sticky="e")
        self.post_text.bind("<KeyRelease>", self._update_char_count)

        # Images
        img_frame = tk.Frame(left, bg=CARD)
        img_frame.grid(row=6, column=0, columnspan=2, pady=6)
        tk.Button(img_frame, text="🖼  Add Images", command=self.add_images,
                  bg="#1877f2", fg="white", relief=tk.FLAT,
                  font=("Segoe UI", 9), padx=10, pady=4).pack(side=tk.LEFT, padx=4)
        tk.Button(img_frame, text="✕  Clear", command=self.clear_images,
                  bg="#e4e6eb", relief=tk.FLAT,
                  font=("Segoe UI", 9), padx=10, pady=4).pack(side=tk.LEFT)
        self.image_label = tk.Label(left, text="No images selected",
                                    bg=CARD, fg=MUTED, font=("Segoe UI", 8))
        self.image_label.grid(row=7, column=0, columnspan=2, pady=2)

        left.columnconfigure(1, weight=1)

        # ── RIGHT ─────────────────────────────────────────────────────────
        right = tk.Frame(tab, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Groups
        grp_frame = tk.LabelFrame(right, text=" Facebook Groups ",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#ffffff", fg="#1877f2", padx=10, pady=8)
        grp_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

        self.groups_text = scrolledtext.ScrolledText(grp_frame, width=46, height=12,
                                                     wrap=tk.WORD, font=("Courier New", 9))
        self.groups_text.pack(fill=tk.BOTH, expand=True)

        grp_btn_frame = tk.Frame(grp_frame, bg="#ffffff")
        grp_btn_frame.pack(pady=(4, 0))
        tk.Button(grp_btn_frame, text="📂  Import from File",
                  command=self.import_groups_file,
                  bg="#e4e6eb", relief=tk.FLAT,
                  font=("Segoe UI", 9), padx=8, pady=3).pack(side=tk.LEFT, padx=4)
        self.grp_count_lbl = tk.Label(grp_btn_frame, text="0 groups",
                                      bg="#ffffff", fg=MUTED, font=("Segoe UI", 8))
        self.grp_count_lbl.pack(side=tk.LEFT, padx=4)
        self.groups_text.bind("<KeyRelease>", self._update_group_count)

        # Log
        log_frame = tk.LabelFrame(right, text=" Activity Log ",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#ffffff", fg="#1877f2", padx=10, pady=8)
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame, width=46, height=12,
                                                  wrap=tk.WORD, state=tk.DISABLED,
                                                  bg="#1a1a2e", fg="#00d4aa",
                                                  font=("Courier New", 9),
                                                  insertbackground="white")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        right.columnconfigure(0, weight=1)

    # ──────────────────────────────────────────────────────────────────────
    def _build_settings_tab(self, nb, CARD, BG):
        tab = tk.Frame(nb, bg=BG)
        nb.add(tab, text="  ⚙️  Settings  ")

        card = tk.LabelFrame(tab, text=" Runtime Settings ",
                             font=("Segoe UI", 10, "bold"),
                             bg=CARD, fg="#1877f2", padx=16, pady=12)
        card.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        def lbl(r, text):
            tk.Label(card, text=text, bg=CARD, font=("Segoe UI", 10)
                     ).grid(row=r, column=0, sticky="w", pady=8, padx=(0, 20))

        # Chrome User Data Dir
        lbl(0, "Chrome User Data Dir:")
        dir_frame = tk.Frame(card, bg=CARD)
        dir_frame.grid(row=0, column=1, sticky="ew")
        tk.Entry(dir_frame, textvariable=self.user_data_dir,
                 width=36, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Button(dir_frame, text="…", width=3,
                  command=self.browse_directory, relief=tk.FLAT,
                  bg="#e4e6eb").pack(side=tk.LEFT, padx=4)

        # Cooldown
        lbl(1, "Cooldown between posts (seconds):")
        cd_frame = tk.Frame(card, bg=CARD)
        cd_frame.grid(row=1, column=1, sticky="w")
        tk.Label(cd_frame, text="Min:", bg=CARD, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Spinbox(cd_frame, from_=5, to=300, textvariable=self.cooldown_min_var,
                   width=6, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(2, 12))
        tk.Label(cd_frame, text="Max:", bg=CARD, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Spinbox(cd_frame, from_=5, to=600, textvariable=self.cooldown_max_var,
                   width=6, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=2)

        # Save / Load config
        lbl(2, "Configuration:")
        cfg_frame = tk.Frame(card, bg=CARD)
        cfg_frame.grid(row=2, column=1, sticky="w")
        tk.Button(cfg_frame, text="💾  Save Config",
                  command=self.save_config, bg="#1877f2", fg="white",
                  relief=tk.FLAT, font=("Segoe UI", 9), padx=10, pady=4
                  ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(cfg_frame, text="📂  Load Config",
                  command=self.load_config_dialog, bg="#e4e6eb",
                  relief=tk.FLAT, font=("Segoe UI", 9), padx=10, pady=4
                  ).pack(side=tk.LEFT)

        card.columnconfigure(1, weight=1)

    # ──────────────────────────────────────────────────────────────────────
    def _build_social_icons(self, parent, BG):
        """Social icon links — placed inside action bar (right side)."""
        icon_frame = tk.Frame(parent, bg=BG)
        icon_frame.pack(side=tk.RIGHT, padx=(0, 8))

        def open_link(url):
            webbrowser.open(url)

        def load_icon(path):
            abs_path = resource_path(path)
            if not os.path.exists(abs_path) or not PIL_AVAILABLE:
                return None
            img = Image.open(abs_path).resize((22, 22), Image.LANCZOS)
            return ImageTk.PhotoImage(img)

        self.icons = {}
        self.icons["linkedin"] = load_icon("icons/linkedin_icon.png")
        self.icons["github"]   = load_icon("icons/github_icon.png")
        self.icons["gmail"]    = load_icon("icons/gmail_icon.png")

        links = [
            ("linkedin", "https://www.linkedin.com/in/asad-ijaz-data-scientist/"),
            ("github",   "https://github.com/mirzaasadijaz"),
            ("gmail",    "https://mail.google.com/mail/?view=cm&fs=1&to=mirzaasadijaz@gmail.com"),
        ]
        for key, url in links:
            if self.icons.get(key):
                lbl = tk.Label(icon_frame, image=self.icons[key], cursor="hand2", bg=BG)
                lbl.pack(side=tk.LEFT, padx=4)
                lbl.bind("<Button-1>", lambda e, u=url: open_link(u))
            else:
                # Fallback text link if icon file missing
                text_map = {"linkedin": "in", "github": "gh", "gmail": "✉"}
                lbl = tk.Label(icon_frame, text=text_map.get(key, key),
                               cursor="hand2", bg=BG, fg="#1877f2",
                               font=("Segoe UI", 9, "underline"))
                lbl.pack(side=tk.LEFT, padx=4)
                lbl.bind("<Button-1>", lambda e, u=url: open_link(u))

    # ══════════════════════════════════════════════════════════════════════
    # UI helpers / events
    # ══════════════════════════════════════════════════════════════════════
    def _toggle_pass(self):
        self.pass_entry.config(show="" if self.show_pass_var.get() else "*")

    def _on_login_mode_change(self):
        """Show/hide credential fields based on selected login mode."""
        if self.login_mode_var.get() == "auto":
            self._cred_frame.grid()
        else:
            self._cred_frame.grid_remove()

    def _update_char_count(self, _event=None):
        txt = self.post_text.get("1.0", tk.END).strip()
        n = len(txt)
        color = "#fa3e3e" if (self.background_var.get() and n > 125) else "#65676b"
        self.char_count_var.set(f"{n} chars")
        # find label and recolour
        for child in self.post_text.master.winfo_children():
            if isinstance(child, tk.Label) and "chars" in (child.cget("textvariable") or ""):
                child.config(fg=color)

    def _update_group_count(self, _event=None):
        lines = [l for l in self.groups_text.get("1.0", tk.END).split("\n") if l.strip()]
        self.grp_count_lbl.config(text=f"{len(lines)} groups")

    def browse_directory(self):
        d = filedialog.askdirectory()
        if d:
            self.user_data_dir.set(d)

    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")]
        )
        if files:
            self.image_paths.extend(files)
            self.image_label.config(text=f"{len(self.image_paths)} image(s) selected")

    def clear_images(self):
        self.image_paths = []
        self.image_label.config(text="No images selected")

    def import_groups_file(self):
        path = filedialog.askopenfilename(
            title="Import Groups",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.groups_text.delete("1.0", tk.END)
            self.groups_text.insert("1.0", content.strip())
            self._update_group_count()
            self.log(f"📂 Imported groups from: {os.path.basename(path)}")

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"fb_poster_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if path:
            content = self.log_text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Exported", f"Log saved to:\n{path}")

    # ══════════════════════════════════════════════════════════════════════
    # Config save / load
    # ══════════════════════════════════════════════════════════════════════
    def save_config(self):
        cfg = {
            "email":        self.email_var.get(),
            "user_data_dir": self.user_data_dir.get(),
            "login_mode":   self.login_mode_var.get(),
            "anonymous":    self.anonymous_var.get(),
            "background":   self.background_var.get(),
            "cooldown_min": self.cooldown_min_var.get(),
            "cooldown_max": self.cooldown_max_var.get(),
            "groups":       self.groups_text.get("1.0", tk.END).strip(),
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        messagebox.showinfo("Saved", f"Config saved to {CONFIG_FILE}")

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.email_var.set(cfg.get("email", ""))
                self.user_data_dir.set(cfg.get("user_data_dir", r"C:\selenium_profile"))
                self.login_mode_var.set(cfg.get("login_mode", "auto"))
                self._on_login_mode_change()
                self.anonymous_var.set(cfg.get("anonymous", False))
                self.background_var.set(cfg.get("background", False))
                self.cooldown_min_var.set(cfg.get("cooldown_min", 45))
                self.cooldown_max_var.set(cfg.get("cooldown_max", 70))
                groups = cfg.get("groups", "")
                if groups:
                    self.groups_text.delete("1.0", tk.END)
                    self.groups_text.insert("1.0", groups)
                    self._update_group_count()
            except Exception:
                pass  # silently skip malformed config

    def load_config_dialog(self):
        path = filedialog.askopenfilename(
            title="Load Config",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            global CONFIG_FILE
            CONFIG_FILE = path
            self._load_config()
            messagebox.showinfo("Loaded", f"Config loaded from:\n{path}")

    # ══════════════════════════════════════════════════════════════════════
    # Logging (always called from main thread via root.after)
    # ══════════════════════════════════════════════════════════════════════
    def log(self, message):
        ts  = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.root.after(0, self._append_log, line)

    def _append_log(self, line):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _set_status(self, msg):
        self.root.after(0, self.status_var.set, msg)

    def _update_progress(self, current, total):
        def _do():
            pct = int(current / total * 100) if total else 0
            self.progress["value"] = pct
            self.progress_label.config(text=f"Group {current} of {total}  ({pct}%)")
        self.root.after(0, _do)

    def _update_chips(self):
        def _do():
            self.ok_chip.config(text=f"✅  {self.success_count}")
            self.fail_chip.config(text=f"❌  {self.fail_count}")
        self.root.after(0, _do)

    # ══════════════════════════════════════════════════════════════════════
    # Validation
    # ══════════════════════════════════════════════════════════════════════
    def validate_inputs(self):
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("Missing dependency",
                                 "Selenium is not installed.\n  pip install selenium")
            return False

        if self.login_mode_var.get() == "auto":
            if not self.email_var.get().strip():
                messagebox.showerror("Error", "Please enter your Facebook email.")
                return False
            if not self.password_var.get():
                messagebox.showerror("Error", "Please enter your Facebook password.")
                return False

        if not self.post_text.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter post text.")
            return False
        if not self.groups_text.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter at least one group ID.")
            return False

        mn, mx = self.cooldown_min_var.get(), self.cooldown_max_var.get()
        if mn > mx:
            messagebox.showerror("Error", "Cooldown Min must be ≤ Cooldown Max.")
            return False
        return True

    # ══════════════════════════════════════════════════════════════════════
    # Start / Stop
    # ══════════════════════════════════════════════════════════════════════
    def start_posting(self):
        if not self.validate_inputs():
            return

        self.is_running              = True
        self.success_count           = 0
        self.fail_count              = 0
        self.consecutive_errors      = 0
        self.consecutive_same_errors = 0
        self.last_error_type         = None
        self._stop_event.clear()
        self._pause_event.clear()

        # ── Create timestamped CSV for this session ───────────────────────
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        folder_name = "result"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        self.csv_path = f"result/fb_poster_results_{ts}.csv"
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["Datetime", "Group ID", "Status", "Note"])
        self.log(f"📄  Results CSV: {self.csv_path}")

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL)
        self.status_var.set("Running…")
        self.progress["value"] = 0
        self._update_chips()

        groups_raw = self.groups_text.get("1.0", tk.END).strip()
        self.groups = [g.strip() for g in groups_raw.splitlines() if g.strip()]

        threading.Thread(target=self._run_posting, daemon=True).start()

    def stop_posting(self):
        self.is_running = False
        self._stop_event.set()
        self._pause_event.clear()   # unblock thread so it can see stop
        self.log("🛑 Stop requested — will halt after current group.")
        self._set_status("Stopping…")

    def toggle_pause(self):
        if self._pause_event.is_set():
            # ── Resume ────────────────────────────────────────────────────
            self._pause_event.clear()
            self.pause_btn.config(text="⏸  Pause", bg="#e4e6eb", fg="#333")
            self._set_status("Running…")
            self.log("▶️  Resumed.")
        else:
            # ── Pause ─────────────────────────────────────────────────────
            self._pause_event.set()
            self.pause_btn.config(text="▶  Resume", bg="#f5a623", fg="white")
            self._set_status("⏸  Paused — click Resume to continue.")
            self.log("⏸  Paused — click Resume to continue.")

    def _pause_check(self):
        """Call this in the background thread at safe checkpoints.
        Blocks until resumed or stopped. Returns True if stopped."""
        while self._pause_event.is_set():
            if self._stop_event.is_set():
                return True
            time.sleep(0.5)
        return self._stop_event.is_set()

    def _finish_ui(self):
        def _do():
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.DISABLED, text="⏸  Pause", bg="#e4e6eb")
            self._pause_event.clear()
        self.root.after(0, _do)

    # ══════════════════════════════════════════════════════════════════════
    # Core automation (background thread)
    # ══════════════════════════════════════════════════════════════════════
    def _run_posting(self):
        FB_EMAIL          = self.email_var.get().strip()
        FB_PASSWORD       = self.password_var.get()
        LOGIN_MODE        = self.login_mode_var.get()   # "auto" | "manual"
        POST_ANONYMOUSLY  = self.anonymous_var.get()
        USE_BACKGROUND    = self.background_var.get()
        POST_TEXT         = self.post_text.get("1.0", tk.END).strip()
        IMAGE_PATHS       = self.image_paths.copy()
        USER_DATA_DIR     = self.user_data_dir.get()
        CD_MIN            = self.cooldown_min_var.get()
        CD_MAX            = self.cooldown_max_var.get()
        TOTAL             = len(self.groups)

        # Validate images on disk
        for img in IMAGE_PATHS:
            if not os.path.exists(img):
                self.log(f"⚠️  Image not found — will skip: {img}")

        # ── Chrome options ────────────────────────────────────────────────
        options = Options()
        options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.log("🚀  Launching Chrome…")

        try:
            driver = webdriver.Chrome(options=options)
            self.driver = driver
            wait    = WebDriverWait(driver, 25)
            actions = ActionChains(driver)

            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"}
            )

            # ── Login ─────────────────────────────────────────────────────
            # Step 1: Always open /login page first (works for both modes).
            # Step 2: After credentials submitted (or user logs in manually),
            #         wait until URL becomes facebook.com/ or facebook.com/home.php
            #         — this also handles human-verification / 2FA pages naturally.
            self.log("🌐  Opening Facebook login page…")
            driver.get("https://www.facebook.com/login")
            time.sleep(random.uniform(4, 6))

            # Check if we're already logged in (profile was saved in user-data-dir)
            already_logged_in = self._is_home_page(driver)

            if already_logged_in:
                self.log("ℹ️  Already logged in (saved session) — proceeding.")

            elif LOGIN_MODE == "auto":
                try:
                    # ── Fill email ────────────────────────────────────────
                    email_inp = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[name='email']")
                    ))
                    email_inp.click()
                    email_inp.clear()
                    for ch in FB_EMAIL:
                        email_inp.send_keys(ch)
                        time.sleep(random.uniform(0.04, 0.10))
                    time.sleep(random.uniform(0.8, 1.4))

                    # ── Fill password ─────────────────────────────────────
                    pass_inp = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[name='pass']")
                    ))
                    pass_inp.click()
                    pass_inp.clear()
                    for ch in FB_PASSWORD:
                        pass_inp.send_keys(ch)
                        time.sleep(random.uniform(0.04, 0.10))
                    time.sleep(random.uniform(0.8, 1.4))

                    # ── Click Log in button ───────────────────────────────
                    login_btn = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div[aria-label='Log in'][role='button']")
                    ))
                    login_btn.click()
                    self.log("🔐  Credentials submitted — waiting for home page…")
                    self.log("⏳  (Human verification / 2FA will be waited on automatically)")

                    # Wait for home page — handles 2FA / captcha too
                    if not self._wait_for_home(driver):
                        self.log("🛑  Did not reach home page — aborting.")
                        return
                    self.log("✅  Logged in successfully!")

                except Exception as e:
                    self.log(f"⚠️  Auto-login error: {e}")
                    self.log("⏳  Waiting for manual completion…")
                    if not self._wait_for_home(driver):
                        self.log("🛑  Login not completed — aborting.")
                        return

            else:  # manual mode
                self.log("👤  MANUAL LOGIN — Please log in in the Chrome window.")
                self.log("⏳  Waiting until you reach the home/feed page…")
                self._set_status("Waiting for manual login…")
                if not self._wait_for_home(driver):
                    self.log("🛑  Login wait cancelled or timed out.")
                    return
                self.log("✅  Manual login confirmed — starting to post!")

            self.log(f"\n🎭 Anonymous: {'ON' if POST_ANONYMOUSLY else 'OFF'}")
            self.log(f"🎨 Background: {'ON' if USE_BACKGROUND else 'OFF'}\n")

            # ── Group loop ────────────────────────────────────────────────
            for idx, group in enumerate(self.groups, start=1):
                if self._stop_event.is_set():
                    self.log("🛑  Stopped by user.")
                    break

                # ── Pause checkpoint ──────────────────────────────────────
                if self._pause_check():
                    self.log("🛑  Stopped while paused.")
                    break

                self._update_progress(idx, TOTAL)
                self._set_status(f"Group {idx}/{TOTAL}: {group}")
                self.log(f"\n[{idx}/{TOTAL}]  ➜  {group}")

                try:
                    driver.get(f"https://www.facebook.com/groups/{group}")
                    time.sleep(random.uniform(6, 10))

                    # ── Check if group page itself is unavailable ─────────
                    # (deleted group, banned, or restricted) — just skip, never terminate
                    group_src = driver.page_source
                    UNAVAILABLE_MARKERS = [
                        "This content isn\u2019t available",
                        "This content isn't available",
                        "This Page Isn\u2019t Available",
                        "This Page Isn't Available",
                        "page you requested cannot be displayed",
                        "content isn\u2019t available right now",
                    ]
                    group_unavailable = any(m in group_src for m in UNAVAILABLE_MARKERS)
                    if group_unavailable:
                        reason = "Group page unavailable (deleted, banned, or restricted)"
                        self.log(f"   ⚠️  {reason} — skipping.")
                        self.fail_count += 1
                        self._update_chips()
                        self._csv_write(group, "Skipped", reason)
                        continue   # never counts toward consecutive termination

                    self._close_chat_windows(driver)

                    # ── Open post box ─────────────────────────────────────
                    self.log("   Clicking Write something / post box...")
                    try:
                        post_box = wait.until(EC.element_to_be_clickable((By.XPATH,
                            "//div[@role='button']//span[contains(text(),'Write') or "
                            "contains(text(),'Escribe') or contains(text(),'Crear')]"
                        )))
                        post_box.click()
                    except Exception:
                        raise Exception("Post box (Write something) not found on group page")
                    time.sleep(5)

                    # ── Anonymous toggle ──────────────────────────────────
                    if POST_ANONYMOUSLY:
                        self._enable_anonymous(driver, wait, actions)

                    # ── Focus textbox ─────────────────────────────────────
                    self.log("   Focusing post textbox...")
                    try:
                        textbox = wait.until(EC.presence_of_element_located((By.XPATH,
                            "//div[@role='dialog']//div[@role='textbox' and @contenteditable='true']"
                        )))
                    except Exception:
                        raise Exception("Post textbox not found inside dialog")
                    actions.move_to_element(textbox).click().perform()
                    time.sleep(random.uniform(1, 2))

                    # ── Paste text ────────────────────────────────────────
                    text_to_paste = POST_TEXT
                    if USE_BACKGROUND:
                        text_to_paste = POST_TEXT[:125]
                        self._apply_background(driver, wait)

                    if pyperclip:
                        pyperclip.copy(text_to_paste)
                        time.sleep(0.4)
                        actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
                    else:
                        textbox.send_keys(text_to_paste)

                    self.log("   Text pasted.")
                    time.sleep(random.uniform(3, 4))

                    self._close_chat_windows(driver)

                    # ── Image upload ──────────────────────────────────────
                    if not USE_BACKGROUND and IMAGE_PATHS:
                        self._upload_images(driver, wait, IMAGE_PATHS)

                    # ── Click Post/Submit ─────────────────────────────────
                    time.sleep(random.uniform(2, 3))
                    try:
                        self._click_post_button(driver, wait, actions)
                    except Exception:
                        raise Exception("Post/Submit button not found in dialog")

                    # Wait for Facebook to process the post
                    time.sleep(4)

                    # ── Check for Facebook error dialog ───────────────────
                    error_text, error_type = self._check_rate_limit(driver, group)

                    if error_text:
                        self.fail_count += 1
                        self._update_chips()
                        self._csv_write(group, "Failed", error_text)

                        # Same-type consecutive tracking
                        if error_type == self.last_error_type:
                            self.consecutive_same_errors += 1
                        else:
                            self.consecutive_same_errors = 1
                            self.last_error_type = error_type

                        remaining = 5 - self.consecutive_same_errors
                        self.log(
                            f"   Error ({error_type}) #{self.consecutive_same_errors}/5"
                            f" — {remaining} more of the same type before halt."
                        )

                        if self.consecutive_same_errors >= 5:
                            self.log(
                                f"   5 consecutive '{error_type}' errors — "
                                "terminating to protect account."
                            )
                            break
                        else:
                            self.log("   Skipping to next group.")
                            continue

                    # ── Clean post ────────────────────────────────────────
                    self.consecutive_same_errors = 0
                    self.last_error_type         = None
                    self.consecutive_errors      = 0
                    self.success_count += 1
                    self._update_chips()
                    self.log("   POST SUCCESSFUL")
                    self._csv_write(group, "Success", "")

                    # ── Cooldown (interruptible) ───────────────────────────
                    cooldown = random.randint(CD_MIN, CD_MAX)
                    self.log(f"   Cooling down {cooldown}s...")
                    for _ in range(cooldown):
                        if self._stop_event.is_set():
                            break
                        if self._pause_event.is_set():
                            self.log("   Paused during cooldown...")
                            if self._pause_check():
                                break
                            self.log("   Cooldown resumed.")
                        time.sleep(1)

                except Exception as e:
                    # General / unexpected errors — write specific reason to CSV
                    err_msg = str(e)
                    self.log(f"   ERROR for group '{group}': {err_msg}")
                    self.fail_count += 1
                    self._update_chips()
                    self._csv_write(group, "Failed", err_msg[:300])

                    # General exceptions count as same-type only if message matches
                    err_type = "general_exception"
                    if err_type == self.last_error_type:
                        self.consecutive_errors += 1
                    else:
                        self.consecutive_errors = 1
                        self.last_error_type = err_type

                    if self.consecutive_errors >= 5:
                        self.log("   5 consecutive general errors — terminating.")
                        break
                    continue

            self.log(f"\n🏁  Done.  ✅ {self.success_count} succeeded  ❌ {self.fail_count} failed")
            if self.csv_path:
                self.log(f"📄  Full results saved → {os.path.abspath(self.csv_path)}")
            try:
                driver.quit()
            except Exception:
                pass

        except Exception as e:
            self.log(f"❌  Fatal error: {e}\n{traceback.format_exc()}")
        finally:
            self.is_running = False
            self._finish_ui()
            self._set_status(f"Completed — ✅ {self.success_count}  ❌ {self.fail_count}")
            self.root.after(0, lambda: self.progress.__setitem__("value", 100))

    # ══════════════════════════════════════════════════════════════════════
    # Selenium helper methods
    # ══════════════════════════════════════════════════════════════════════

    def _is_home_page(self, driver) -> bool:
        """Return True if current URL is facebook.com/home.php or facebook.com/ (root)."""
        try:
            url = driver.current_url.rstrip("/").lower()
            return url in (
                "https://www.facebook.com",
                "https://www.facebook.com/home.php",
                "https://facebook.com",
                "https://facebook.com/home.php",
            )
        except Exception:
            return False

    def _wait_for_home(self, driver, poll_interval=3, timeout=600) -> bool:
        """
        Block until the browser URL becomes facebook.com/ or facebook.com/home.php.
        Works for BOTH auto-login (after submit) and manual login (user types creds).
        Also handles 2FA / human-verification pages — just waits them out.
        Respects Stop and Pause buttons.
        Returns True when home reached, False on stop/timeout.
        """
        deadline = time.time() + timeout
        attempt  = 0

        while time.time() < deadline:
            if self._stop_event.is_set():
                return False
            if self._pause_event.is_set():
                time.sleep(0.5)
                continue

            attempt += 1
            try:
                if self._is_home_page(driver):
                    return True

                url = driver.current_url.lower()
                if attempt % 5 == 1:
                    self.log(f"   ⏳  Waiting for home… [{attempt}] current: {url[:60]}")

            except Exception:
                pass  # driver briefly unavailable during navigation

            time.sleep(poll_interval)

        self.log("⏰  Wait for home page timed out (10 min).")
        return False

    def _csv_write(self, group: str, status: str, note: str):
        """Append one result row to the session CSV file."""
        if not self.csv_path:
            return
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    group,
                    status,
                    note,
                ])
        except Exception as e:
            self.log(f"⚠️  CSV write error: {e}")

    def _close_chat_windows(self, driver):
        try:
            btns = driver.find_elements(By.XPATH,
                "//div[@aria-label='Close chat' or @aria-label='Close tab' "
                "or @aria-label='Cerrar chat']")
            for btn in btns:
                driver.execute_script("arguments[0].click();", btn)
                self.log("   🧹  Closed stray chat window.")
                time.sleep(random.uniform(0.9, 1.3))
        except Exception:
            pass

    def _enable_anonymous(self, driver, wait, actions):
        self.log("   🎭  Trying to enable anonymous posting…")
        toggle = None

        # Strategy 1 – walk up from label text
        try:
            spans = driver.find_elements(By.XPATH,
                "//div[@role='dialog']//span[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                "'abcdefghijklmnopqrstuvwxyz'),'anonymously')]")
            if spans:
                for level in range(1, 8):
                    parent = spans[0]
                    for _ in range(level):
                        parent = parent.find_element(By.XPATH, "..")
                    if parent.get_attribute("role") in ("switch", "button", "checkbox"):
                        toggle = parent
                        self.log(f"   ✓  Toggle found (level {level})")
                        break
        except Exception:
            pass

        # Strategy 2 – scan all switches in dialog
        if not toggle:
            try:
                switches = driver.find_elements(By.XPATH,
                    "//div[@role='dialog']//*[@role='switch' or "
                    "(@type='checkbox' and @role='switch')]")
                for sw in switches:
                    label = (sw.get_attribute("aria-label") or "").lower()
                    if "anonym" in label:
                        toggle = sw
                        self.log("   ✓  Toggle found via aria-label")
                        break
            except Exception:
                pass

        # Strategy 3 – clickable row containing the word
        if not toggle:
            try:
                containers = driver.find_elements(By.XPATH,
                    "//div[@role='dialog']//div[contains(.,'Post anonymously')]")
                for c in containers[:5]:
                    if c.get_attribute("tabindex") or c.get_attribute("role") in ("button","switch"):
                        toggle = c
                        self.log("   ✓  Toggle found via container row")
                        break
            except Exception:
                pass

        if toggle:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", toggle)
            time.sleep(0.8)
            if toggle.get_attribute("aria-checked") != "true":
                try:
                    actions.move_to_element(toggle).pause(0.4).click().perform()
                except Exception:
                    driver.execute_script("arguments[0].click();", toggle)
                time.sleep(random.uniform(2, 3))
                # Dismiss "Got it" popup if present
                try:
                    got_it = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH,
                        "//div[@role='button'][.//span[text()='Got it' or text()='Entendido']]"
                        " | //span[text()='Got it']//ancestor::div[@role='button'][1]"
                    )))
                    got_it.click()
                    time.sleep(random.uniform(1, 2))
                    self.log("   ✅  'Got it' popup dismissed")
                except Exception:
                    pass
                self.log("   ✅  Anonymous posting ENABLED")
            else:
                self.log("   ℹ️  Anonymous already ON")
        else:
            self.log("   ⚠️  Anonymous toggle not found — group may not support it.")

    def _apply_background(self, driver, wait):
        self.log("   🎨  Selecting background…")
        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@aria-label='Show Background Options']")
            ))
            btn.click()
            time.sleep(2)
            choices = ["purple magenta", "red blue", "yellow", "green"]
            choice  = random.choice(choices)
            bg_btn  = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//*[contains(@aria-label,'{choice}')]")
            ))
            bg_btn.click()
            time.sleep(2)
            self.log(f"   ✅  Background '{choice}' selected")
        except Exception as e:
            self.log(f"   ⚠️  Background selection failed: {e}")

    def _upload_images(self, driver, wait, paths):
        self.log("   🖼️  Uploading images…")
        try:
            abs_paths   = [os.path.abspath(p) for p in paths if os.path.exists(p)]
            files_str   = "\n".join(abs_paths)
            file_input  = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@role='dialog']//input[@type='file']")
            ))
            file_input.send_keys(files_str)
            self.log(f"   ✅  {len(abs_paths)} image(s) uploaded")
            time.sleep(5 + len(abs_paths) * 3)
        except Exception as e:
            self.log(f"   ⚠️  Image upload failed: {e}")

    def _click_post_button(self, driver, wait, actions):
        self.log("   🔍  Looking for Post/Submit button…")

        # All known aria-labels + text variants (English + Spanish)
        ARIA_LABELS = ["Post", "Submit", "Enviar", "Publicar", "Publish"]
        SPAN_TEXTS  = ["Post", "Submit", "Enviar", "Publicar", "Publish"]

        btn = None

        # ── Pass 1: instant find_elements (no timeout cost) ───────────────
        # Try aria-label first — fastest and most reliable
        for label in ARIA_LABELS:
            els = driver.find_elements(
                By.XPATH,
                f"//div[@role='dialog']//div[@role='button' and @aria-label='{label}']"
                f" | //div[@role='dialog']//div[@aria-label='{label}']"
            )
            for el in els:
                try:
                    if el.is_displayed() and el.is_enabled():
                        btn = el
                        self.log(f"   ✓  Found via aria-label='{label}'")
                        break
                except Exception:
                    continue
            if btn:
                break

        # Try span text → ancestor button
        if not btn:
            for txt in SPAN_TEXTS:
                els = driver.find_elements(
                    By.XPATH,
                    f"//div[@role='dialog']//span[normalize-space(text())='{txt}']"
                    f"//ancestor::div[@role='button'][1]"
                )
                for el in els:
                    try:
                        if el.is_displayed() and el.is_enabled():
                            btn = el
                            self.log(f"   ✓  Found via span text='{txt}'")
                            break
                    except Exception:
                        continue
                if btn:
                    break

        # ── Pass 2: broad button text scan (still instant) ────────────────
        if not btn:
            self.log("   ⏳  Trying broad button scan…")
            terms = {"post", "submit", "enviar", "publicar", "publish"}
            all_btns = driver.find_elements(
                By.XPATH, "//div[@role='dialog']//div[@role='button']"
            )
            for el in all_btns:
                try:
                    label = (el.get_attribute("aria-label") or "").strip().lower()
                    text  = (el.text or "").strip().lower()
                    if any(t == label or t == text for t in terms):
                        if el.is_displayed() and el.is_enabled():
                            btn = el
                            self.log(f"   ✓  Found via broad scan: '{el.text or label}'")
                            break
                except Exception:
                    continue

        # ── Pass 3: short wait — single combined XPath (8s max, not 25×6) ─
        if not btn:
            self.log("   ⏳  Still not found — waiting up to 8s…")
            combined = (
                " | ".join(
                    f"//div[@role='dialog']//div[@aria-label='{l}']" for l in ARIA_LABELS
                )
            )
            try:
                btn = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, combined))
                )
                self.log("   ✓  Found after short wait")
            except Exception:
                pass

        if not btn:
            raise Exception("Post/Submit button not found after all strategies.")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(random.uniform(0.6, 1.2))

        try:
            actions.move_to_element(btn).click().perform()
            self.log("   ✅  Clicked (ActionChains)")
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", btn)
                self.log("   ✅  Clicked (JavaScript)")
            except Exception:
                btn.click()
                self.log("   ✅  Clicked (Direct)")

    def _check_rate_limit(self, driver, group) -> tuple:
        """
        Scan the page for Facebook error dialogs after clicking Post.

        Returns: (error_text: str, error_type: str) if an error is found,
                 (None, None) if the post was clean.

        error_type is used by the caller to track same-type consecutive errors.
        Only 5 of the SAME type in a row triggers termination.

        NOTE: 'This content is not available' is NOT included here — that is
        a group-page-level issue handled before posting (group deleted/banned).
        """

        # ── Rate-limit patterns (type: "rate_limit") ─────────────────────
        RATE_LIMIT_PATTERNS = [
            "We limit how often you can post",
            "You can try again later",
        ]

        # ── Server / request error patterns (type: "server_error") ────────
        SERVER_ERROR_PATTERNS = [
            "We\u2019re having trouble completing",   # curly apostrophe (real FB)
            "We're having trouble completing",
            "having trouble completing your request",
            "We\u2019re sorry, but something went wrong",
            "Something went wrong. Please try again",
        ]

        try:
            page_src = driver.page_source
        except Exception:
            return None, None   # driver lost — outer except handles it

        # ── Check rate-limit patterns ─────────────────────────────────────
        for pat in RATE_LIMIT_PATTERNS:
            if pat in page_src:
                error_text = self._extract_error_text(driver, pat) or pat
                self.log(f"   Rate-limit error detected: {error_text[:120]}")
                self._write_failed_groups_txt(group, error_text)
                return error_text, "rate_limit"

        # ── Check server error patterns ───────────────────────────────────
        for pat in SERVER_ERROR_PATTERNS:
            if pat in page_src:
                error_text = self._extract_error_text(driver, pat) or pat
                self.log(f"   Server error detected: {error_text[:120]}")
                self._write_failed_groups_txt(group, error_text)
                return error_text, "server_error"

        # ── Strategy B: Give feedback button (catches unlabeled dialogs) ──
        fb_btns = driver.find_elements(
            By.XPATH,
            "//div[@role='button' and normalize-space(.)='Give feedback']"
        )
        if fb_btns:
            error_text = "Facebook error dialog detected (Give feedback button present)"
            self.log(f"   {error_text}")
            self._write_failed_groups_txt(group, error_text)
            return error_text, "fb_error_dialog"

        return None, None   # No error — post was successful

    def _extract_error_text(self, driver, pattern: str) -> str:
        """Try to extract clean readable error text from the page using the matched pattern."""
        try:
            els = driver.find_elements(
                By.XPATH, f'//div[contains(., "{pattern}")]'
            )
            for el in els:
                t = (el.text or "").strip()
                if 10 < len(t) < 400:
                    return t
        except Exception:
            pass
        return ""

    def _write_failed_groups_txt(self, group: str, error_text: str):
        """Append to legacy failed_groups.txt for backward compatibility."""
        try:
            with open("failed_groups.txt", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}  |  Group: {group}  |  {error_text}\n")
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = FacebookPosterGUI(root)
    root.mainloop()