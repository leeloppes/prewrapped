"""
3 INFERENZ PIPELINE
Live-Daten von Spotify + neueste Features aus Hopsworks + Modell -> Vorhersage

Für welche Songs? Für neue Songs, die ich in den letzten 30 Tagen entdeckt habe.
Bei denen ist der Monat noch nicht vorbei, man weiss also noch nicht, ob sie hängen bleiben.

Ausführen mit:  python pipelines/3_inference_pipeline.py
"""
import os
import sys
from datetime import datetime, timedelta
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

# ---------- Schritt 1: Live-Daten von Spotify holen ----------
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

# ---------- Schritt 2: Feature View holen und neueste Features laden ----------
print("2) Lade die Features der neuen Songs aus Hopsworks ...")
project = hopsworks.login(
    host=os.getenv("HOPSWORKS_HOST"),
    project=os.getenv("HOPSWORKS_PROJECT"),
    api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    cert_folder=str(PROJEKT / ".hopsworks_certs"),
)
fs = project.get_feature_store()
fv = fs.get_feature_view(name="song_favorite_view", version=3)

# Nur Songs, die ich in den letzten 30 Tagen zum ersten Mal gehört habe
neue = fv.get_batch_data(
    start_time=datetime.now() - timedelta(days=30),
    primary_key=True,
    event_time=True,
)
if len(neue) == 0:
    print("   Keine neuen Songs in den letzten 30 Tagen gefunden. Ende.")
    sys.exit()
print(f"   {len(neue)} neue Songs gefunden")

# Hopsworks schreibt den Tabellennamen vor den Primary Key (z.B. "song_features_2_song_id").
# Wir benennen die Spalte wieder einfach "song_id".
pk_spalte = [spalte for spalte in neue.columns if spalte.endswith("song_id")][0]
neue = neue.rename(columns={pk_spalte: "song_id"}).reset_index(drop=True)

# ---------- RT-Features mit den Live-Daten aktualisieren ----------
# Die Uhrzeit vom letzten Play und "in den letzten 24h gehört?" kennt man erst jetzt.
# Wenn ein Song gerade live gehört wurde, nehmen wir die aktuellen Werte von Spotify.
letzter_live = live.groupby("song_id")["played_at"].max()
gerade_gehoert = neue["song_id"].isin(letzter_live.index)
for i in neue[gerade_gehoert].index:
    letzter = letzter_live[neue.loc[i, "song_id"]]
    neue.loc[i, "played_last_24h"] = int(letzter > jetzt - pd.Timedelta(hours=24))
    neue.loc[i, "hour_of_last_play"] = letzter.tz_convert(ZEITZONE).hour
print(f"   davon {gerade_gehoert.sum()} gerade live gehört (RT-Features aktualisiert)")

# ---------- Schritt 3: Modell aus der Model Registry holen ----------
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

# ---------- Schritt 4: Vorhersage ----------
print("4) Mache die Vorhersage ...\n")
neue["chance"] = modell.predict_proba(neue[FEATURE_SPALTEN])[:, 1]
neue = neue.sort_values("chance", ascending=False)

print("PreWrapped - meine neuen Songs mit dem meisten Lieblingssong-Potenzial:")
for _, zeile in neue.head(10).iterrows():
    live_info = "  (gerade gehört)" if zeile["song_id"] in letzter_live.index else ""
    print(f"   {zeile['chance']:>4.0%}  {zeile['song_id']}{live_info}")
