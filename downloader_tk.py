# downloader_tk.py
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from yt_dlp import YoutubeDL

# Standard-Zielordner
HOME = os.path.expanduser("~")
MUSIC_DIR = os.path.join(HOME, "Music")
VIDEO_DIR = os.path.join(HOME, "Videos")

def get_ffmpeg_location():
    """
    Wenn per PyInstaller gebaut und ffmpeg mitgegeben wurde, liegt es im Unterordner 'ffmpeg'.
    Sonst None -> System-PATH benutzen.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        cand = os.path.join(base, "ffmpeg")
        if os.path.isdir(cand):
            return cand
    return None

def build_opts(fmt: str, quality: str):
    """
    yt-dlp Optionen für MP3 / MP4 mit Qualitätsauswahl.
    """
    opts = {"quiet": True, "noprogress": True}
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
                "preferredquality": quality  # "128"/"192"/"256"/"320"
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

def do_download(url: str, fmt: str, quality: str, status_lbl: ttk.Label, btn: ttk.Button):
    """
    Download in Thread starten, UI nicht blockieren.
    """
    url = (url or "").strip()
    if not url:
        messagebox.showerror("Fehler", "Bitte eine YouTube-URL eingeben.")
        return

    btn.state(["disabled"])
    status_lbl.config(text="📥 Lade...", foreground="black")
    try:
        opts = build_opts(fmt, quality)
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        target = MUSIC_DIR if fmt == "MP3" else VIDEO_DIR
        status_lbl.config(text=f"✅ Fertig! Gespeichert in: {target}", foreground="green")
    except Exception as e:
        status_lbl.config(text=f"❌ Fehler: {e}", foreground="red")
    finally:
        btn.state(["!disabled"])

def main():
    root = tk.Tk()
    root.title("YouTube Downloader")
    root.geometry("560x180")
    root.resizable(False, False)

    pad = {"padx": 8, "pady": 6}

    # URL
    ttk.Label(root, text="YouTube-URL").grid(row=0, column=0, sticky="w", **pad)
    url_var = tk.StringVar()
    url_entry = ttk.Entry(root, textvariable=url_var, width=60)
    url_entry.grid(row=0, column=1, columnspan=3, sticky="we", **pad)

    # Format
    ttk.Label(root, text="Format").grid(row=1, column=0, sticky="w", **pad)
    fmt_var = tk.StringVar(value="MP3")
    fmt_combo = ttk.Combobox(root, textvariable=fmt_var, values=["MP3", "MP4"], state="readonly", width=8)
    fmt_combo.grid(row=1, column=1, sticky="w", **pad)

    # Qualität (Dropdown wird je nach Format gefüllt)
    ttk.Label(root, text="Qualität").grid(row=1, column=2, sticky="e", **pad)
    q_var = tk.StringVar(value="192")
    q_combo = ttk.Combobox(root, textvariable=q_var, state="readonly", width=8)
    q_combo.grid(row=1, column=3, sticky="w", **pad)

    def refresh_quality(*_):
        if fmt_var.get() == "MP3":
            q_combo["values"] = ["128", "192", "256", "320"]
            if q_var.get() not in q_combo["values"]:
                q_var.set("192")
        else:
            q_combo["values"] = ["480", "720", "1080", "1440", "2160"]
            if q_var.get() not in q_combo["values"]:
                q_var.set("1080")

    fmt_combo.bind("<<ComboboxSelected>>", refresh_quality)
    refresh_quality()

    # Status + Button
    status_lbl = ttk.Label(root, text="")
    status_lbl.grid(row=3, column=0, columnspan=4, sticky="w", padx=8, pady=(4, 0))

    def on_click():
        threading.Thread(
            target=do_download,
            args=(url_var.get(), fmt_var.get(), q_var.get(), status_lbl, dl_btn),
            daemon=True
        ).start()

    dl_btn = ttk.Button(root, text="Download starten", command=on_click)
    dl_btn.grid(row=2, column=0, columnspan=4, pady=8)

    url_entry.focus()
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Zeig Fehler als Popup, falls beim Start was crasht
        import traceback
        try:
            _r = tk.Tk(); _r.withdraw()
            messagebox.showerror("Fehler beim Start", traceback.format_exc())
            _r.destroy()
        except Exception:
            print("Startfehler:", traceback.format_exc(), file=sys.stderr)
        raise
