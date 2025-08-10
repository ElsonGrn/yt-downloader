# 🎬 YouTube Downloader – Modern GUI Edition

Ein einfaches, modernes Desktop-Tool zum Herunterladen von YouTube-Videos oder -Audios im **MP3**- oder **MP4**-Format.  
Die Downloads werden automatisch im Standard-**Musik-** oder **Videos**-Ordner gespeichert.

---

## ✨ Features
- **Moderne Benutzeroberfläche** mit [ttkbootstrap](https://ttkbootstrap.readthedocs.io/en/latest/)
- **MP3-Download** in 128, 192, 256 oder 320 kbps
- **MP4-Download** in 480p, 720p, 1080p, 1440p oder 2160p
- **Fortschrittsbalken** und Statusanzeige
- **Ordner öffnen**-Button nach Fertigstellung
- Optional **Dark Mode** aktivierbar
- Komplett **portable**

---

## 📥 Installation & Start

### 1. Fertige EXE starten
Falls du die fertige `ytdl_1.3.exe` hast:
- **Doppelklick** starten
- Keine Installation nötig (wenn FFmpeg gebündelt wurde)

> **Hinweis:** Beim ersten Start kann Windows Defender nachfragen, ob du die App starten möchtest – erlaube die Ausführung.

---

### 2. Selbst bauen (für Entwickler)
Falls du Python installiert hast, kannst du die EXE selbst erstellen.

#### Voraussetzungen
- Python 3.9+ (empfohlen 3.13)
- Abhängigkeiten installieren:
```powershell
py -m pip install -U yt-dlp ttkbootstrap
