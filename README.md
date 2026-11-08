# PreWrapped

Projektarbeit MLOps – Leandro Lopes – CAS AI Operations

## Worum geht es?

Spotify Wrapped zeigt Ende Jahr, was man am meisten gehört hat. Ich wollte das umdrehen:
Wenn ich einen neuen Song entdecke, soll mein Modell nach einer Woche sagen, ob der Song bei mir hängen bleibt.

Ein neuer Song gilt als Lieblingssong (`is_favorite`), wenn ich ihn nach der ersten Woche (Tag 7 bis 30)
noch mindestens 2 Mal höre. Ein Play zählt erst ab 30 Sekunden, sonst gilt er als geskippt.

Am Anfang hatte ich "mindestens 10 Plays in Tag 0 bis 30". Das waren aber nur 0.7 % Lieblingssongs,
und die Plays aus der ersten Woche zählten schon zum Label (Data Leakage). Darum zähle ich jetzt nur,
was nach der Vorhersage passiert.

## Daten

- **Spotify Datenexport** (`StreamingHistory_music_*.json`): mein Hörverlauf vom 25.10.2025 bis 28.10.2026,
  38'522 Plays. Daraus kommen die Features und die Trainingsdaten.
- **Spotify Web API**: meine letzten 50 Plays, live. Die brauche ich bei der Inferenz.
- **Beispieldaten** in `data/sample/`: erfundene Daten zum Ausprobieren ohne eigenen Export.

Meine echten Daten sind privat und nicht auf GitHub. Wenn `data/raw/` leer ist, nimmt die Feature Pipeline
automatisch die Beispieldaten. Songs aus den ersten 30 Tagen vom Verlauf lasse ich weg, weil ich die
vielleicht schon vorher kannte. Am Schluss habe ich 7'113 Songs zum Trainieren, davon 439 Lieblingssongs (6 %).

## Features

| Feature | Art | Was es ist |
|---|---|---|
| `plays_first_7d` | aggregiert | Plays in der ersten Woche |
| `skip_rate_first_7d` | aggregiert | Anteil Skips in der ersten Woche |
| `days_with_play_7d` | aggregiert | An wie vielen Tagen der ersten Woche gehört |
| `artist_plays_90d` | aggregiert | Wie oft ich den Artist in den 90 Tagen davor gehört habe |
| `played_last_24h` | RT | In den letzten 24 Stunden gehört? |
| `hour_of_last_play` | RT | Uhrzeit vom letzten Play (Schweizer Zeit) |

Die aggregierten Features werden in `src/features.py` berechnet und im Featurestore gespeichert.
Die RT-Features werden bei der Inferenz mit den Live-Daten von Spotify neu berechnet.
Primary Key ist `song_id` ("Artist - Titel"), Event Time ist `first_played_at`.

## Modell

Ein Random Forest von scikit-learn (100 Bäume, `max_depth=5`). Weil nur 6 % Lieblingssongs sind,
nehme ich `class_weight="balanced"`, sonst sagt das Modell einfach immer "nein".

Auf den Testdaten (Modell Version 4): Accuracy 0.69, F1 0.16. Die einfache Regel "nie Lieblingssong"
hat zwar ca. 93 % Accuracy, findet aber keinen einzigen Lieblingssong (F1 = 0). Das Modell ist also
schwach, aber besser als nichts. Am wichtigsten sind die Plays in der ersten Woche und ob ich den Artist schon kenne.

![Model Registry](docs/hopsworks_model_registry.png)

## Aufbau (die 3 Pipelines)

```
1 Feature Pipeline:   Spotify Export   ──► Feature Group "song_features" (Hopsworks)
2 Training Pipeline:  Feature Group    ──► Feature View ──► Modell ──► Model Registry (Hopsworks)
3 Inferenz Pipeline:  Spotify API live + Feature View + Model Registry ──► Top 10 neue Songs mit Chance
```

1. **Feature Pipeline** (`pipelines/1_feature_pipeline.py`): lädt den Spotify Export, berechnet Features
   und Label und speichert sie in der Feature Group `song_features`.
2. **Training Pipeline** (`pipelines/2_training_pipeline.py`): erstellt die Feature View, teilt die Daten
   in Hopsworks 80/20 auf (nur Songs mit fertigem Label), trainiert das Modell und speichert es in der Model Registry.
3. **Inferenz Pipeline** (`pipelines/3_inference_pipeline.py`): holt meine letzten 50 Plays von Spotify,
   lädt die Features der Songs, bei denen der erste Monat noch nicht vorbei ist, berechnet die RT-Features neu,
   holt das neueste Modell und zeigt die Top 10.

In Hopsworks sind Feature Group v1 und Feature View v1 noch mit den Beispieldaten.
Aktuell benutzt werden Feature Group v2, Feature View v3 und Modell Version 4.

## So bringt man es zum Laufen

Man braucht Python 3.13, einen Hopsworks Account mit API-Key und Spotify Premium mit einer App im
Developer Dashboard (Redirect URI `http://127.0.0.1:8888/callback`, Web API).

```powershell
git clone https://github.com/leeloppes/prewrapped.git
cd prewrapped
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# .env.example kopieren, in .env umbenennen und die eigenen Keys eintragen
python test_verbindungen.py   # optional: testet Hopsworks und Spotify
```

Auf Windows zuerst `mkdir C:\tmp` (siehe Schwierigkeiten). Die eigenen Spotify Dateien
`StreamingHistory_music_*.json` kommen nach `data/raw/`. Dann die Pipelines nacheinander starten:

```powershell
python pipelines/1_feature_pipeline.py
# ca. 2-5 Minuten warten, bis der Job in Hopsworks unter "Jobs" fertig ist
python pipelines/2_training_pipeline.py
python pipelines/3_inference_pipeline.py
```

## Resultat

Die Vorhersage vom 05.11.2026 (Songs, die ich im Oktober entdeckt habe):

```
    78%  Lithe - For What (feat. Cash Cobain)
    78%  Lithe - Leaning
    75%  Loe Shimmy - Seduce You
    74%  Kale Joseph - HIGH HOPES
    74%  Josh Levi - EGO
```

Später habe ich noch meinen erweiterten Streamingverlauf (bis 05.11.2026) bekommen und nachgeschaut,
ob die Songs wirklich hängen geblieben sind. Von 579 neuen Songs aus dem Oktober sind nur 6 hängen geblieben,
und keiner davon war in den Top 10 % vom Modell. Das Modell hat im Oktober also nicht getroffen.

Um die Live-Daten zu testen, habe ich am 08.11. "HIGH HOPES" nochmals gehört und direkt danach die
Inferenz gestartet. Die Pipeline hat den Song in den Live-Daten gefunden und er ist von Platz 4 (74 %)
auf Platz 28 (66 %) gefallen. Dazwischen habe ich aber neu trainiert, ein Teil davon kann auch vom neuen Modell kommen.

Dabei habe ich gemerkt: Die Pipeline hat Songs aus den letzten 30 Tagen ab heute genommen. Mit älteren
Daten (oder den Beispieldaten) findet sie so mit der Zeit keine Songs mehr. Jetzt zählen die 30 Tage ab dem
Ende der Daten. Ausserdem wird `played_last_24h` jetzt für alle Songs neu berechnet (nicht in den Live-Daten = 0).

![Live-Test](docs/inferenz_live_test.png)

## Schwierigkeiten

- **Hopsworks Version:** Der Server lief auf 5.1, darum habe ich `hopsworks==5.1.2` installiert. Am 08.11.2026
  wurde der Server auf 5.2 aktualisiert. Es kommt eine Warnung, aber alles läuft weiter. Falls es mal
  Probleme gibt: `pip install "hopsworks[python]==5.2.*"`.
- **Hopsworks auf Windows:** Hopsworks ist für Linux/Mac gemacht. Ich musste einen eigenen `cert_folder`
  angeben, `time_travel_format="HUDI"` verwenden (DELTA geht nur auf Linux/Mac) und `C:\tmp` von Hand erstellen,
  weil Hopsworks dort fest Dateien speichern will.
- **Warten nach der Feature Pipeline:** Startet man das Training zu früh, kommt "Could not read data using
  Hopsworks Query Service", weil der Job im Hintergrund noch nicht fertig ist.
- **Primary Key umbenannt:** Bei `get_batch_data` schreibt Hopsworks den Tabellennamen vor `song_id`.
- **Spotify API:** Viele Funktionen (Tempo, Beliebtheit usw.) sind seit 2026 gesperrt, darum nur Hörverhalten.
  Die Redirect URI muss `127.0.0.1` sein, `localhost` geht nicht mehr. Die Zeit kommt in UTC.

## Limitationen

- Das Modell ist schwach (F1 0.16) und hat im Backtest nicht getroffen. Ob ein Song hängen bleibt,
  hängt von vielem ab, das nicht in den Daten ist.
- Ich höre sehr breit: 69 % der neuen Songs höre ich nur einmal. Lieblingssongs sind darum selten.
- Data Drift: Im Training waren 6 % Lieblingssongs, im Oktober nur 1 %. Man müsste regelmässig neu trainieren.
- Die API gibt nur 50 Plays zurück (ca. ein halber Tag). Für die erste Woche braucht es den Export,
  und der kommt nur auf Anfrage.
- Skips sind geschätzt (unter 30 Sekunden) und die Song-ID ist nur "Artist - Titel".
- Der 80/20 Split ist zufällig. Ein Split nach Zeit wäre ehrlicher.

Als nächsten Schritt würde ich das Modell mit dem erweiterten Streamingverlauf trainieren
(mehrere Jahre, echte Skip-Info) und im Dezember mit meinem Spotify Wrapped 2026 vergleichen.

## Projektstruktur

```
data/raw/            meine Spotify Daten (nicht auf GitHub)
data/sample/         Beispieldaten
pipelines/           die 3 Pipelines
src/features.py      Berechnung der Features und des Labels
notebooks/           erste Versuche mit den Beispieldaten
docs/                Screenshots aus Hopsworks (Model Registry, Statistiken der Features, Live-Test)
test_verbindungen.py testet Hopsworks und Spotify
requirements.txt     Python Pakete
.env.example         Vorlage für die Keys
```
