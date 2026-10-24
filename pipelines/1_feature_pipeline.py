"""
1 FEATURE PIPELINE
Rohdaten (Spotify Verlauf) -> Features + Label -> Hopsworks Featurestore

Ausführen mit:  python pipelines/1_feature_pipeline.py
"""
import sys
from pathlib import Path

# Damit Python unseren Ordner "src" findet
PROJEKT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJEKT))

from src.features import lade_verlauf, berechne_song_features

# Welche Daten? Wenn echte Daten in data/raw liegen -> die nehmen, sonst die Beispieldaten
if list((PROJEKT / "data" / "raw").glob("StreamingHistory_music_*.json")):
    DATEN_ORDNER = PROJEKT / "data" / "raw"
else:
    DATEN_ORDNER = PROJEKT / "data" / "sample"

# ---------- Schritt 1: Rohdaten laden ----------
print(f"1) Lade Daten aus {DATEN_ORDNER.name}/ ...")
plays = lade_verlauf(DATEN_ORDNER)
print(f"   {len(plays)} Plays, {plays['song_id'].nunique()} verschiedene Songs")
print(f"   Zeitraum: {plays['played_at'].min():%d.%m.%Y} bis {plays['played_at'].max():%d.%m.%Y}")

# ---------- Schritt 2 + 3: Features und Label berechnen ----------
print("\n2) Berechne Features ...")
features = berechne_song_features(plays)
fertig = features[features["label_fertig"]]
print(f"   {len(features)} Songs mit Features")
print(f"   davon {len(fertig)} mit fertigem Label, "
      f"{fertig['is_favorite'].sum()} Lieblingssongs ({fertig['is_favorite'].mean():.0%})")

print("\n   So sieht die Tabelle aus (erste 5 Zeilen):")
print(features.drop(columns=["artist", "track"]).head().to_string(index=False))

# ---------- Schritt 4 + 5: In Hopsworks speichern ----------
import os
import hopsworks
from dotenv import load_dotenv

load_dotenv()

print("\n3) Verbinde mit Hopsworks ...")
project = hopsworks.login(
    host=os.getenv("HOPSWORKS_HOST"),
    project=os.getenv("HOPSWORKS_PROJECT"),
    api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    cert_folder=str(PROJEKT / ".hopsworks_certs"),
)
fs = project.get_feature_store()

# Hopsworks will die Zeit ohne Zeitzone, darum UTC entfernen
features["first_played_at"] = features["first_played_at"].dt.tz_localize(None)

# Schritt 4: Feature Group erstellen (oder holen, falls es sie schon gibt)
fg = fs.get_or_create_feature_group(
    name="song_features",
    version=1,
    primary_key=["song_id"],
    event_time="first_played_at",
    time_travel_format="HUDI",
    description="Features pro Song aus der ersten Woche und Label (Lieblingssong ja/nein)",
)

# Schritt 5: Daten einfügen
print("4) Speichere Features in Hopsworks ...")
fg.insert(features)
print(f"   fertig, {len(features)} Songs in der Feature Group 'song_features'")
