"""
Erstellt erfundene Beispieldaten im GLEICHEN Format wie der Spotify Export
(Datei "StreamingHistory_music_0.json" aus den Kontodaten).

So kann man das Projekt testen, ohne echte Spotify-Daten zu haben.
Ausführen mit:  python src/beispieldaten_erstellen.py

Format von einem Eintrag (wie bei Spotify):
    {"endTime": "2026-03-14 18:42", "artistName": "...", "trackName": "...", "msPlayed": 187000}
    endTime  = wann der Song fertig war (UTC)
    msPlayed = wie lange gehört, in Millisekunden (1000 ms = 1 Sekunde)
"""
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)  # gleicher "Zufall" bei jedem Ausführen -> immer gleiche Daten

START = datetime(2025, 10, 18)  # Beginn vom Verlauf (1 Jahr)
TAGE = 365
ANZAHL_SONGS = 1200
ANTEIL_LIEBLINGSSONGS = 0.15  # ca. 15 % der neuen Songs werden Lieblingssongs

# Erfundene Namen (keine echten Artists)
SILBEN = ["Lu", "Ka", "Mo", "Zé", "Ri", "Na", "Vo", "Tex", "Bly", "Ju", "Ro", "Fi", "Sa", "Dro"]
WOERTER = ["Nacht", "Blau", "Gold", "Regen", "Signal", "Neon", "Echo", "Herz", "Sommer",
           "Stadt", "Feuer", "Wellen", "Mond", "Kreis", "Glas", "Wind", "Licht", "Zeit"]


def poisson(mittelwert):
    """Zufällige Anzahl (0, 1, 2, ...) mit gegebenem Durchschnitt."""
    grenze, k, p = math.exp(-mittelwert), 0, 1.0
    while True:
        p *= random.random()
        if p < grenze:
            return k
        k += 1


# 1) Artists erfinden. "beliebt" = wie gern ich den Artist höre
artists = []
for i in range(60):
    name = random.choice(SILBEN) + random.choice(SILBEN).lower() + random.choice(["", " MC", " 99", "x"])
    artists.append({"name": f"{name} {i}", "beliebt": random.random()})

# 2) Songs erfinden. Jeder Song wird an einem zufälligen Tag "entdeckt"
songs = []
for i in range(ANZAHL_SONGS):
    artist = random.choices(artists, weights=[a["beliebt"] + 0.1 for a in artists])[0]
    # Songs von beliebten Artists werden eher zu Lieblingssongs
    chance = ANTEIL_LIEBLINGSSONGS * (0.5 + artist["beliebt"])
    songs.append({
        "artist": artist["name"],
        "titel": f"{random.choice(WOERTER)} {random.choice(WOERTER).lower()} {i}",
        "entdeckt": random.randint(0, TAGE - 1),
        "liebling": random.random() < chance,
        "laenge_ms": random.randint(140_000, 260_000),
    })

# 3) Plays erzeugen: Wie oft wird ein Song an jedem Tag nach dem Entdecken gehört?
plays = []
for song in songs:
    for tag in range(60):  # die ersten 60 Tage nach dem Entdecken
        datum = song["entdeckt"] + tag
        if datum >= TAGE:
            break
        if song["liebling"]:
            pro_tag = 1.2 * math.exp(-tag / 35)  # oft, langsam weniger
            skip_chance = 0.08
        else:
            pro_tag = 0.8 * math.exp(-tag / 2.5)  # am Anfang ein paar Mal, dann kaum noch
            skip_chance = 0.35
        if tag == 0:
            pro_tag = max(pro_tag, 1)  # am Entdeckungstag mindestens ca. 1 Play

        for _ in range(poisson(pro_tag)):
            # Uhrzeit: eher am Nachmittag/Abend
            stunde = min(23, max(6, int(random.gauss(17, 4))))
            zeit = START + timedelta(days=datum, hours=stunde, minutes=random.randint(0, 59))
            if random.random() < skip_chance:
                ms = random.randint(3_000, 29_000)  # geskippt (unter 30 Sek.)
            else:
                ms = song["laenge_ms"] - random.randint(0, 5_000)
            plays.append({
                "endTime": zeit.strftime("%Y-%m-%d %H:%M"),
                "artistName": song["artist"],
                "trackName": song["titel"],
                "msPlayed": ms,
            })

# 4) Nach Zeit sortieren (wie bei Spotify) und speichern
plays.sort(key=lambda p: p["endTime"])
ziel = Path(__file__).resolve().parent.parent / "data" / "sample" / "StreamingHistory_music_0.json"
ziel.write_text(json.dumps(plays, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"{len(plays)} Plays von {ANZAHL_SONGS} Songs erstellt")
print(f"   davon {sum(s['liebling'] for s in songs)} Lieblingssongs")
print(f"   gespeichert in: {ziel}")
