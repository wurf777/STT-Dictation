# Operation inlärningskurva

Status för STT Dictation efter arbetet med smartare diktering.

## Klart

- Appen återställer Windows urklipp efter automatisk inklistring.
- Urklipp återställs med fördröjning (`clipboard_restore_delay_ms`, standard 500 ms) för att undvika att målappen hinner klistra in gammalt urklipp.
- Senaste diktat sparas i appens eget minne och kan klistras in igen med F10.
- Lokal diktathistorik sparas i `data/dictation_history.jsonl`.
- Historiken ignoreras av git via `data/` i `.gitignore`.
- Varje historikpost kan innehålla:
  - `raw_text`
  - `processed_text`
  - `output_text`
  - `corrected_text`
  - `segments`
  - `words`
  - `pauses`
- Korrigeringsfönster finns via Ctrl+Alt+F10 och tray-menyn.
- Korrigeringsfönstret har knappar för:
  - spara facit
  - spara och klistra in korrigerad text
  - godkänna direkta ordlisteförslag
  - lägga ordlisteförslag i en lärandekorg
- Korrigeringsfönstret försöker lyfta sig till fokus när det öppnas.
- Korrigeringsfönstret visar en enkel diff mellan rå Whisper-text och facit.
- Om rå text och facit är identiska förklarar fönstret att appen inte har någon
  skillnad att lära sig av ännu.
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
- Efterprocessorn sväljer extra Whisper-skiljetecken efter kommandoord, till exempel `utropstecken,` -> `!`.

## Viktiga filer

- `post_processor.py` - svensk regelbaserad efterbehandling.
- `test_post_processor.py` - enkla regressionstester för efterprocessorn.
- `dictation_history.py` - lokal historik och korrigeringar.
- `correction_window.py` - GUI för att korrigera senaste diktat.
- `learning_suggestions.py` - föreslår replacement-regler och sparar lärandekorg.
- `output_handler.py` - urklipp, inklistring och senaste diktat.
- `transcriber.py` - Whisper-transkribering, ordtider och pauser.

## Testkommandon

Eftersom `pytest` inte finns i `.venv` just nu kör vi testerna direkt:

```powershell
.\.venv\Scripts\python.exe -c "import test_post_processor as t; t.test_punctuation_commands(); t.test_line_break_commands(); t.test_spacing_cleanup(); t.test_command_words_swallow_whisper_punctuation(); t.test_literal_command_words_in_examples(); print('post processor tests ok')"
```

Syntaxkontroll:

```powershell
.\.venv\Scripts\python.exe -m compileall main.py transcriber.py post_processor.py dictation_history.py correction_window.py learning_suggestions.py output_handler.py hotkey_manager.py tray.py config.py
```

## Installerad kopia

Tidigare deploy-script pekar på:

```text
C:\Program_USB\STT Dictation
```

Bygg och deploy:

```powershell
.\.venv\Scripts\pyinstaller.exe "STT Dictation.spec" --clean --noconfirm
.\deploy.bat
```

`deploy.bat` kopierar `dist\STT Dictation` till `C:\Program_USB\STT Dictation` och undantar `settings.json`.

## Nästa steg

1. Fortsätt testa efterprocessorn i vanlig diktering.
2. När den gör fel: lägg exempel i `test_post_processor.py` och justera reglerna.
3. Förbättra ordlistan till flera varianter per rätt ord, till exempel:
   - `Terört elle?` från `terort eller`, `t-rört`, `terört eller`
   - `ChatGPT` från `chat gpt`, `chatt gpt`, `chat-gpt`
4. Bygg ett analysverktyg för `data/dictation_history.jsonl`.
5. Analysera faktiska pauser och föreslå regler för:
   - komma
   - punkt
   - tre punkter
   - nytt stycke
6. Bygg kontextmedveten fortsättning mellan flera diktat:
   - appen minns senaste texten den själv klistrade in
   - om nästa diktat snabbt verkar fortsätta samma mening kan appen ta bort
     sista punkt, lägga blanksteg och klistra in fortsättningen
   - bara gör detta när appen är ganska säker på att markören fortfarande står
     direkt efter senaste inklistringen
7. Senare: lägg till lokal Gemma/Ollama-polering som ett valfritt steg efter regelbaserad efterprocessor.

## Kända begränsningar

- Efterprocessorn är regelbaserad och kommer behöva fler undantag.
- Den kan fortfarande misstolka kommandoord som används som vanliga ord.
- Pausdata loggas men används inte för output ännu.
- Korrigeringsfacit sparas, men det finns ännu inget analysverktyg som föreslår nya regler automatiskt.
- Om automatisk inklistring ger förra diktatet men F10 ger rätt diktat, är det troligen clipboard-race. Höja `clipboard_restore_delay_ms`.

## Tillagt: första lärandeförslagen

- `learning_suggestions.py` jämför rå Whisper-text med korrigerat facit och
  föreslår korta konkreta ersättningsregler.
- `correction_window.py` visar nu en lista med förslag under korrigeringsrutan.
- Knapparna `Använd markerad` och `Använd alla` sparar förslag till
  `replacements` i `settings.json`.
- Knapparna `Spara markerad` och `Spara alla` sparar förslag till
  `data/learning_basket.jsonl` utan att aktivera dem.
- Det är medvetet att första versionen använder `replacements` i stället för
  `vocabulary`: ersättningar är exakta och ger direkt effekt, medan vocabulary
  bara nudgar Whisper och inte garanterar resultat.

## Aktuell strategi för smartare inlärning

1. Fortsätt samla riktiga exempel i `data/dictation_history.jsonl`.
2. Använd korrigeringsfönstret för att spara facit när Whisper eller
   efterprocessorn gör fel.
3. Godkänn bara enkla, uppenbara regler direkt.
4. Lägg osäkra förslag i `data/learning_basket.jsonl` och gå igenom dem senare.
5. När korgen och historiken innehåller tillräckligt många riktiga exempel kan
   en lokal Gemma/Ollama-modell analysera mönster och föreslå mer generella
   regler.

Språkmodellen ska inledningsvis vara ett analyslager: den får föreslå och
förklara, men inte automatiskt skriva om alla diktat utan godkännande.

## Framtida: kontextmedveten fortsättning

Problem: Om ett diktat slutar med punkt och nästa diktat egentligen är en
fortsättning av samma mening måste användaren idag manuellt ta bort punkten och
lägga in blanksteg.

Första enkla implementationen finns i `output_handler.py`:

- Appen minns senaste automatiska inklistring.
- Om nästa diktat kommer inom `smart_leading_space_window_seconds` sekunder kan
  appen lägga till ett inledande blanksteg.
- Om förra inklistringen slutade med en enkel punkt och nästa diktat ser ut som
  en fortsättning, till exempel börjar med `och`, `men`, `att` eller liten
  bokstav, skickar appen Backspace före inklistringen. Då försvinner punkten och
  den nya texten klistras in med ett inledande blanksteg.
- Funktionen styrs av `smart_leading_space_enabled` och
  `smart_remove_previous_period_enabled`.

Första versionen bör vara försiktig och bygga på appens eget minne:

- Spara metadata om senaste automatiska inklistring: text, sluttid, längd och
  om den slutade med punkt.
- När nästa diktat kommer inom ett kort tidsfönster och börjar som en
  fortsättning, exempelvis med `och`, `men`, `att`, `som`, `därför` eller liten
  bokstav, föreslå eller gör en sammanfogning.
- Sammanfogning betyder: ta bort sista punkten från förra inklistringen, lägg
  ett blanksteg och klistra in den nya texten.
- Ha en säkerhetsregel: ändra bara om appen rimligen vet att markören står kvar
  direkt efter förra inklistringen. Annars klistras texten in normalt.

Mer avancerad kontextläsning runt markören via Windows UI Automation kan provas
senare, men den är beroende av målprogrammet och bör inte vara första steget.

Test för lärandeförslag:

```powershell
.\.venv\Scripts\python.exe -c "import test_learning_suggestions as t; t.test_suggests_short_replacement_from_correction(); t.test_skips_identical_text(); t.test_adds_candidate_to_learning_basket(); print('learning suggestion tests ok')"
```

## Tillagt: säkrare användardata vid deploy

- Installerad app använder nu mappen bredvid `STT Dictation.exe` för
  `settings.json` och `data/`.
- `deploy.bat` har kort retry-tid (`/R:2 /W:2`) så kopiering inte fastnar om
  appen fortfarande är igång.
- `deploy.bat` skyddar `data` och legacy-`_internal\data` från purge, så lokal
  historik inte rensas vid uppdatering.
