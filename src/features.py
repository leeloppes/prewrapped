"""
Hier werden die Features berechnet.

Wichtig: Diese Funktionen werden von der Feature Pipeline UND von der Inferenz Pipeline
benutzt. So werden die Features immer gleich berechnet (kein Training-Serving Skew).
"""
from pathlib import Path

import pandas as pd

# ---------- Einstellungen ----------
MIN_MS_PLAY = 30_000        # unter 30 Sekunden gilt ein Play als geskippt
TAGE_BEOBACHTEN = 7         # nach so vielen Tagen machen wir die Vorhersage
TAGE_LABEL = 30             # in diesem Zeitraum wird gezählt, ob es ein Lieblingssong wurde
MIN_PLAYS_LIEBLING = 10     # ab so vielen Plays ist es ein Lieblingssong
TAGE_ARTIST = 90            # wie weit zurück schauen wir, ob ich den Artist kenne
ZEITZONE = "Europe/Zurich"  # Spotify speichert UTC, wir wollen Schweizer Zeit

# Diese Spalten bekommt das Modell als Input (Training und Inferenz brauchen die gleiche Liste)
FEATURE_SPALTEN = [
    "plays_first_7d",
    "skip_rate_first_7d",
    "days_with_play_7d",
    "artist_plays_90d",
    "played_last_24h",
    "hour_of_last_play",
]
LABEL_SPALTE = "is_favorite"


def lade_verlauf(ordner):
    """Liest alle Spotify-Dateien "StreamingHistory_music_*.json" aus einem Ordner
    und macht daraus eine Tabelle (DataFrame) mit einer Zeile pro Play."""
    dateien = sorted(Path(ordner).glob("StreamingHistory_music_*.json"))
    if not dateien:
        raise FileNotFoundError(f"Keine StreamingHistory_music_*.json in {ordner} gefunden")

    df = pd.concat([pd.read_json(d) for d in dateien], ignore_index=True)
    df = df.rename(columns={"endTime": "played_at", "artistName": "artist",
                            "trackName": "track", "msPlayed": "ms_played"})
    df["played_at"] = pd.to_datetime(df["played_at"], utc=True)
    df = df.dropna(subset=["artist", "track"])
    # Eine eindeutige ID pro Song: "Artist - Titel"
    df["song_id"] = df["artist"] + " - " + df["track"]
    df["gehoert"] = df["ms_played"] >= MIN_MS_PLAY  # True = richtig gehört, False = geskippt
    return df.sort_values("played_at").reset_index(drop=True)


def berechne_song_features(plays, jetzt=None):
    """Macht aus der Play-Tabelle eine Feature-Tabelle mit EINER Zeile pro Song.

    plays: Tabelle von lade_verlauf()
    jetzt: bis wann haben wir Daten? (Standard: letzter Play im Verlauf)
    """
    if jetzt is None:
        jetzt = plays["played_at"].max()

    # Wann habe ich jeden Song zum ersten Mal gehört?
    erster_play = plays.groupby("song_id")["played_at"].min().rename("first_played_at")
    df = plays.join(erster_play, on="song_id")
    df["tage_seit_erstem"] = (df["played_at"] - df["first_played_at"]).dt.total_seconds() / 86400

    zeilen = []
    for song_id, p in df.groupby("song_id"):
        erster = p["first_played_at"].iloc[0]
        vorhersage_zeit = erster + pd.Timedelta(days=TAGE_BEOBACHTEN)

        # Songs, die noch keine 7 Tage alt sind, überspringen (zu wenig Infos)
        if vorhersage_zeit > jetzt:
            continue

        # Nur Plays, die VOR dem Vorhersage-Zeitpunkt passiert sind (sonst wäre es Data Leakage)
        frueh = p[p["tage_seit_erstem"] < TAGE_BEOBACHTEN]
        letzter = frueh["played_at"].max()

        # Label: Wurde er in den ersten 30 Tagen mind. 10 Mal richtig gehört?
        label_fertig = erster + pd.Timedelta(days=TAGE_LABEL) <= jetzt
        plays_30d = p[(p["tage_seit_erstem"] < TAGE_LABEL) & p["gehoert"]].shape[0]

        zeilen.append({
            "song_id": song_id,
            "artist": p["artist"].iloc[0],
            "track": p["track"].iloc[0],
            "first_played_at": erster,
            # ---- aggregierte Features (über mehrere Tage) ----
            "plays_first_7d": int(frueh["gehoert"].sum()),
            "skip_rate_first_7d": round(1 - frueh["gehoert"].mean(), 3),
            "days_with_play_7d": int(frueh["played_at"].dt.date.nunique()),
            # ---- RT-Features (Zustand im Moment der Vorhersage) ----
            "played_last_24h": int(letzter > vorhersage_zeit - pd.Timedelta(hours=24)),
            "hour_of_last_play": int(letzter.tz_convert(ZEITZONE).hour),
            # ---- Label ----
            "is_favorite": int(plays_30d >= MIN_PLAYS_LIEBLING),
            "label_fertig": bool(label_fertig),  # False = 30 Tage noch nicht vorbei
        })

    features = pd.DataFrame(zeilen)
    features["artist_plays_90d"] = _artist_bekanntheit(plays, features)
    return features


def _artist_bekanntheit(plays, features):
    """Aggregiertes Feature: Wie oft habe ich den Artist in den 90 Tagen
    VOR dem ersten Play des Songs gehört? (= Kenne ich den Artist schon?)"""
    gehoert = plays[plays["gehoert"]]
    werte = []
    for _, zeile in features.iterrows():
        von = zeile["first_played_at"] - pd.Timedelta(days=TAGE_ARTIST)
        a = gehoert[(gehoert["artist"] == zeile["artist"])
                    & (gehoert["played_at"] >= von)
                    & (gehoert["played_at"] < zeile["first_played_at"])]
        werte.append(len(a))
    return werte
