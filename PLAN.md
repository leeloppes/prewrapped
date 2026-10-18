# Projektplan PreWrapped

> Ziel: **Bis 1.11. steht alles** → danach nur noch Feedback / zweite Meinung und Abgabe.
> Offizielle Abgabe: 15.11.2026 23:59 (Link zum GitHub Repo via Teams)

---

## 1. Ziele

**Muss (zum Bestehen):**
- [ ] Feature Pipeline läuft und speichert Features in Hopsworks
- [ ] Training Pipeline läuft und speichert das Modell in der Model Registry
- [ ] Inferenz Pipeline läuft und macht eine Vorhersage
- [ ] Mind. 1 aggregiertes Feature + 1 RT-Feature, beide werden bei der Inferenz verwendet
- [ ] README komplett (Daten, Features, Modell, Pipelines, Anleitung, Limitationen)
- [ ] `requirements.txt` + Python-Version angegeben

**Kann (nur wenn Zeit bleibt):**
- [ ] Playlist "Next Favorites" automatisch erstellen
- [ ] Web-App

## 2. Vorgaben aus der Aufgabenstellung (Checkliste)

| Vorgabe | Wo erfüllt? |
|---|---|
| Datenquelle, aufteilbar in historisch (Training) + aktuell (Inferenz) | Spotify Export + Spotify API |
| Target + passende Features | KONZEPT.md Kap. 6 + 7 |
| GitHub Repo | github.com/leeloppes/prewrapped |
| Hopsworks Account | erledigt |
| Dependencies, Python < 3.14 | Python 3.13, requirements.txt |
| Feature Pipeline: Daten holen → Features → Feature Group (Primary Key + Event Time) → einfügen | `pipelines/1_feature_pipeline.py` |
| Training Pipeline: Feature View → Training Dataset → Modell → Registry | `pipelines/2_training_pipeline.py` |
| Inferenz Pipeline: Live-Daten → neueste Features → Modell laden → Vorhersage | `pipelines/3_inference_pipeline.py` |
| README mit Features, Modell, Pipelines, Anleitung, Limitationen | `README.md` |

## 3. Vorgehen – der Trick

**Wir warten nicht auf die Spotify-Daten.**
Wir bauen zuerst alles mit **Beispieldaten** (erfundene Songs im gleichen Format wie der Spotify Export).
Wenn die echten Daten kommen, tauschen wir nur die Datei aus – der Code bleibt gleich.

Immer gleicher Ablauf pro Arbeitstag:
1. Kurz erklären lassen, was wir bauen
2. Code schreiben / ausführen
3. Verstehen (Kontrollfrage: "Was macht diese Zeile?")
4. `git commit` + `git push`
5. README-Abschnitt dazu kurz ergänzen

## 4. Zeitplan

| Datum | Zeit | Was | Ergebnis | |
|---|---|---|---|---|
| Fr 16.10. – Sa 17.10. | – | Idee, Konzept, Setup, GitHub | Repo online | erledigt |
| Sa 17.10. | – | Hopsworks + Spotify Verbindungstest | Beide Verbindungen klappen | erledigt |
| **So 18.10.** | 2–3 h | Beispieldaten erstellen · Daten anschauen (Notebook) · evtl. Feature Pipeline starten | Beispieldaten da | offen |
| **Di 20.10.** | 1–1.5 h | Feature Pipeline Teil 1: Daten einlesen, Features mit pandas berechnen | Tabelle mit Features + Label | offen |
| *21.–23.10.* | – | Spotify Export kommt (hoffentlich) | | offen |
| **Fr 23.10.** | 3–4 h | Feature Pipeline Teil 2: Feature Group in Hopsworks erstellen + Daten einfügen · Falls Export da: echte Daten anschauen | Features im Featurestore | offen |
| **Sa 24.10.** | 3–4 h | Echte Daten einbauen, Label-Grenze prüfen (5 oder 10 Plays) · Training Pipeline | Modell in der Model Registry | offen |
| **So 25.10.** | 1 h | Kurz reinschauen: alles committed? README Features + Modell ergänzen | | offen |
| **Di 27.10.** | 2–3 h | Inferenz Pipeline mit Live-Daten von der API | Vorhersage "XY % Lieblingssong" | offen |
| **So 1.11.** | 3 h | README fertig, Limitationen, alles einmal von vorne testen | **Version fertig** | offen |
| 2.–14.11. | Puffer | Zweite Meinung, Korrekturen, evtl. Playlist-Ausbau | | offen |
| **bis 15.11.** | – | Link via Teams abgeben (Ziel: schon ca. 8.11.) | Abgabe | offen |

**Total ca. 16–20 Stunden.**

## 5. Risiken & Plan B

| Risiko | Plan B |
|---|---|
| Spotify Export kommt erst nach dem 25.10. | Mit Beispieldaten weitermachen. Laut Aufgabenstellung sind künstlich generierte Daten erlaubt. Echte Daten später austauschen. |
| Spotify API macht Probleme (Fehler 403 o.ä.) | Letzte Wochen vom Export abspalten und als "aktuelle Daten" verwenden (erlaubt) |
| Hopsworks Installation / Verbindung klappt nicht | Am 18.10. als Erstes testen, damit genug Zeit bleibt |
| Ein Termin fällt aus | Puffer 2.–14.11. |
| Etwas läuft am Schluss nicht ganz | Im README ehrlich beschreiben – das ist erlaubt und zählt zur Bewertung |
