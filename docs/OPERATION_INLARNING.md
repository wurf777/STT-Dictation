# Operation inlarningskurva

Status for STT Dictation efter arbetet med smartare diktering.

## Klart

- Appen aterstaller Windows urklipp efter automatisk inklistring.
- Urklipp aterstalls med fordrojning (`clipboard_restore_delay_ms`, standard 500 ms) for att undvika att malappen hinner klistra in gammalt urklipp.
- Senaste diktat sparas i appens eget minne och kan klistras in igen med F10.
- Lokal diktathistorik sparas i `data/dictation_history.jsonl`.
- Historiken ignoreras av git via `data/` i `.gitignore`.
- Varje historikpost kan innehalla:
  - `raw_text`
  - `processed_text`
  - `output_text`
  - `corrected_text`
  - `segments`
  - `words`
  - `pauses`
- Korrigeringsfonster finns via Ctrl+Alt+F10 och tray-menyn.
- Korrigeringsfonstret har knappar for:
  - spara facit
  - spara och klistra in korrigerad text
- Korrigeringsfonstret forsoker lyfta sig till fokus nar det oppnas.
- Regelbaserad svensk efterprocessor finns i `post_processor.py`.
- Efterprocessorn tolkar just nu:
  - `komma` -> `,`
  - `punkt` -> `.`
  - `fragetecken` / `frågetecken` -> `?`
  - `utropstecken` -> `!`
  - `ny rad` -> radbrytning
  - `nytt stycke` -> blankrad
  - `kolon` -> `:`
  - `semikolon` -> `;`
- Efterprocessorn svaljer extra Whisper-skiljetecken efter kommandoord, till exempel `utropstecken,` -> `!`.

## Viktiga filer

- `post_processor.py` - svensk regelbaserad efterbehandling.
- `test_post_processor.py` - enkla regressionstester for efterprocessorn.
- `dictation_history.py` - lokal historik och korrigeringar.
- `correction_window.py` - GUI for att korrigera senaste diktat.
- `output_handler.py` - urklipp, inklistring och senaste diktat.
- `transcriber.py` - Whisper-transkribering, ordtider och pauser.

## Testkommandon

Eftersom `pytest` inte finns i `.venv` just nu kor vi testerna direkt:

```powershell
.\.venv\Scripts\python.exe -c "import test_post_processor as t; t.test_punctuation_commands(); t.test_line_break_commands(); t.test_spacing_cleanup(); t.test_command_words_swallow_whisper_punctuation(); t.test_literal_command_words_in_examples(); print('post processor tests ok')"
```

Syntaxkontroll:

```powershell
.\.venv\Scripts\python.exe -m compileall main.py transcriber.py post_processor.py dictation_history.py correction_window.py output_handler.py hotkey_manager.py tray.py config.py
```

## Installerad kopia

Tidigare deploy-script pekar pa:

```text
C:\Program_USB\STT Dictation
```

Bygg och deploy:

```powershell
.\.venv\Scripts\pyinstaller.exe "STT Dictation.spec" --clean --noconfirm
.\deploy.bat
```

`deploy.bat` kopierar `dist\STT Dictation` till `C:\Program_USB\STT Dictation` och undantar `settings.json`.

## Nasta steg

1. Fortsatt testa efterprocessorn i vanlig diktering.
2. Nar den gor fel: lagg exempel i `test_post_processor.py` och justera reglerna.
3. Forbattra ordlistan till flera varianter per ratt ord, till exempel:
   - `Terört elle?` fran `terort eller`, `t-rört`, `terört eller`
   - `ChatGPT` fran `chat gpt`, `chatt gpt`, `chat-gpt`
4. Bygg ett analysverktyg for `data/dictation_history.jsonl`.
5. Analysera faktiska pauser och foresla regler for:
   - komma
   - punkt
   - tre punkter
   - nytt stycke
6. Senare: lagg till lokal Gemma/Ollama-polering som ett valfritt steg efter regelbaserad efterprocessor.

## Kanda begransningar

- Efterprocessorn ar regelbaserad och kommer behova fler undantag.
- Den kan fortfarande misstolka kommandoord som anvands som vanliga ord.
- Pausdata loggas men anvands inte for output annu.
- Korrigeringsfacit sparas, men det finns annu inget analysverktyg som foreslar nya regler automatiskt.
- Om automatisk inklistring ger forra diktatet men F10 ger ratt diktat, ar det troligen clipboard-race. Hoja `clipboard_restore_delay_ms`.
