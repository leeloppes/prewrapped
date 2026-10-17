# 🎁 PreWrapped

Projektarbeit MLOps – Leandro Lopes – Abgabe 15.11.2026

> ⚠️ Noch in Arbeit. Die Kapitel mit ✏️ fülle ich aus, sobald der Teil fertig ist.

---

## Worum geht es?

Spotify Wrapped zeigt einem Ende Jahr, was man am meisten gehört hat. Ich wollte das umdrehen:
Wenn ich einen neuen Song entdecke, soll mein Modell nach 5 Tagen sagen, ob das ein Lieblingssong von mir wird.

Ein Song ist für mich ein Lieblingssong, wenn ich ihn in den ersten 30 Tagen mindestens 10 Mal höre.

## Daten

- **Für das Training:** mein eigener Spotify Datenexport (Hörverlauf vom letzten Jahr).
  Da steht drin, wann ich welchen Song wie lange gehört habe.
- **Für die Vorhersage:** die Spotify Web API. Damit hole ich live meine zuletzt gehörten Songs.

Meine echten Daten sind nicht auf GitHub, weil das private Daten sind.
Zum Ausprobieren gibt es Beispieldaten in `data/sample/`.

✏️ *Wie viele Songs / Plays sind es? Wie viele davon wurden Lieblingssongs?*

## Features

| Feature | Art | Was es ist |
|---|---|---|
| ✏️ | aggregiert | |
| ✏️ | RT (live) | |

## Modell

✏️ *Welches Modell und warum.*

## Aufbau (die 3 Pipelines)

✏️ *Kurz erklären, was jede Pipeline macht.*

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
#    .env.example kopieren, in .env umbenennen und eigene Keys eintragen
```

✏️ *Reihenfolge zum Ausführen der Pipelines.*

## Resultat

✏️ *Was kommt raus? Beispiel-Ausgabe.*

## Was nicht so gut geht (Limitationen)

✏️ *Schwierigkeiten und Einschränkungen.*

## Projektstruktur

```
data/raw/      meine echten Daten (nicht auf GitHub)
data/sample/   Beispieldaten
pipelines/     die 3 Pipelines
src/           Hilfsfunktionen
notebooks/     zum Ausprobieren
```
