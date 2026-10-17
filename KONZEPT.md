# 🎁 PreWrapped – Welche Songs landen in deinem Wrapped?

> Projektarbeit MLOps · Leandro Lopes · Abgabe: 15.11.2026 23:59
> Status: **Entwurf v2** – offene Punkte sind mit ❓ markiert

---

## 1. Die Idee in einem Satz

Spotify Wrapped zeigt dir **Ende Jahr rückblickend**, was du am meisten gehört hast.
**PreWrapped** schaut **nach vorne**: Sobald ich einen neuen Song entdecke, sagt mein Modell nach
**5 Tagen** voraus, ob er zu einem meiner **Lieblingssongs** wird – und packt die Hit-Kandidaten
automatisch in eine Playlist **"Next Favorites"**.

**Beispiel-Ausgabe der Inferenz:**
```
🎁 PreWrapped – deine neuen Songs:
  🔥 "Song A" – Artist X    81 % Lieblingssong-Potenzial  → zur Playlist hinzugefügt
  🙂 "Song B" – Artist Y    42 %
  💤 "Song C" – Artist Z     9 %
```

### Abgrenzung zu Spotify Wrapped
| Spotify Wrapped | PreWrapped (dieses Projekt) |
|---|---|
| Zählt und sortiert: "Du hast 50'000 Minuten gehört" | **Lernt** aus meinem Verhalten und **sagt voraus** |
| Schaut zurück (Vergangenheit) | Schaut nach vorne (Zukunft) |
| Statistik | Machine Learning |

## 2. Wie lernt das Modell? (Grundidee)

In meinem Verlauf vom letzten Jahr kenne ich bei alten Songs bereits **die Lösung**:
Ich kann nachzählen, ob ein Song nach dem Entdecken wirklich oft gehört wurde.

```
Song entdeckt ──► die ersten 5 Tage ──► Vorhersage-Zeitpunkt ──► ... ──► Tag 30: Lieblingssong? ja/nein
                  (daraus Features)                                        (= Label / Lösung)
```

1. **Training (historische Daten):** Das Modell sieht hunderte alte Songs mit den Features
   ("wie habe ich ihn in den ersten 5 Tagen gehört?") **und** der Lösung (wurde er ein Lieblingssong?).
   Es erkennt selbst Muster, z.B. *"Wer einen Song in den ersten Tagen 4× fertig hört, behält ihn oft."*
2. **Test:** Ein Teil der alten Songs wird zurückgehalten, um zu prüfen, ob das Modell richtig rät.
3. **Inferenz (aktuelle Daten):** Für **neu entdeckte Songs** ist die Lösung noch unbekannt –
   hier macht das Modell die eigentliche Vorhersage.

## 3. Ziele

| Priorität | Ziel | Nötig fürs Testat? |
|---|---|---|
| 🟢 Muss | 3 funktionierende Pipelines (Feature, Training, Inferenz) | ✅ Ja |
| 🟢 Muss | Hopsworks **Featurestore** für die Features | ✅ Ja |
| 🟢 Muss | Mind. 1 aggregiertes Feature + 1 Echtzeit-Feature (RT), bei der Inferenz verwendet | ✅ Ja |
| 🟢 Muss | README: Daten, Features, Modell, Pipelines, Anleitung, Limitationen | ✅ Ja |
| 🟢 Muss | Abhängigkeiten sauber definiert (Python-Version, `requirements.txt`) | ✅ Ja |
| 🔵 Soll | Beispieldaten (`data/sample/`) mit erfundenen Songs → andere können es testen | ❌ (hilft aber bei Nachvollziehbarkeit) |
| 🟡 Kann | Inferenz erstellt Spotify-Playlist **"Next Favorites"** | ❌ Ausbaustufe |
| 🟡 Kann | Web-App "Mein PreWrapped" mit Statistiken + Vorhersagen | ❌ Ausbaustufe |
| ⚪ Später | Freunde laden ihren eigenen Export hoch; erweiterter Streamingverlauf | ❌ Nach Abgabe |

## 4. Tools

| Zweck | Tool | Begründung |
|---|---|---|
| Featurestore | **Hopsworks** | Von der Aufgabenstellung vorgegeben |
| Model Registry | **Hopsworks** | Gleicher Account & Login wie der Featurestore → am einfachsten (MLflow wäre auch erlaubt, aber ein zusätzliches Tool) |
| ML | scikit-learn | Einfach, gut dokumentiert |
| Spotify-Zugriff | `spotipy` | Python-Bibliothek für die Spotify Web API |
| Code & Abgabe | GitHub | Abgabe = Link aufs Repo |

## 5. Datenquellen

| Quelle | Inhalt | Verwendung |
|---|---|---|
| **Spotify Datenexport** ("Kontodaten", Streamingverlauf letztes Jahr) | Pro gehörtem Song: Zeitpunkt, Artist, Titel, Hördauer (ms) | **Historische Daten** → Training |
| **Spotify Web API** (Premium) – "Recently Played" | Die letzten 50 gehörten Songs, **live** | **Aktuelle Daten** → Inferenz |

- Datenexport angefordert am: ❓ *(Datum eintragen)* – erwartet nach ca. 5 Tagen
- Fallback: die letzten Wochen des Exports abspalten und als "aktuelle" Daten verwenden (laut Aufgabenstellung erlaubt).

## 6. Target (was wird vorhergesagt?)

**Label `is_favorite` (ja / nein):**
Ein neuer Song gilt als Lieblingssong, wenn ich ihn in den **30 Tagen nach dem ersten Hören
mindestens 10 Mal** gehört habe.

- "Neuer Song" = Song, den ich im Verlauf zum ersten Mal höre.
- Ein Play zählt nur ab **30 Sekunden** Hördauer (sonst = geskippt).
- **Vorhersage-Zeitpunkt:** **5 Tage** nach dem ersten Hören.
- Die Grenze (5 oder 10 Plays) legen wir endgültig fest, wenn die Daten da sind: Es sollten ca.
  10–30 % der neuen Songs Lieblingssongs sein, sonst lernt das Modell schlecht.

→ Typ: **binäre Klassifikation**

## 7. Features (erster Entwurf)

| Feature | Art | Beschreibung |
|---|---|---|
| `plays_first_5d` | 📦 aggregiert | Anzahl Plays in den ersten 5 Tagen |
| `skip_rate_first_5d` | 📦 aggregiert | Anteil Plays unter 30 Sek. in den ersten 5 Tagen |
| `days_with_play_5d` | 📦 aggregiert | An wie vielen der ersten 5 Tage ich den Song gehört habe |
| `artist_plays_90d` | 📦 aggregiert | Wie oft ich den Artist in den 90 Tagen davor gehört habe ("kenne ich den Artist schon?") |
| `played_last_24h` | ⚡ RT | Wurde der Song in den letzten 24 h gehört? (erst bei Inferenz bekannt, via API) |
| `hour_of_last_play` | ⚡ RT | Uhrzeit des letzten Plays |

## 8. Modell

- Start: **Random Forest** (scikit-learn) – einfach & erklärbar ("welche Features waren wichtig?")
- Bewertung: Accuracy / F1 nur zur Info (Modellperformance wird **nicht** bewertet)
- Speicherung: lokal mit `joblib` → Upload in die **Hopsworks Model Registry**

## 9. Architektur (FTI)

```
 Spotify Export ─┐
                 ├─► 1️⃣ Feature-Pipeline ──► 🗄️ Hopsworks Featurestore (Feature Group)
 Spotify API ────┘                                   │
                                                     ▼
                                   2️⃣ Training-Pipeline ──► 📦 Hopsworks Model Registry
                                                     │                │
                                                     ▼                ▼
                             Spotify API (live) ─► 3️⃣ Inferenz-Pipeline ──► 🔥 Vorhersage + Playlist
```

- **Feature Group** `song_features`: Primary Key = `song_id` (Artist + Titel), Event Time = `first_played_at`

## 10. Projektstruktur

```
spotify/
├── data/
│   ├── raw/          🔒 Echter Spotify-Export (NICHT auf GitHub)
│   └── sample/       🧪 Erfundene Beispieldaten zum Testen
├── pipelines/
│   ├── 1_feature_pipeline.py
│   ├── 2_training_pipeline.py
│   └── 3_inference_pipeline.py
├── src/              🧰 Gemeinsame Hilfsfunktionen (Spotify-Login, Feature-Berechnung)
├── notebooks/        🔬 Zum Ausprobieren und Daten anschauen
├── models/           🤖 Lokal gespeicherte Modelle (NICHT auf GitHub)
├── docs/             🖼️ Bilder/Diagramme fürs README
├── .env.example      🔑 Vorlage für API-Keys (ohne echte Werte)
├── .gitignore
├── requirements.txt
├── KONZEPT.md        📝 Dieses Dokument
└── README.md         📘 Abgabe-Dokumentation
```

## 11. Zeitplan

| Woche | Zeitraum | Aufgabe | ✔ |
|---|---|---|---|
| 1 | 16.–25.10. | Konzept ✅, Setup (Python, Git, GitHub, Hopsworks, Spotify-App), Beispieldaten | ☐ |
| 2 | 26.10.–1.11. | Echte Daten erkunden, Feature-Pipeline | ☐ |
| 3 | 2.–8.11. | Training- & Inferenz-Pipeline | ☐ |
| 4 | 9.–15.11. | README, Limitationen, Puffer, (Playlist) – **Abgabe** | ☐ |

## 12. Risiken & Limitationen (fürs README)

- Der Export enthält **keine Skip-Info und keine Songlänge** → Skip wird über "< 30 Sek." geschätzt.
- Die API liefert nur die **letzten 50 Songs** → Lücke zwischen Export-Datum und heute.
- Songs werden über **Artist + Titel** identifiziert (keine Spotify-ID im einfachen Export).
- Spotify hat 2026 viele API-Endpoints gesperrt (Audio Features, Popularity) → nur Hörverhalten als Features.
- Songs der letzten 30 Tage im Export haben noch kein sicheres Label → nicht fürs Training verwendbar.
- Modell basiert nur auf **meinem** Hörverhalten → nicht direkt auf andere übertragbar.

## 13. Entscheidungen

| Frage | Entscheid |
|---|---|
| Titel | PreWrapped |
| Lieblingssong-Grenze | 10 Plays in 30 Tagen (wird mit echten Daten überprüft) |
| Vorhersage-Zeitpunkt | 5 Tage nach erstem Hören |
| Beispieldaten | Ja |
| Model Registry | Hopsworks |
| Persönlicher Ausbau | Playlist "Next Favorites" |
