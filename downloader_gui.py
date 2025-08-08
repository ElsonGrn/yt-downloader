import os, sys, PySimpleGUI as sg
from yt_dlp import YoutubeDL

HOME = os.path.expanduser("~")
MUSIC_DIR = os.path.join(HOME, "Music")
VIDEO_DIR = os.path.join(HOME, "Videos")

def ffmpeg_dir():
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    d = os.path.join(base, "ffmpeg")
    return d if os.path.isdir(d) else None

def build_opts(fmt, quality):
    opts = {"quiet": True, "noprogress": True}
    ffd = ffmpeg_dir()
    if ffd: opts["ffmpeg_location"] = ffd

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
        vf = f"bestvideo[height<={quality}]+bestaudio/best"
        opts.update({
            "outtmpl": os.path.join(VIDEO_DIR, "%(title)s.%(ext)s"),
            "format": vf,
            "merge_output_format": "mp4"
        })
    return opts

# Theme nur setzen, wenn die Funktion existiert (sonst überspringen)
if hasattr(sg, "theme"):
    sg.theme("SystemDefault")
# bei manchen 5.x-Builds gibt's set_options, aber ohne 'theme' -> also nicht verwenden

layout = [
    [sg.Text("YouTube-URL"), sg.Input(key="-URL-", expand_x=True)],
    [sg.Text("Format"), sg.Combo(["MP3","MP4"], default_value="MP3", key="-FMT-", readonly=True, enable_events=True),
     sg.Text("Qualität"),
     sg.Combo(["128","192","256","320"], key="-QMP3-", default_value="192", readonly=True, visible=True),
     sg.Combo(["480","720","1080","1440","2160"], key="-QMP4-", default_value="1080", readonly=True, visible=False)],
    [sg.Button("Download starten", bind_return_key=True), sg.Text("", key="-STATUS-", expand_x=True)]
]
win = sg.Window("YouTube Downloader", layout, finalize=True)

def switch_dropdown(fmt):
    win["-QMP3-"].update(visible = (fmt=="MP3"))
    win["-QMP4-"].update(visible = (fmt=="MP4"))

switch_dropdown("MP3")

while True:
    ev, val = win.read()
    if ev in (sg.WIN_CLOSED, "Exit"): break
    if ev == "-FMT-":
        switch_dropdown(val["-FMT-"])
    if ev == "Download starten":
        url = (val["-URL-"] or "").strip()
        if not url:
            win["-STATUS-"].update("Bitte URL eingeben.", text_color="red"); continue
        fmt = val["-FMT-"]
        q   = val["-QMP3-"] if fmt=="MP3" else val["-QMP4-"]
        try:
            win["-STATUS-"].update("Lade...", text_color="black")
            with YoutubeDL(build_opts(fmt, q)) as ydl:
                ydl.download([url])
            target = MUSIC_DIR if fmt=="MP3" else VIDEO_DIR
            win["-STATUS-"].update(f"Fertig ✅  Gespeichert in: {target}", text_color="green")
        except Exception as e:
            win["-STATUS-"].update(f"Fehler: {e}", text_color="red")

win.close()
