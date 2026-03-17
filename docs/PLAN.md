# STT Dictation – Windows Dikteringsverktyg
## Plan för implementation

### Syfte
Ett lättviktigt push-to-talk-dikteringsverktyg för Windows. Användaren håller ner en global hotkey, talar, och när tangenten släpps transkriberas talet med KB-Whisper och texten klistras in i aktivt fönster (eller kopieras till clipboard). Primärt användningsfall: diktera promptar till Claude Code och andra språkmodeller under kodning.

---

### Teknisk stack
- **Språk:** Python (samma miljö som TTS-appen)
- **STT-motor:** `faster-whisper` med KB-Whisper-modell (`KBLab/kb-whisper-large` eller medium beroende på VRAM)
- **Hotkey/tangentbord:** `keyboard` (global hotkey, fungerar i bakgrunden)
- **Ljud:** `sounddevice` + `numpy` (spelar in microfoninput)
- **Clipboard/output:** `pyperclip` + `pyautogui` (klistra in i aktivt fönster)
- **Trayikon:** `pystray` + `Pillow` (körs i systemtray, diskret)

---

### Projektstruktur
```
stt-dictation/
├── main.py              # Startpunkt, initierar allt
├── recorder.py          # Ljud­inspelning via sounddevice
├── transcriber.py       # Whisper-transkribering (med streaming)
├── output_handler.py    # Clipboard + autotype
├── hotkey_manager.py    # Global hotkey-hantering
├── feedback_window.py   # Live transkriberings-fönster (tkinter)
├── tray.py              # Systemtray-ikon och meny
├── config.py            # Inställningar (hotkey, modell, språk etc.)
├── requirements.txt
└── README.md
```

---

### Flöde (steg för steg)

1. **App startar** → laddar Whisper-modell i bakgrunden (en gång) → visas i systemtray
2. **Användaren håller ner hotkey** (default: `F9`) → inspelning startar
3. **Hotkey släpps** → inspelning stoppas, ljud skickas till Whisper
4. **Whisper transkriberar** → returnerar text (sv-SE)
5. **Text outputas** via en av två lägen:
   - **Auto-paste** (default): kopierar till clipboard + `Ctrl+V` i aktivt fönster
   - **Clipboard only**: kopierar bara, användaren klistrar manuellt
6. **Visuell feedback** (valfritt): kort notifikation eller tray-ikon blinkar under inspelning

---

### Konfiguration (`config.py`)
```python
HOTKEY = "F9"                          # Global push-to-talk-tangent
WHISPER_MODEL = "KBLab/kb-whisper-medium"  # Eller "large" om VRAM räcker
LANGUAGE = "sv"                        # Svenska
OUTPUT_MODE = "auto_paste"             # "auto_paste" | "clipboard_only"
SAMPLE_RATE = 16000                    # Hz (Whisper föredrar 16kHz)
SILENCE_THRESHOLD = 0.01               # Klipp tystnad i början/slutet
```

---

### Modellval (KB-Whisper)
| Modell | VRAM | Hastighet | Kvalitet |
|--------|------|-----------|----------|
| `kb-whisper-small` | ~1 GB | Snabb | Bra |
| `kb-whisper-medium` | ~2 GB | Medel | Mycket bra |
| `kb-whisper-large` | ~4 GB | Långsammare | Utmärkt |

Rekommendation: börja med **medium**. G14:ans GPU bör hantera det utan problem.

Modellen laddas från Hugging Face automatiskt via `faster-whisper` vid första körning.

---

### Beroenden (`requirements.txt`)
```
faster-whisper
sounddevice
numpy
keyboard
pyperclip
pyautogui
pystray
Pillow
```

---

### Live feedback-fönster (`feedback_window.py`)
Ett litet always-on-top-fönster som visar vad Whisper tolkar i nära realtid.

**Beteende:**
- Poppar upp när inspelning startar (hotkey trycks ner)
- `faster-whisper` stöder streaming av segment – texten dyker upp progressivt medan modellen transkriberar
- Visar pågående text i grått → bekräftad text i vitt (eller liknande visuell distinktion)
- Stängs automatiskt efter 2–3 sekunder när transkriberingen är klar och text outputats
- Litet, diskret fönster i ett hörn (konfigurerbart position) – stör inte arbetsflödet

**Implementation:**
- `tkinter` (inbyggt i Python, inga extra beroenden) med `overrideredirect(True)` för ett fönster utan titlebar
- `always_on_top` via `wm_attributes("-topmost", True)`
- Uppdateras via `after()` i tkinter-loopen från en kö (`queue.Queue`) som transcriber skriver till
- `faster-whisper` används med `word_timestamps=True` för att kunna visa ord i takt med att de bekräftas

**Tillägg i projektstruktur:**
```
stt-dictation/
├── feedback_window.py   # Live transkriberings-fönster (tkinter)
└── ...
```

**Tillägg i konfiguration:**
```python
SHOW_FEEDBACK_WINDOW = True       # Visa live-fönster
FEEDBACK_WINDOW_POSITION = "bottom-right"  # "top-left" | "top-right" | "bottom-left" | "bottom-right"
FEEDBACK_AUTO_CLOSE_DELAY = 2500  # ms innan fönstret stängs efter klar transkribering
```

---

### Implementationsordning (prioritet)
1. ✅ `recorder.py` – grundläggande inspelning med start/stopp
2. ✅ `transcriber.py` – ladda KB-Whisper och transkribera en audiobuffer, med streaming-stöd
3. ✅ Koppla ihop recorder + transcriber i `main.py`, testa via kommandorad
4. ✅ `hotkey_manager.py` – global hotkey push-to-talk (stöd för tangentkombinationer)
5. ✅ `output_handler.py` – clipboard + auto-paste
6. ✅ `feedback_window.py` – live transkriberings-fönster (multi-monitor-stöd)
7. ✅ `tray.py` – trayikon med möjlighet att avsluta appen
8. ✅ Felhantering (mikrofon ej tillgänglig, CUDA-fallback, modell ej laddad etc.)
9. ✅ `settings_window.py` – konfigurationsfönster (hotkey, mikrofon, utmatningsläge, feedback)
10. ✅ `config.py` – JSON-persistens av inställningar (`settings.json`)
11. ✅ CUDA-stöd – automatisk DLL-laddning från pip-paket
12. ✅ Optimering – tystnadstrimning av ljud före transkribering
13. ✅ Beam size konfigurerbar i settings-fönstret
14. ✅ Enkel README med installationsinstruktioner

---

### Önskvärd UX
- Appen ska vara **helt diskret** – inga fönster, bara tray
- Inspelning ska **kännas omedelbar** (ingen uppstartslatens efter hotkey)
- Transkriberingen ska ta **under 2 sekunder** för normala meningar
- Vid fel: tyst fallback (ingen krasch), gärna tray-notifikation

---

### Framtida utbyggnad (ej del av MVP)
- ✅ ~~Konfigurerbart via tray-meny (byta hotkey, modell, outputläge)~~ — implementerat via settings_window.py
- Beam size konfigurerbar i settings-fönstret (just nu bara via settings.json)
- Ordkorrektion / efterbehandling via LLM (skiljetecken, formatering)
- ~~Stöd för flera mikrofoner~~ — implementerat (valbar i inställningar)
- Kommando-läge ("öppna terminal", "ny fil" etc.)
- Integration med TTS-appen som ett kombinerat röstgränssnitt
