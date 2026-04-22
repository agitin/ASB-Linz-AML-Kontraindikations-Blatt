# AML-Datenbank - Dokumentation

Eine Python-basierte Datenbank für Algorithmen zur Arzneimittelgabe durch Notfallsanitäter mit Git-freundlichem YAML-Format.

## Struktur

### Dateien
- **`*.yaml`** - Einzelne Algorithmus-Dateien (z.B. `anaphylaxis.yaml`)
- **`algorithm_db.py`** - Python-Datenbank und Export-Funktionen
- **`export/`** - Generierte Markdown-Dateien (wird bei Export erstellt)

## YAML-Format

Jeder Algorithmus hat folgende Struktur:

```yaml
name: Name des Algorithmus
indication: Indikation
symptoms:
  - Symptom 1
  - Symptom 2

children:
  contraindications:
    - Kontraindikation 1
  active_substances:
    - name: Wirkstoff-Name
      specialty: Optional (z.B. Autoinjektor)
      dosage_groups:
        - weight_class: "Gewichtsklasse / Altersklasse"
          dosage: "Dosierung"
          route: "Applikationsroute (i.m., i.v., etc.)"
        - weight_class: "..."
          dosage: "..."
          route: "..."
  repetition: Wiederholungsmöglichkeiten

adults:
  # Gleiche Struktur wie children
```

## Python-Verwendung

### Basis-Beispiele

```python
from pathlib import Path
from algorithm_db import AlgorithmDatabase

# Initialisiere Datenbank
db = AlgorithmDatabase(Path(__file__).parent)

# Liste alle Algorithmen auf
print(db.list_algorithms())
# Output: ['anaphylaxis', 'myocardial_infarction', ...]

# Hole einen Algorithmus
algo = db.get_algorithm('anaphylaxis')
print(algo.name)
print(algo.indication)

# Gib einen Algorithmus als Markdown aus
db.print_algorithm('anaphylaxis')

# Exportiere einen Algorithmus als Markdown-String
markdown = db.export_algorithm_to_markdown('anaphylaxis')
```

### Alle Algorithmen exportieren

```python
# Exportiert alle Algorithmen als .md-Dateien ins 'export/'-Verzeichnis
db.export_all_to_markdown()

# Oder in ein custom Verzeichnis
db.export_all_to_markdown(Path('my_export_folder'))
```

## Workflow mit Git

1. **Neue Algorithmen hinzufügen:**
   - Neue `.yaml`-Datei im Verzeichnis erstellen
   - Datenbank lädt sie automatisch

2. **Änderungen tracken:**
   ```bash
   git add *.yaml
   git commit -m "Update Anaphylaxis-Dosierung"
   ```

3. **Markdown-Tabellen generieren:**
   ```bash
   python algorithm_db.py
   ```

## Erweiterbarkeit

Für zukünftige Features (z.B. neue Felder pro Algorithmus):

1. **Neue Felder in YAML hinzufügen** (z.B. `special_notes`, `last_updated`)
2. **Entsprechende Eigenschaften in Python-Klassen hinzufügen**
3. **`to_markdown()`-Methode anpassen** zum Exportieren

Die Struktur ist vollständig erweiterbar ohne bestehende Daten zu brechen!

## Abhängigkeiten

```bash
pip install pyyaml
```
