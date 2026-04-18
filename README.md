# STT Dictation

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

Push-to-talk-dikteringsverktyg för Windows. Håll en global snabbtangent (standard: F9), tala, släpp — talet transkriberas med KB-Whisper och klistras in i det aktiva fönstret.

## Kom igång

### 1. Installera beroenden

```bash
pip install -r requirements.txt
```

### 2. (Valfritt) GPU-acceleration

Om du har ett NVIDIA-grafikkort, installera CUDA-biblioteken för snabbare transkribering:

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Utan dessa körs transkriberingen på CPU, vilket fungerar men är långsammare.

### 3. Starta

```bash
python main.py
```

Appen laddar Whisper-modellen (tar en stund första gången — den laddas ned från Hugging Face) och dyker sedan upp som en ikon i systemfältet.

CLI-testläge (utan tray/hotkey):

```bash
python main.py --cli
```

## Användning

1. **Håll F9** (eller din konfigurerade tangent) — inspelning startar
2. **Släpp** — transkribering körs, texten klistras in i det aktiva fönstret
3. **Högerklicka tray-ikonen** — öppna inställningar eller avsluta

## Inställningar

Högerklicka tray-ikonen → **Inställningar** för att konfigurera:

| Inställning | Beskrivning |
|-------------|-------------|
| Snabbtangent | Valfri tangent eller kombination (t.ex. `ctrl+shift+f9`) |
| Mikrofon | Välj ljudinmatningsenhet |
| Utmatning | Klistra in automatiskt eller bara kopiera till urklipp |
| Feedback-fönster | Visa/dölj transkriberings-overlay |
| Beam size | 1 (snabb) till 5 (bäst kvalitet) |

Inställningar sparas i `settings.json`.

## Bygga och distribuera

Bygg fristående exe med PyInstaller:

```bash
pyinstaller "STT Dictation.spec" --noconfirm
```

Resultatet hamnar i `dist\STT Dictation\`. Kopiera sedan till målmappen:

```bash
deploy.bat
```

Skriptet kopierar `dist\STT Dictation\` till `C:\Program_USB\STT Dictation\` och rensar bort gamla filer. `settings.json` i målmappen berörs aldrig, så användarens inställningar bevaras.

## Teknik

- **faster-whisper** med [KB-Whisper](https://huggingface.co/KBLab/kb-whisper-medium) (svenska)
- **sounddevice** för ljudinspelning
- **keyboard** för globala snabbtangenter
- **pyperclip** + **pyautogui** för urklipp/inklistring
- **pystray** + **tkinter** för systemfält och GUI

## Felsökning

| Problem | Lösning |
|---------|---------|
| `cublas64_12.dll not found` | Installera `nvidia-cublas-cu12` via pip, eller kör på CPU |
| Hotkey fungerar inte | Kör som administratör (`keyboard` kan kräva det) |
| Ingen ljud-input | Kontrollera mikrofon i inställningar |

## Licens

[MIT](LICENSE)
