"""
2 TRAINING PIPELINE
Features aus Hopsworks holen -> Modell trainieren -> Modell in die Model Registry

Ausführen mit:  python pipelines/2_training_pipeline.py
"""
import os
import sys
from pathlib import Path

import hopsworks
import joblib
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

PROJEKT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJEKT))
from src.features import FEATURE_SPALTEN, LABEL_SPALTE

load_dotenv()

# ---------- Verbinden ----------
print("1) Verbinde mit Hopsworks ...")
project = hopsworks.login(
    host=os.getenv("HOPSWORKS_HOST"),
    project=os.getenv("HOPSWORKS_PROJECT"),
    api_key_value=os.getenv("HOPSWORKS_API_KEY"),
    cert_folder=str(PROJEKT / ".hopsworks_certs"),
)
fs = project.get_feature_store()

# ---------- Schritt 1: Feature Group laden ----------
fg = fs.get_feature_group(name="song_features", version=1)

# ---------- Schritt 2: Feature View erstellen ----------
# Die Query sagt, welche Spalten wir wollen: die Features + das Label.
# Mit dem Filter nehmen wir nur Songs, bei denen der Monat schon vorbei ist (Label sicher).
print("2) Erstelle Feature View ...")
query = fg.select(FEATURE_SPALTEN + [LABEL_SPALTE]).filter(fg.label_fertig == True)

fv = fs.get_or_create_feature_view(
    name="song_favorite_view",
    version=1,
    query=query,
    labels=[LABEL_SPALTE],
    description="Features aus der ersten Woche + Label, nur Songs mit fertigem Label",
)

# ---------- Schritt 3: Training Dataset erstellen ----------
# Hopsworks teilt die Daten auf: 80 % zum Trainieren, 20 % zum Testen
print("3) Hole Trainingsdaten ...")
X_train, X_test, y_train, y_test = fv.train_test_split(
    test_size=0.2,
    description="80/20 Split",
)
y_train = y_train[LABEL_SPALTE]
y_test = y_test[LABEL_SPALTE]
print(f"   {len(X_train)} Songs zum Trainieren, {len(X_test)} zum Testen")

# ---------- Schritt 4: Modell trainieren und bewerten ----------
print("4) Trainiere Modell ...")
modell = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
modell.fit(X_train[FEATURE_SPALTEN], y_train)

vorhersage = modell.predict(X_test[FEATURE_SPALTEN])
accuracy = accuracy_score(y_test, vorhersage)
f1 = f1_score(y_test, vorhersage)

# Vergleich mit einer ganz einfachen Regel: "Es ist nie ein Lieblingssong"
baseline = accuracy_score(y_test, [0] * len(y_test))

print(f"   Accuracy: {accuracy:.2f}  (einfache Regel 'nie Lieblingssong': {baseline:.2f})")
print(f"   F1-Score: {f1:.2f}")
print("   Wichtigste Features:")
wichtigkeit = sorted(zip(FEATURE_SPALTEN, modell.feature_importances_), key=lambda x: -x[1])
for name, wert in wichtigkeit:
    print(f"     {name:<22} {wert:.2f}")

# ---------- Schritt 5: Modell speichern ----------
print("5) Speichere Modell ...")
modell_ordner = PROJEKT / "models" / "prewrapped_model"
modell_ordner.mkdir(parents=True, exist_ok=True)
joblib.dump(modell, modell_ordner / "model.pkl")

mr = project.get_model_registry()
hops_modell = mr.sklearn.create_model(
    name="prewrapped_model",
    metrics={"accuracy": accuracy, "f1": f1},
    description="Random Forest: wird ein neuer Song ein Lieblingssong?",
    input_example=X_train[FEATURE_SPALTEN].head(1),
    feature_view=fv,
)
hops_modell.save(str(modell_ordner))
print(f"   fertig, Modell Version {hops_modell.version} in der Model Registry")
