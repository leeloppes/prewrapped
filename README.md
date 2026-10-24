# PreWrapped

Projektarbeit MLOps – Leandro Lopes – Abgabe 15.11.2026

>  Noch in Arbeit. Die Kapitel mit TODO: fülle ich aus, sobald der Teil fertig ist.

---

## Worum geht es?

Spotify Wrapped zeigt einem Ende Jahr, was man am meisten gehört hat. Ich wollte das umdrehen:
Wenn ich einen neuen Song entdecke, soll mein Modell nach einer Woche (7 Tagen) sagen, ob das ein Lieblingssong von mir wird.

Ein Song ist für mich ein Lieblingssong, wenn ich ihn in den ersten 30 Tagen mindestens 10 Mal höre.

## Daten

- **Für das Training:** mein eigener Spotify Datenexport (Hörverlauf vom letzten Jahr).
  Da steht drin, wann ich welchen Song wie lange gehört habe.
- **Für die Vorhersage:** die Spotify Web API. Damit hole ich live meine zuletzt gehörten Songs.

Meine echten Daten sind nicht auf GitHub, weil das private Daten sind.
Zum Ausprobieren gibt es Beispieldaten in `data/sample/`.

TODO: *Wie viele Songs / Plays sind es? Wie viele davon wurden Lieblingssongs?*

## Features

| Feature | Art | Was es ist |
|---|---|---|
| TODO: | aggregiert | |
| TODO: | RT (live) | |

## Modell

TODO: *Welches Modell und warum.*

## Aufbau (die 3 Pipelines)

TODO: *Kurz erklären, was jede Pipeline macht.*

1. **Feature Pipeline** – `pipelines/1_feature_pipeline.py`
2. **Training Pipeline** – `pipelines/2_training_pipeline.py`
3. **Inferenz Pipeline** – `pipelines/3_inference_pipeline.py`

## So bringt man es zum Laufen

**Was man braucht:** Python 3.13, ein Hopsworks Account, ein Spotify Premium Account mit einer Developer App.

```powershell
# 1. Repo holen
git clone https://github.com/leeloppes/prewrapped.git
cd prewrapped

# 2. Umgebung erstellen und Pakete installieren
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Keys eintragen
# .env.example kopieren, in .env umbenennen und eigene Keys eintragen
```

**Auf Windows:** zuerst den Ordner `C:\tmp` erstellen (`mkdir C:\tmp`), sonst kann Hopsworks keine Daten hochladen (siehe Schwierigkeiten).

TODO: *Reihenfolge zum Ausführen der Pipelines.*

## Resultat

TODO: *Was kommt raus? Beispiel-Ausgabe.*

## Schwierigkeiten

- **Hopsworks Version:** Zuerst hatte ich Version 5.2.1 installiert, der Server läuft aber auf 5.1.
  Es kam eine Warnung → ich habe die passende Version 5.1.2 installiert.
- **Hopsworks auf Windows (3 Probleme):** Hopsworks ist vor allem für Linux und Mac gemacht.
  Auf Windows hatte ich drei Fehler:
  1. Beim Login wollte Hopsworks Zertifikate im Ordner `/tmp` speichern. Den gibt es auf Windows nicht
     → Fehler "Pfad nicht gefunden". Lösung: mit `cert_folder` einen eigenen Ordner im Projekt angeben.
  2. Beim Erstellen der Feature Group: Das Standard-Format "DELTA" braucht eine Bibliothek,
     die es nur für Linux/Mac gibt. Lösung: `time_travel_format="HUDI"` verwenden.
  3. Beim Hochladen schreibt Hopsworks nochmals Dateien nach `/tmp`, diesmal fest im Code
     (ignoriert `cert_folder`). Lösung: Ordner `C:\tmp` von Hand erstellen (`mkdir C:\tmp`).
- **Spotify API 2026:** Spotify hat viele Funktionen für Entwickler gesperrt
  (z.B. Tempo, Tanzbarkeit, Beliebtheit von Songs). Darum nutze ich nur mein Hörverhalten.
- **Spotify Redirect URI:** Muss `http://127.0.0.1:8888/callback` sein, `localhost` wird nicht mehr akzeptiert.
- **Zeitzone:** Die Spotify API gibt die Zeit in UTC zurück (z.B. 10:20 statt 12:20 bei uns).
  Muss man bei Features wie der Uhrzeit beachten.

TODO: *wird laufend ergänzt*

## Was nicht so gut geht (Limitationen)

TODO: *Einschränkungen.*

## Projektstruktur

```
data/raw/      meine echten Daten (nicht auf GitHub)
data/sample/   Beispieldaten
pipelines/     die 3 Pipelines
src/           Hilfsfunktionen
notebooks/     zum Ausprobieren
```
