# downloader_tk.py – moderne GUI mit ttkbootstrap
import os, sys, threading
from yt_dlp import YoutubeDL
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox

HOME = os.path.expanduser("~")
MUSIC_DIR = os.path.join(HOME, "Music")
VIDEO_DIR = os.path.join(HOME, "Videos")

def get_ffmpeg_location():
    base = getattr(sys, "_MEIPASS", None)
    if base:
        cand = os.path.join(base, "ffmpeg")
        if os.path.isdir(cand):
            return cand
    return None

def build_opts(fmt: str, quality: str, progress_hook):
    opts = {
        "quiet": True,
        "noprogress": False,
        "progress_hooks": [progress_hook],
    }
    ffdir = get_ffmpeg_location()
    if ffdir:
        opts["ffmpeg_location"] = ffdir

    if fmt == "MP3":
        opts.update({
            "outtmpl": os.path.join(MUSIC_DIR, "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality
            }]
        })
    else:
        vfmt = f"bestvideo[height<={quality}]+bestaudio/best"
        opts.update({
            "outtmpl": os.path.join(VIDEO_DIR, "%(title)s.%(ext)s"),
            "format": vfmt,
            "merge_output_format": "mp4"
        })
    return opts

class App(tb.Window):
    def __init__(self):
        # Theme: „flatly“ ist hell, „darkly“ ist dunkel – du kannst jeden ttkbootstrap-Style nehmen
        super().__init__(title="YouTube Downloader", themename="flatly")  # probier auch: "darkly", "cyborg", "morph"
        self.geometry("720x300")
        self.minsize(680, 280)
        self.place_widgets()

    def place_widgets(self):
        pad = {"padx": 10, "pady": 8}

        # Header
        self.label = tb.Label(self, text="🎬  YouTube Downloader", font=("Segoe UI", 18, "bold"))
        self.label.grid(row=0, column=0, columnspan=6, sticky="w", **pad)

        # URL
        tb.Label(self, text="YouTube-URL").grid(row=1, column=0, sticky="w", **pad)
        self.url_var = tb.StringVar()
        self.url_entry = tb.Entry(self, textvariable=self.url_var, width=70)
        self.url_entry.grid(row=1, column=1, columnspan=5, sticky="we", **pad)

        # Format
        tb.Label(self, text="Format").grid(row=2, column=0, sticky="w", **pad)
        self.fmt_var = tb.StringVar(value="MP3")
        self.fmt_combo = tb.Combobox(self, textvariable=self.fmt_var, values=["MP3", "MP4"], state="readonly", width=10)
        self.fmt_combo.grid(row=2, column=1, sticky="w", **pad)
        self.fmt_combo.bind("<<ComboboxSelected>>", self.refresh_quality)

        # Qualität
        tb.Label(self, text="Qualität").grid(row=2, column=2, sticky="e", **pad)
        self.q_var = tb.StringVar(value="320")
        self.q_combo = tb.Combobox(self, textvariable=self.q_var, state="readonly", width=10)
        self.q_combo.grid(row=2, column=3, sticky="w", **pad)

        # Theme-Toggle
        self.dark_var = tb.BooleanVar(value=False)
        self.dark_chk = tb.Checkbutton(self, text="Dark Mode", variable=self.dark_var, bootstyle="secondary-round-toggle", command=self.toggle_theme)
        self.dark_chk.grid(row=2, column=5, sticky="e", **pad)

        # Progress + Status
        self.progress = tb.Progressbar(self, mode="determinate", maximum=100, bootstyle="info-striped")
        self.progress.grid(row=3, column=0, columnspan=6, sticky="we", padx=10)

        self.status = tb.Label(self, text="", bootstyle="success")
        self.status.grid(row=4, column=0, columnspan=6, sticky="w", **pad)

        # Buttons
        self.dl_btn = tb.Button(self, text="⭳  Download starten", bootstyle=SUCCESS, command=self.on_download)
        self.dl_btn.grid(row=5, column=0, columnspan=3, sticky="w", **pad)

        self.open_btn = tb.Button(self, text="📂 Ordner öffnen", bootstyle=SECONDARY, command=self.open_target, state="disabled")
        self.open_btn.grid(row=5, column=3, columnspan=3, sticky="e", **pad)

        # Grid behaviour
        for c in (1, 2, 3, 4):
            self.columnconfigure(c, weight=1)

        self.refresh_quality()
        self.url_entry.focus()

    def refresh_quality(self, *_):
        if self.fmt_var.get() == "MP3":
            vals = ["128", "192", "256", "320"]
            self.q_combo.config(values=vals)
            if self.q_var.get() not in vals:
                self.q_var.set("192")
        else:
            vals = ["480", "720", "1080", "1440", "2160"]
            self.q_combo.config(values=vals)
            if self.q_var.get() not in vals:
                self.q_var.set("1080")

    def toggle_theme(self):
        self.style.theme_use("darkly" if self.dark_var.get() else "flatly")

    def progress_hook(self, d):
        if d.get("status") == "downloading":
            p = d.get("_percent_str", "").strip().replace("%", "")
            try:
                self.progress["value"] = float(p)
            except Exception:
                pass
            self.status.config(text=f"📥 Lädt… {d.get('_percent_str','')}", bootstyle="info")
        elif d.get("status") == "finished":
            self.status.config(text="🔁 Verarbeite… (ffmpeg)", bootstyle="warning")
            self.progress["value"] = 100

    def on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Fehler", "Bitte eine YouTube-URL eingeben.")
            return
        self.progress["value"] = 0
        self.open_btn.config(state="disabled")
        self.status.config(text="Startet…", bootstyle="secondary")
        self.dl_btn.configure(state=DISABLED)

        def worker():
            fmt, qual = self.fmt_var.get(), self.q_var.get()
            try:
                opts = build_opts(fmt, qual, self.progress_hook)
                with YoutubeDL(opts) as ydl:
                    ydl.download([url])
                target = MUSIC_DIR if fmt == "MP3" else VIDEO_DIR
                self.status.config(text=f"✅ Fertig! Gespeichert in: {target}", bootstyle="success")
                self.open_btn.config(state=NORMAL)
                self.last_target = target
            except Exception as e:
                self.status.config(text=f"❌ Fehler: {e}", bootstyle="danger")
            finally:
                self.dl_btn.configure(state=NORMAL)

        threading.Thread(target=worker, daemon=True).start()

    def open_target(self):
        path = getattr(self, "last_target", None)
        if not path:
            path = MUSIC_DIR if self.fmt_var.get() == "MP3" else VIDEO_DIR
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Fehler", f"Kann Ordner nicht öffnen:\n{e}")

def main():
    app = App()
    app.mainloop()

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
