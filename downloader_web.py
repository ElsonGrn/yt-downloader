import os
import streamlit as st
from yt_dlp import YoutubeDL
import sys
_bundle = getattr(sys, "_MEIPASS", None)
if _bundle:
    FF_DIR = os.path.join(_bundle, "ffmpeg")
else:
    FF_DIR = None
# wenn gebundelt, yt-dlp sagen wo ffmpeg liegt:
# in build_opts(...) jeweils: if FF_DIR: ydl_opts["ffmpeg_location"] = FF_DIR


# Standardordner (plattformabhängig)
MUSIC_DIR = os.path.join(os.path.expanduser("~"), "Music")
VIDEO_DIR = os.path.join(os.path.expanduser("~"), "Videos")

st.set_page_config(page_title="YouTube Downloader", page_icon="🎵", layout="centered")
st.title("🎥 YouTube Downloader")
st.write("URL einfügen, Format & Qualität auswählen. MP3 → Musik, MP4 → Videos.")

url = st.text_input("YouTube-URL", placeholder="https://www.youtube.com/watch?v=...")
fmt = st.radio("Format", ["mp3", "mp4"], horizontal=True)

# Dropdown abhängig vom Format
if fmt == "mp3":
    qual = st.selectbox("Qualität (kbps)", ["128", "192", "256", "320"], index=1)
else:
    qual = st.selectbox("Maximale Auflösung (px)", ["480", "720", "1080", "1440", "2160"], index=2)

status = st.empty()

def build_opts(fmt: str, qual: str):
    if fmt == "mp3":
        output = os.path.join(MUSIC_DIR, "%(title)s.%(ext)s")
        ydl_opts = {
            "outtmpl": output,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": qual
            }],
            "quiet": True,
            "noprogress": True,
        }
    else:  # mp4
        output = os.path.join(VIDEO_DIR, "%(title)s.%(ext)s")
        vfmt = f"bestvideo[height<={qual}]+bestaudio/best"
        ydl_opts = {
            "outtmpl": output,
            "format": vfmt,
            "merge_output_format": "mp4",
            "quiet": True,
            "noprogress": True,
        }
    return ydl_opts, output

if st.button("Download starten"):
    if not url.strip():
        st.error("Bitte eine gültige URL eingeben.")
    else:
        opts, outtmpl = build_opts(fmt, qual)
        try:
            status.info("📥 Download läuft...")
            with YoutubeDL(opts) as ydl:
                ydl.download([url.strip()])
            st.success(f"✅ Fertig! Gespeichert in:\n{outtmpl}")
            if fmt == "mp3":
                st.write(f"📂 Ordner: {MUSIC_DIR}")
            else:
                st.write(f"📂 Ordner: {VIDEO_DIR}")
        except Exception as e:
            st.error(f"❌ Fehler: {e}")
