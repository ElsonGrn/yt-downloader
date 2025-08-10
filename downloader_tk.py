# downloader_tk.py – Modern GUI, echte Qualitäten, Settings, Windows-Theme, klickbarer Dateilink
import os, sys, json, threading, platform
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from yt_dlp import YoutubeDL

APP_NAME = "YTDL-Modern"

# -------- Konfig (persistiert unter ~/.ytdl-modern/config.json) --------
DEFAULT_CFG = {
    "music_dir": os.path.join(os.path.expanduser("~"), "Music"),
    "video_dir": os.path.join(os.path.expanduser("~"), "Videos"),
    "last_theme": None,  # light/dark; wenn None -> Windows-Theme
}
def _config_dir():
    home = os.path.expanduser("~")
    path = os.path.join(home, ".ytdl-modern")
    os.makedirs(path, exist_ok=True)
    return path
CFG_PATH = os.path.join(_config_dir(), "config.json")

def load_config():
    cfg = DEFAULT_CFG.copy()
    try:
        if os.path.isfile(CFG_PATH):
            with open(CFG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in DEFAULT_CFG:
                if k in data:
                    cfg[k] = data[k]
    except Exception:
        pass
    return cfg

def save_config(cfg):
    try:
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Config speichern fehlgeschlagen:", e, file=sys.stderr)

# -------- Windows-Theme erkennen --------
def detect_windows_theme():
    if platform.system().lower() != "windows":
        return "light"
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        val, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        winreg.CloseKey(k)
        return "light" if val == 1 else "dark"
    except Exception:
        return "light"

def get_start_theme(cfg):
    return cfg.get("last_theme") or detect_windows_theme()

def theme_to_bootstrap(kind: str):
    return "flatly" if kind == "light" else "darkly"

# -------- ffmpeg (falls mit PyInstaller gebündelt) --------
def get_ffmpeg_location():
    base = getattr(sys, "_MEIPASS", None)
    if base:
        cand = os.path.join(base, "ffmpeg")
        if os.path.isdir(cand):
            return cand
    return None

def ydl_basic_opts():
    opts = {"quiet": True, "noprogress": True}
    ffdir = get_ffmpeg_location()
    if ffdir:
        opts["ffmpeg_location"] = ffdir
    return opts

# -------- Qualitäten pro URL ermitteln --------
def probe_available_resolutions(url: str):
    """
    Liefert Liste vorhandener Video-Höhen (als Strings), z. B. ['480','720','1080'].
    """
    opts = ydl_basic_opts()
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    heights = set()
    for f in info.get("formats", []):
        if f.get("vcodec") and f.get("vcodec") != "none":
            h = f.get("height")
            if isinstance(h, int) and h > 0:
                heights.add(h)
    vals = sorted(heights)  # aufsteigend
    # Optional auf gängige Raster filtern, Reihenfolge erhalten
    common = ["2160","1440","1080","720","480","360","240"]
    if vals:
        s = [str(v) for v in vals]
        filtered = [v for v in common if v in s]
        return filtered or s
    return []

# -------- yt-dlp Optionen --------
def build_opts(fmt: str, quality: str, progress_hook, post_hook, cfg):
    opts = {
        "quiet": True,
        "noprogress": False,
        "progress_hooks": [progress_hook],          # Download-Status
        "postprocessor_hooks": [post_hook],         # finaler Dateipfad
        "outtmpl": None,
    }
    ffdir = get_ffmpeg_location()
    if ffdir:
        opts["ffmpeg_location"] = ffdir

    if fmt == "MP3":
        opts["outtmpl"] = os.path.join(cfg["music_dir"], "%(title)s.%(ext)s")
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality  # "128","192","256","320"
            }]
        })
    else:
        opts["outtmpl"] = os.path.join(cfg["video_dir"], "%(title)s.%(ext)s")
        vfmt = f"bestvideo[height<={quality}]+bestaudio/best"
        opts.update({
            "format": vfmt,
            "merge_output_format": "mp4"
        })
    return opts

# -------- Settings Dialog --------
class SettingsDialog(tb.Toplevel):
    def __init__(self, master, cfg):
        super().__init__(master)
        self.title("Einstellungen")
        self.resizable(False, False)
        self.cfg = cfg
        p = {"padx": 10, "pady": 8}

        tb.Label(self, text="Zielordner MP3").grid(row=0, column=0, sticky="w", **p)
        self.music_var = tb.StringVar(value=cfg["music_dir"])
        tb.Entry(self, textvariable=self.music_var, width=54).grid(row=0, column=1, **p)
        tb.Button(self, text="Wählen…", bootstyle=SECONDARY, command=self.pick_music).grid(row=0, column=2, **p)

        tb.Label(self, text="Zielordner MP4").grid(row=1, column=0, sticky="w", **p)
        self.video_var = tb.StringVar(value=cfg["video_dir"])
        tb.Entry(self, textvariable=self.video_var, width=54).grid(row=1, column=1, **p)
        tb.Button(self, text="Wählen…", bootstyle=SECONDARY, command=self.pick_video).grid(row=1, column=2, **p)

        tb.Label(self, text="Start-Theme").grid(row=2, column=0, sticky="w", **p)
        self.theme_var = tb.StringVar(value=get_start_theme(cfg))
        tb.Radiobutton(self, text="Hell",   variable=self.theme_var, value="light").grid(row=2, column=1, sticky="w", **p)
        tb.Radiobutton(self, text="Dunkel", variable=self.theme_var, value="dark").grid(row=2, column=2, sticky="w", **p)

        bar = tb.Frame(self); bar.grid(row=3, column=0, columnspan=3, sticky="e", **p)
        tb.Button(bar, text="Abbrechen", bootstyle=SECONDARY, command=self.destroy).pack(side="right", padx=6)
        tb.Button(bar, text="Speichern",  bootstyle=SUCCESS,   command=self.save).pack(side="right")

        self.columnconfigure(1, weight=1)

    def pick_music(self):
        path = filedialog.askdirectory(title="Ordner für MP3 wählen")
        if path: self.music_var.set(path)

    def pick_video(self):
        path = filedialog.askdirectory(title="Ordner für MP4 wählen")
        if path: self.video_var.set(path)

    def save(self):
        self.cfg["music_dir"] = self.music_var.get().strip() or self.cfg["music_dir"]
        self.cfg["video_dir"] = self.video_var.get().strip() or self.cfg["video_dir"]
        self.cfg["last_theme"] = self.theme_var.get()
        save_config(self.cfg)
        self.destroy()
        messagebox.showinfo("Einstellungen", "Gespeichert. Theme greift beim nächsten Start.")

# -------- Haupt-App --------
class App(tb.Window):
    def __init__(self, cfg):
        self.cfg = cfg
        start_kind = get_start_theme(cfg)  # 'light'/'dark'
        super().__init__(title="YouTube Downloader", themename=theme_to_bootstrap(start_kind))
        self.geometry("800x360"); self.minsize(740, 320)
        self.available_res = []
        self.last_file = None
        self.place_widgets(start_kind)

    def place_widgets(self, start_kind):
        p = {"padx": 10, "pady": 8}

        tb.Label(self, text="🎬  YouTube Downloader", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=8, sticky="w", **p
        )

        tb.Label(self, text="YouTube-URL").grid(row=1, column=0, sticky="w", **p)
        self.url_var = tb.StringVar()
        self.url_entry = tb.Entry(self, textvariable=self.url_var, width=70)
        self.url_entry.grid(row=1, column=1, columnspan=5, sticky="we", **p)
        tb.Button(self, text="Analysieren", bootstyle=INFO, command=self.on_probe).grid(row=1, column=6, sticky="e", **p)

        tb.Label(self, text="Format").grid(row=2, column=0, sticky="w", **p)
        self.fmt_var = tb.StringVar(value="MP3")
        self.fmt_combo = tb.Combobox(self, textvariable=self.fmt_var, values=["MP3","MP4"], state="readonly", width=10)
        self.fmt_combo.grid(row=2, column=1, sticky="w", **p); self.fmt_combo.bind("<<ComboboxSelected>>", self.refresh_quality)

        tb.Label(self, text="Qualität").grid(row=2, column=2, sticky="e", **p)
        self.q_var = tb.StringVar(value="320")
        self.q_combo = tb.Combobox(self, textvariable=self.q_var, state="readonly", width=12)
        self.q_combo.grid(row=2, column=3, sticky="w", **p)

        self.dark_var = tb.BooleanVar(value=(start_kind=="dark"))
        tb.Checkbutton(self, text="Dark Mode", variable=self.dark_var,
                       bootstyle="secondary-round-toggle", command=self.toggle_theme)\
            .grid(row=2, column=6, sticky="e", **p)

        self.progress = tb.Progressbar(self, mode="determinate", maximum=100, bootstyle="info-striped")
        self.progress.grid(row=3, column=0, columnspan=8, sticky="we", padx=10)

        self.status = tb.Label(self, text="")
        self.status.grid(row=4, column=0, columnspan=8, sticky="w", **p)

        # klickbarer Dateilink
        self.file_link = tb.Label(self, text="", cursor="hand2", bootstyle="info")
        self.file_link.grid(row=5, column=0, columnspan=8, sticky="w", padx=10)
        self.file_link.bind("<Button-1>", lambda e: self._open_last_file())

        self.dl_btn = tb.Button(self, text="⭳  Download starten", bootstyle=SUCCESS, command=self.on_download)
        self.dl_btn.grid(row=6, column=0, columnspan=2, sticky="w", **p)

        self.open_btn = tb.Button(self, text="📂 Ordner öffnen", bootstyle=SECONDARY, command=self.open_target, state=DISABLED)
        self.open_btn.grid(row=6, column=2, columnspan=2, sticky="w", **p)

        self.settings_btn = tb.Button(self, text="⚙️  Einstellungen", bootstyle=SECONDARY, command=self.open_settings)
        self.settings_btn.grid(row=6, column=6, columnspan=2, sticky="e", **p)

        for c in (1,2,3,4,5):
            self.columnconfigure(c, weight=1)

        self.refresh_quality()
        self.url_entry.focus()

    # ----- helpers -----
    def toggle_theme(self):
        self.style.theme_use("darkly" if self.dark_var.get() else "flatly")

    def open_target(self):
        path = self.cfg["music_dir"] if self.fmt_var.get()=="MP3" else self.cfg["video_dir"]
        try:
            if sys.platform.startswith("win"): os.startfile(path)
            elif sys.platform=="darwin": os.system(f'open "{path}"')
            else: os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Fehler", f"Kann Ordner nicht öffnen:\n{e}")

    def open_settings(self):
        SettingsDialog(self, self.cfg)
        self.status.config(text=f"MP3 → {self.cfg['music_dir']}  |  MP4 → {self.cfg['video_dir']}")

    def _set_file_link(self, path: str):
        self.last_file = path
        shown = os.path.basename(path)
        self.file_link.configure(text=f"📄 Datei öffnen: {shown}")

    def _open_last_file(self):
        if not self.last_file: return
        try:
            if sys.platform.startswith("win"): os.startfile(self.last_file)
            elif sys.platform=="darwin": os.system(f'open "{self.last_file}"')
            else: os.system(f'xdg-open "{self.last_file}"')
        except Exception as e:
            messagebox.showerror("Fehler", f"Kann Datei nicht öffnen:\n{e}")

    # ----- Qualitäten -----
    def refresh_quality(self, *_):
        if self.fmt_var.get()=="MP3":
            vals = ["128","192","256","320"]
            self.q_combo.config(values=vals)
            if self.q_var.get() not in vals: self.q_var.set("192")
        else:
            vals = self.available_res or ["480","720","1080","1440","2160"]
            self.q_combo.config(values=vals)
            if self.q_var.get() not in vals: self.q_var.set(vals[-1])

    def on_probe(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Fehler", "Bitte eine YouTube-URL eingeben."); return
        self.status.config(text="🔎 Analysiere Video-Qualitäten…")
        self.progress["value"] = 0
        self.available_res = []
        def worker():
            try:
                res = probe_available_resolutions(url)
                self.available_res = res
                self.status.config(text=f"✅ Gefundene Auflösungen: {', '.join(res) if res else 'keine'}")
                self.refresh_quality()
            except Exception as e:
                self.status.config(text=f"❌ Analyse fehlgeschlagen: {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ----- yt-dlp Hooks -----
    def progress_hook(self, d):
        if d.get("status") == "downloading":
            p = d.get("_percent_str", "").strip().replace("%","")
            try: self.progress["value"] = float(p)
            except: pass
            self.status.config(text=f"📥 Lädt… {d.get('_percent_str','')}")
        elif d.get("status") == "finished":
            self.status.config(text="🔁 Verarbeite… (ffmpeg)")
            self.progress["value"] = 100

    def post_hook(self, d):
        fp = d.get("filepath") or d.get("info_dict", {}).get("filepath")
        if fp and os.path.isfile(fp):
            self._set_file_link(fp)

    # ----- Download -----
    def on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Fehler", "Bitte eine YouTube-URL eingeben."); return
        fmt, qual = self.fmt_var.get(), self.q_var.get()
        self.progress["value"] = 0
        self.file_link.configure(text="")
        self.open_btn.configure(state=DISABLED)
        self.dl_btn.configure(state=DISABLED)
        self.status.config(text="Startet…")

        def worker():
            try:
                opts = build_opts(fmt, qual, self.progress_hook, self.post_hook, self.cfg)
                with YoutubeDL(opts) as ydl:
                    ydl.download([url])

                # Fallback, falls Post-Hook keinen Pfad lieferte
                if not self.last_file:
                    target = self.cfg["music_dir"] if fmt=="MP3" else self.cfg["video_dir"]
                    try:
                        files = [os.path.join(target, f) for f in os.listdir(target)]
                        files = [p for p in files if os.path.isfile(p)]
                        if files:
                            latest = max(files, key=os.path.getmtime)
                            self._set_file_link(latest)
                    except Exception:
                        pass

                target_dir = self.cfg["music_dir"] if fmt=="MP3" else self.cfg["video_dir"]
                self.status.config(text=f"✅ Fertig! Gespeichert in: {target_dir}")
                self.open_btn.configure(state=NORMAL)
            except Exception as e:
                self.status.config(text=f"❌ Fehler: {e}")
            finally:
                self.dl_btn.configure(state=NORMAL)

        threading.Thread(target=worker, daemon=True).start()

# -------- Entry Point --------
def main():
    cfg = load_config()
    cfg["last_theme"] = get_start_theme(cfg)
    app = App(cfg)
    app.mainloop()
    # gewähltes Theme fürs nächste Mal merken
    try:
        current_theme = app.style.theme.name
        cfg["last_theme"] = "dark" if "dark" in current_theme.lower() else "light"
        save_config(cfg)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback, tkinter as tk
        from tkinter import messagebox
        r = tk.Tk(); r.withdraw()
        messagebox.showerror("Fehler beim Start", traceback.format_exc())
        r.destroy()
        raise
