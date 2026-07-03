# Operation inlärningskurva

Kort projektminne för hur STT Dictation ska bli bättre på Christians diktering.

## Nuläge

Programmet kan redan:

- diktera med F9
- klistra in senaste diktat igen med F10
- öppna korrigeringsfönster med Ctrl+Alt+F10
- återställa Windows urklipp efter automatisk inklistring
- spara lokal diktathistorik i `data/dictation_history.jsonl`
- spara korrigeringar/facit från korrigeringsfönstret
- föreslå enkla ersättningsregler från råtext till korrigerad text
- spara osäkra förslag i `data/learning_basket.jsonl`
- visa och ändra nya inställningar i inställningsfönstret
- visa snabbknappar i tray-menyn
- göra enkel smart fortsättning mellan två diktat

## Viktiga snabbknappar

- F9: håll inne för att diktera
- F10: klistra in senaste diktat igen
- Ctrl+Alt+F10: korrigera senaste diktat

## Viktiga filer

- `main.py`: startar appen och kopplar ihop allt
- `transcriber.py`: Whisper-transkribering
- `post_processor.py`: svensk regelbaserad efterbehandling
- `output_handler.py`: urklipp, inklistring, F10 och smart fortsättning
- `dictation_history.py`: lokal historik och korrigeringar
- `correction_window.py`: korrigeringsfönster
- `learning_suggestions.py`: regelkandidater och lärandekorg
- `settings_window.py`: inställningsfönster
- `tray.py`: meny vid ikonen nere till höger
- `config.py`: standardinställningar och `settings.json`

## Data som samlas lokalt

Historiken ligger normalt bredvid den installerade appen:

```text
C:\Program_USB\STT Dictation\data\dictation_history.jsonl
C:\Program_USB\STT Dictation\data\learning_basket.jsonl
```

Historiken kan innehålla:

- rå Whisper-text
- efterprocessad text
- faktiskt inklistrad text
- korrigerat facit
- ordtider
- pausdata

Lärandekorgen innehåller förslag som inte automatiskt aktiverats ännu.

## Klart i efterprocessorn

Efterprocessorn tolkar bland annat:

- `komma` -> `,`
- `punkt` -> `.`
- `frågetecken` -> `?`
- `utropstecken` -> `!`
- `ny rad` -> radbrytning
- `nytt stycke` -> blankrad
- `kolon` -> `:`
- `semikolon` -> `;`

Den försöker också ta bort extra Whisper-skiljetecken efter kommandoord, till
exempel `utropstecken,` -> `!`.

## Smart fortsättning

Första versionen finns i `output_handler.py`.

Idén:

- appen minns senaste automatiska inklistring
- om nästa diktat kommer inom ett valt tidsfönster kan appen lägga till blanksteg
- om förra texten slutade med enkel punkt och nästa diktat ser ut som en
  fortsättning kan appen skicka Backspace före inklistringen

Inställningar:

- `smart_leading_space_enabled`
- `smart_remove_previous_period_enabled`
- `smart_leading_space_window_seconds`

Begränsning: appen vet inte säkert var markören står i målprogrammet. Därför
måste funktionen vara försiktig.

## Vad vi har kvar

Högst värdefullt härnäst:

1. Bygg ett enkelt analysverktyg för `dictation_history.jsonl`.
2. Visa statistik över vanliga fel, korrigeringar, pauser och konstiga
   skiljetecken.
3. Bygg ett bättre UI för att gå igenom `learning_basket.jsonl`.
4. Förbättra ordlista/replacements med flera varianter per rätt ord.
5. Lägg fler verkliga fel som tester i `test_post_processor.py`.

Efter det:

6. Använd pausdata för att föreslå komma, punkt, tre punkter och nytt stycke.
7. Lägg till valfri lokal språkmodell via Ollama/Gemma som analyslager.
8. Låt språkmodellen föreslå förbättringar, men inte ändra allt automatiskt
   utan godkännande.

## Vad språkmodellen bör göra

Språkmodellen är mest intressant för sådant som kräver förståelse:

- upptäcka självkorrigeringar i tal
- ta bort upprepningar som beror på att användaren tänker högt
- skilja kommandoord från vanliga ord i sammanhang
- föreslå mer generella regler från flera exempel
- förbättra flyt och interpunktion utan att ändra meningen

Regler är bättre för exakta, återkommande saker:

- `chat gpt` -> `ChatGPT`
- `t-rört` -> `Terört`
- `utropstecken,` -> `!`
- mellanslag runt skiljetecken

## Framtida: förbättringsförslag efter diktat

Målet är inte att appen ska visa vaga varningar. Christian ser ofta själv när
texten blivit fel. Värdet ska i stället vara att appen redan har ett färdigt
förslag.

Flöde:

1. Texten klistras in direkt som vanligt.
2. Appen skickar råtext och faktisk output till ett analyslager.
3. Om analyslagret har ett tydligt bättre förslag visas en liten diskret ruta.
4. Christian kan välja `Använd`, `Ignorera` eller `Lär av detta`.
5. `Använd` ersätter senaste inklistrade text med förslaget.
6. `Lär av detta` sparar original och förslag i historik eller lärandekorg.

Exempel:

```text
Original: två filer till Jason-filerna
Förslag: två JSON-filer
```

Bra kandidater:

- självkorrigeringar i tal
- upprepningar
- taligt språk som borde bli skriven text
- uppenbara sammanhangsfel, till exempel `Jason` när sammanhanget handlar om
  `JSON`
- konstig interpunktion som inte kan lösas med enkla regler

Funktionen bör vara valfri och försiktig. Den ska inte stoppa diktatflödet, och
den ska inte skriva om all text automatiskt utan godkännande.

## Testkommandon

Efterprocessor:

```powershell
.\.venv\Scripts\python.exe -c "import test_post_processor as t; t.test_punctuation_commands(); t.test_line_break_commands(); t.test_spacing_cleanup(); t.test_command_words_swallow_whisper_punctuation(); t.test_literal_command_words_in_examples(); print('post processor tests ok')"
```

Lärandeförslag:

```powershell
.\.venv\Scripts\python.exe -c "import test_learning_suggestions as t; t.test_suggests_short_replacement_from_correction(); t.test_skips_identical_text(); t.test_adds_candidate_to_learning_basket(); print('learning suggestion tests ok')"
```

Smart fortsättning:

```powershell
.\.venv\Scripts\python.exe -c "import test_output_handler as t; t.test_prefixes_space_for_recent_continuation(); t.test_removes_single_previous_period_for_continuation(); t.test_output_text_removes_previous_period_before_paste(); print('output handler tests ok')"
```

Syntaxkontroll:

```powershell
.\.venv\Scripts\python.exe -m compileall main.py transcriber.py post_processor.py dictation_history.py correction_window.py learning_suggestions.py output_handler.py hotkey_manager.py tray.py config.py settings_window.py
```

## Bygg och deploy

Installerad kopia:

```text
C:\Program_USB\STT Dictation
```

Bygg och deploy:

```powershell
.\.venv\Scripts\pyinstaller.exe "STT Dictation.spec" --clean --noconfirm
.\deploy.bat
```

`deploy.bat` skyddar `settings.json` och `data/`, så lokal historik inte rensas
vid uppdatering.
