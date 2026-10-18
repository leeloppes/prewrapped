"""
Test: Klappt die Verbindung zu Hopsworks und Spotify?
Ausführen mit:  python test_verbindungen.py
"""
import os
from dotenv import load_dotenv

# Liest die geheimen Keys aus der .env-Datei
load_dotenv()


# ---------- 1. Hopsworks ----------
print("1) Verbinde mit Hopsworks ...")
import hopsworks

project = hopsworks.login(
    host=os.getenv("HOPSWORKS_HOST"),
    project=os.getenv("HOPSWORKS_PROJECT"),
    api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    # Hopsworks speichert Zertifikate standardmässig in "/tmp" - den Ordner gibt es
    # auf Windows nicht. Darum nehmen wir einen Ordner in unserem Projekt.
    cert_folder=os.path.abspath(".hopsworks_certs"),
)
fs = project.get_feature_store()  # der Featurestore
mr = project.get_model_registry()  # die Model Registry
print(f"   Hopsworks ok! Projekt: {project.name}")


# ---------- 2. Spotify ----------
print("\n2) Verbinde mit Spotify ...")
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Beim ersten Mal öffnet sich der Browser -> mit Spotify einloggen und erlauben.
# "scope" = was die App lesen darf. Hier: die zuletzt gehörten Songs.
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-recently-played"))

zuletzt = sp.current_user_recently_played(limit=5)
print("   Spotify ok! Deine letzten 5 Songs:")
for eintrag in zuletzt["items"]:
    # Spotify hat 2026 teilweise "track" in "item" umbenannt -> wir nehmen, was da ist
    song = eintrag.get("track") or eintrag.get("item")
    print(f"    {song['name']} – {song['artists'][0]['name']}  ({eintrag['played_at']})")
