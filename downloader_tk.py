import os, sys, threading, tkinter as tk
from tkinter import ttk, messagebox
from yt_dlp import YoutubeDL

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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("640x240")
        self.minsize(640, 240)
        self.configure(padx=14, pady=12)

        # Theme & Styles
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Body.TLabel", font=("Segoe UI", 10))
        self.style.configure("Body.TButton", font=("Segoe UI", 10))
        self.style.configure("Status.TLabel", font=("Segoe UI", 10))
        self.create_widgets()

    def create_widgets(self):
        pad = {"padx": 6, "pady": 6}

        ttk.Label(self, text="🎬  YouTube Downloader", style="Header.TLabel").grid(
            row=0, column=0, columnspan=5, sticky="w", **pad
        )

        ttk.Label(self, text="YouTube-URL", style="Body.TLabel").grid(row=1, column=0, sticky="w", **pad)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self, textvariable=self.url_var)
        self.url_entry.grid(row=1, column=1, columnspan=4, sticky="we", **pad)

        ttk.Label(self, text="Format", style="Body.TLabel").grid(row=2, column=0, sticky="w", **pad)
        self.fmt_var = tk.StringVar(value="MP3")
        self.fmt_combo = ttk.Combobox(self, textvariable=self.fmt_var, values=["MP3", "MP4"],
                                      state="readonly", width=8)
        self.fmt_combo.grid(row=2, column=1, sticky="w", **pad)
        self.fmt_combo.bind("<<ComboboxSelected>>", self.refresh_quality)

        ttk.Label(self, text="Qualität", style="Body.TLabel").grid(row=2, column=2, sticky="e", **pad)
        self.q_var = tk.StringVar(value="320")
        self.q_combo = ttk.Combobox(self, textvariable=self.q_var, state="readonly", width=8)
        self.q_combo.grid(row=2, column=3, sticky="w", **pad)

        self.theme_var = tk.BooleanVar(value=False)
        theme_chk = ttk.Checkbutton(self, text="Dark Mode", variable=self.theme_var, command=self.toggle_theme)
        theme_chk.grid(row=2, column=4, sticky="e", **pad)

        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.grid(row=3, column=0, columnspan=5, sticky="we", padx=6)

        self.status = ttk.Label(self, text="", style="Status.TLabel")
        self.status.grid(row=4, column=0, columnspan=5, sticky="w", **pad)

        self.dl_btn = ttk.Button(self, text="⭳  Download starten", style="Body.TButton", command=self.on_download)
        self.dl_btn.grid(row=5, column=0, columnspan=3, sticky="w", **pad)

        self.open_btn = ttk.Button(self, text="📂 Ordner öffnen", style="Body.TButton",
                                   command=self.open_target, state="disabled")
        self.open_btn.grid(row=5, column=3, columnspan=2, sticky="e", **pad)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=0)
        self.refresh_quality()
        self.url_entry.focus()

    def refresh_quality(self, *_):
        if self.fmt_var.get() == "MP3":
            self.q_combo["values"] = ["128", "192", "256", "320"]
            if self.q_var.get() not in self.q_combo["values"]:
                self.q_var.set("192")
        else:
            self.q_combo["values"] = ["480", "720", "1080", "1440", "2160"]
            if self.q_var.get() not in self.q_combo["values"]:
                self.q_var.set("1080")

    def toggle_theme(self):
        # einfacher Dark/Light Wechsel
        self.style.theme_use("clam" if not self.theme_var.get() else "alt")
        # kleines Dark-Feeling: Hintergrund abdunkeln
        bg = "#1f1f1f" if self.theme_var.get() else self.cget("bg")
        try:
            self.configure(bg=bg)
        except tk.TclError:
            pass

    def progress_hook(self, d):
        # Fortschritt von yt-dlp (download bzw. postprocessing)
        if d.get("status") == "downloading":
            p = d.get("_percent_str", "").strip().replace("%", "")
            try:
                self.progress["value"] = float(p)
            except Exception:
                pass
            self.status.config(text=f"📥 Lädt… {d.get('_percent_str','')}")
        elif d.get("status") == "finished":
            self.status.config(text="🔁 Verarbeite… (ffmpeg)")
            self.progress["value"] = 100

    def on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Fehler", "Bitte eine YouTube-URL eingeben.")
            return

        self.progress["value"] = 0
        self.open_btn.config(state="disabled")
        self.status.config(text="Startet…")
        self.dl_btn.state(["disabled"])

        def worker():
            fmt = self.fmt_var.get()
            qual = self.q_var.get()
            try:
                opts = build_opts(fmt, qual, self.progress_hook)
                with YoutubeDL(opts) as ydl:
                    ydl.download([url])
                target = MUSIC_DIR if fmt == "MP3" else VIDEO_DIR
                self.status.config(text=f"✅ Fertig! Gespeichert in: {target}")
                self.open_btn.config(state="normal")
                self.last_target = target
            except Exception as e:
                self.status.config(text=f"❌ Fehler: {e}")
            finally:
                self.dl_btn.state(["!disabled"])

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
    except Exception as e:
        import traceback
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Fehler beim Start", traceback.format_exc())
        root.destroy()
        raise
