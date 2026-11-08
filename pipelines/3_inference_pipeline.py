"""
3 INFERENZ PIPELINE
Live-Daten von Spotify + neueste Features aus Hopsworks + Modell -> Vorhersage

Für welche Songs? Für neue Songs, bei denen der erste Monat noch nicht vorbei ist
(die letzten 30 Tage vom Verlauf). Bei denen weiss man noch nicht, ob sie hängen bleiben.

Ausführen mit:  python pipelines/3_inference_pipeline.py
"""
import os
import sys
from pathlib import Path

import hopsworks
import joblib
import pandas as pd
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

PROJEKT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJEKT))
from src.features import FEATURE_SPALTEN, ZEITZONE

load_dotenv()
jetzt = pd.Timestamp.now(tz="UTC")

# Live-Daten von Spotify holen
print("1) Hole meine zuletzt gehörten Songs von Spotify ...")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-read-recently-played",
    cache_path=str(PROJEKT / ".cache"),
))
live = []
for eintrag in sp.current_user_recently_played(limit=50)["items"]:
    song = eintrag.get("track") or eintrag.get("item")  # Spotify hat "track" teilweise umbenannt
    live.append({
        "song_id": song["artists"][0]["name"] + " - " + song["name"],
        "played_at": pd.to_datetime(eintrag["played_at"], utc=True),
    })
live = pd.DataFrame(live)
print(f"   {len(live)} Plays, der letzte um {live['played_at'].max().tz_convert(ZEITZONE):%d.%m. %H:%M}")

# Feature View holen und neueste Features laden
print("2) Lade die Features der neuen Songs aus Hopsworks ...")
project = hopsworks.login(
    host=os.getenv("HOPSWORKS_HOST"),
    project=os.getenv("HOPSWORKS_PROJECT"),
    api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    cert_folder=str(PROJEKT / ".hopsworks_certs"),
)
fs = project.get_feature_store()
fv = fs.get_feature_view(name="song_favorite_view", version=3)

# Alle Songs aus der Feature View holen, mit Primary Key und Event Time
neue = fv.get_batch_data(primary_key=True, event_time=True)

# Hopsworks schreibt den Tabellennamen vor Spalten, die keine Features sind
# (z.B. "song_features_2_song_id"). Wir benennen sie wieder einfach.
for name in ["song_id", "first_played_at"]:
    spalte = [s for s in neue.columns if s.endswith(name)][0]
    neue = neue.rename(columns={spalte: name})
neue["first_played_at"] = pd.to_datetime(neue["first_played_at"])

# Nur neue Songs, bei denen der erste Monat noch nicht vorbei ist (Ergebnis noch offen).
# Gezählt ab dem Ende der Daten und nicht ab heute, sonst findet man mit älteren Daten nichts mehr.
# Die Feature Group hat nur Songs mit fertiger erster Woche, darum: letzter Song + 7 Tage = Ende der Daten.
ende_daten = neue["first_played_at"].max() + pd.Timedelta(days=7)
neue = neue[neue["first_played_at"] > ende_daten - pd.Timedelta(days=30)].reset_index(drop=True)
if len(neue) == 0:
    print("   Keine neuen Songs gefunden. Ende.")
    sys.exit()
print(f"   {len(neue)} neue Songs gefunden (entdeckt ab {ende_daten - pd.Timedelta(days=30):%d.%m.%Y})")

# RT-Features mit den Live-Daten neu berechnen (kennt man erst jetzt)
# played_last_24h: für ALLE Songs neu. Ist ein Song nicht in den Live-Daten, wurde er nicht gerade gehört.
# hour_of_last_play: nur für Songs in den Live-Daten neu, sonst bleibt die letzte bekannte Uhrzeit.
letzter_live = live.groupby("song_id")["played_at"].max()
neue["played_last_24h"] = 0
gerade_gehoert = neue["song_id"].isin(letzter_live.index)
for i in neue[gerade_gehoert].index:
    letzter = letzter_live[neue.loc[i, "song_id"]]
    neue.loc[i, "played_last_24h"] = int(letzter > jetzt - pd.Timedelta(hours=24))
    neue.loc[i, "hour_of_last_play"] = letzter.tz_convert(ZEITZONE).hour
print(f"   davon {gerade_gehoert.sum()} gerade live gehört (RT-Features aktualisiert)")

# Modell aus der Model Registry holen
print("3) Lade das neueste Modell aus der Model Registry ...")
mr = project.get_model_registry()
alle_versionen = mr.get_models("prewrapped_model")
neuestes = max(alle_versionen, key=lambda m: m.version)
# Pro Version ein eigener Ordner. Ist das Modell schon da, nicht nochmals herunterladen
# (sonst gibt Hopsworks einen Fehler, weil die Datei schon existiert)
download_ordner = PROJEKT / "models" / "download" / f"v{neuestes.version}"
if not list(download_ordner.rglob("model.pkl")):
    download_ordner.mkdir(parents=True, exist_ok=True)
    neuestes.download(local_path=str(download_ordner))
modell = joblib.load(next(download_ordner.rglob("model.pkl")))
print(f"   Modell Version {neuestes.version}")

# Vorhersage
print("4) Mache die Vorhersage ...\n")
neue["chance"] = modell.predict_proba(neue[FEATURE_SPALTEN])[:, 1]
neue = neue.sort_values("chance", ascending=False)

print("PreWrapped - meine neuen Songs mit dem meisten Lieblingssong-Potenzial:")
for _, zeile in neue.head(10).iterrows():
    live_info = "  (gerade gehört)" if zeile["song_id"] in letzter_live.index else ""
    print(f"   {zeile['chance']:>4.0%}  {zeile['song_id']}{live_info}")

# Gerade live gehörte Songs extra zeigen (auch wenn sie nicht in den Top 10 sind)
neue["platz"] = range(1, len(neue) + 1)
live_songs = neue[neue["song_id"].isin(letzter_live.index)]
if len(live_songs) > 0:
    print("\nNeue Songs, die ich gerade live gehört habe:")
    for _, zeile in live_songs.iterrows():
        print(f"   {zeile['chance']:>4.0%}  Platz {zeile['platz']} von {len(neue)}  {zeile['song_id']}")
