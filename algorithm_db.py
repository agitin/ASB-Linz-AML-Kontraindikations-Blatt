"""
AML-Datenbank: Algorithmen für Arzneimittel bei Notfallsanitätern
Struktur-Klassen und Datenbankfunktionen
"""

from dataclasses import dataclass, field
from typing import List, Optional
import yaml
from pathlib import Path


@dataclass
class PropertyWithComment:
    """Eine Eigenschaft mit optionalem Kommentar"""
    text: str
    comment: str = ""


@dataclass
class SymptomProperty:
    """Ein Symptom mit voller, hervorgehobener und verkürzter Version sowie Kommentar"""
    full_text: str
    highlighted: str = ""
    shortened: str = ""
    comment: str = ""


@dataclass
class Specialty:
    """Handelsnamen/Handelsname eines Wirkstoffs"""
    name: str
    comment: str = ""


@dataclass
class DosageGroup:
    """Dosierungsgruppe mit Gewichts-/Altersklasse und Dosierung"""
    weight_class: str = ""
    weight_class_comment: str = ""
    dosage: str = ""
    dosage_comment: str = ""
    route: str = ""
    route_comment: str = ""


@dataclass
class ActiveSubstance:
    """Wirkstoff mit Spezialitäten, Kontraindikationen, Dosierungen und Wiederholungen"""
    name: str
    comment: str = ""
    specialties: List[Specialty] = field(default_factory=list)
    contraindications: List[PropertyWithComment] = field(default_factory=list)
    dosage_groups: List[DosageGroup] = field(default_factory=list)
    repetitions: List[PropertyWithComment] = field(default_factory=list)


@dataclass
class PatientGroup:
    """Patient-Gruppe (Kinder oder Erwachsene) mit allen Informationen"""
    notarzt: str = ""
    notarzt_comment: str = ""
    contraindications: List[PropertyWithComment] = field(default_factory=list)
    active_substances: List[ActiveSubstance] = field(default_factory=list)


@dataclass
class Algorithm:
    """Ein Algorithmus für ein bestimmtes Medikament/Indikation"""
    title: str
    comment: str = ""
    symptoms: List[SymptomProperty] = field(default_factory=list)
    apply_children: bool = False
    apply_adults: bool = False
    children: Optional[PatientGroup] = None
    adults: Optional[PatientGroup] = None
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'Algorithm':
        """Lädt einen Algorithmus aus einer YAML-Datei"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parse symptoms
        symptoms = []
        if 'symptoms' in data and data['symptoms']:
            for symptom in data['symptoms']:
                if isinstance(symptom, dict):
                    # Versuche neue Keys, fallback auf alte Keys
                    full_text = symptom.get('full_text') or symptom.get('symptom') or symptom.get('text', '')
                    highlighted = symptom.get('highlighted') or symptom.get('symptom_highlighted', '')
                    shortened = symptom.get('shortened') or symptom.get('symptom_shortened', '')
                    symptoms.append(SymptomProperty(
                        full_text=full_text,
                        highlighted=highlighted,
                        shortened=shortened,
                        comment=symptom.get('comment', '')
                    ))
                else:
                    symptoms.append(SymptomProperty(full_text=symptom, comment=''))
        
        # Parse symptoms_highlighted (für Rückwärtskompatibilität)
        if 'symptoms_highlighted' in data and data['symptoms_highlighted']:
            for symptom in data['symptoms_highlighted']:
                if isinstance(symptom, dict):
                    full_text = symptom.get('symptom_highlighted') or symptom.get('text', '')
                    shortened = symptom.get('symptom_highlighted_shortened', '')
                    symptoms.append(SymptomProperty(
                        full_text=full_text,
                        highlighted=full_text,
                        shortened=shortened,
                        comment=symptom.get('comment', '')
                    ))
                else:
                    symptoms.append(SymptomProperty(full_text=symptom, highlighted=symptom, comment=''))
        
        # Parse children
        children = None
        if 'kinder' in data and data['kinder']:
            children = cls._parse_patient_group(data['kinder'])
        elif 'children' in data and data['children']:
            children = cls._parse_patient_group(data['children'])
        
        # Parse adults
        adults = None
        if 'erwachsene' in data and data['erwachsene']:
            adults = cls._parse_patient_group(data['erwachsene'])
        elif 'adults' in data and data['adults']:
            adults = cls._parse_patient_group(data['adults'])
        
        return cls(
            title=data.get('title', ''),
            comment=data.get('comment', ''),
            symptoms=symptoms,
            apply_children=data.get('kinderanwendung', data.get('apply_children', False)),
            apply_adults=data.get('erwachsenenanwendung', data.get('apply_adults', False)),
            children=children,
            adults=adults
        )
    
    @staticmethod
    def _parse_patient_group(group_data: dict) -> PatientGroup:
        """Parser für eine PatientGroup aus YAML"""
        # Parse contraindications
        contraindications = []
        for ci_key in ['kontraindikationen', 'contraindications']:
            if ci_key in group_data and group_data[ci_key]:
                for ci in group_data[ci_key]:
                    if isinstance(ci, dict):
                        # Versuche deutsch oder english
                        text = ci.get('kontraindikation') or ci.get('contraindication') or ci.get('text', '')
                        contraindications.append(PropertyWithComment(
                            text=text,
                            comment=ci.get('comment', '')
                        ))
                    else:
                        contraindications.append(PropertyWithComment(text=ci, comment=''))
                break
        
        # Parse active substances
        active_substances = []
        for substance_key in ['wirkstoffe', 'active_substances']:
            if substance_key in group_data and group_data[substance_key]:
                for substance_data in group_data[substance_key]:
                # Parse handelsnamen
                handelsnamen = []
                for spec_list in [substance_data.get('handelsnamen', []), substance_data.get('specialties', [])]:
                    for spec in spec_list:
                        if isinstance(spec, dict):
                            # Versuche 'handelsname' oder 'specialty' oder fallback 'name'
                            name = spec.get('handelsname') or spec.get('specialty') or spec.get('name', '')
                            handelsnamen.append(Specialty(
                                name=name,
                                comment=spec.get('comment', '')
                            ))
                        else:
                            handelsnamen.append(Specialty(name=spec, comment=''))
                    if spec_list:
                        break
                
                # Parse substance contraindications
                subst_contraindications = []
                for ci_list in [substance_data.get('kontraindikationen', []), substance_data.get('contraindications', [])]:
                    for ci in ci_list:
                        if isinstance(ci, dict):
                            # Versuche 'kontraindikation' oder 'contraindication' oder fallback 'text'
                            text = ci.get('kontraindikation') or ci.get('contraindication') or ci.get('text', '')
                            subst_contraindications.append(PropertyWithComment(
                                text=text,
                                comment=ci.get('comment', '')
                            ))
                        else:
                            subst_contraindications.append(PropertyWithComment(text=ci, comment=''))
                    if ci_list:
                        break
                
                # Parse dosage groups
                dosage_groups = []
                for dg_list in [substance_data.get('dosierungsgruppen', []), substance_data.get('dosage_groups', [])]:
                    for dg in dg_list:
                        dosage_groups.append(DosageGroup(
                            weight_class=dg.get('gewichtsklasse') or dg.get('weight_class', ''),
                            weight_class_comment=dg.get('gewichtsklasse_comment') or dg.get('weight_class_comment', ''),
                            dosage=dg.get('dosierung') or dg.get('dosage', ''),
                            dosage_comment=dg.get('dosierung_comment') or dg.get('dosage_comment', ''),
                            route=dg.get('applikation') or dg.get('route', ''),
                            route_comment=dg.get('applikation_comment') or dg.get('route_comment', '')
                        ))
                    if dg_list:
                        break
                
                # Parse repetitions
                repetitions = []
                for rep_list in [substance_data.get('wiederholungen', []), substance_data.get('repetitions', [])]:
                    for rep in rep_list:
                        if isinstance(rep, dict):
                            # Versuche 'wiederholung' oder 'repetition' oder fallback 'text'
                            text = rep.get('wiederholung') or rep.get('repetition') or rep.get('text', '')
                            repetitions.append(PropertyWithComment(
                                text=text,
                                comment=rep.get('comment', '')
                            ))
                        else:
                            repetitions.append(PropertyWithComment(text=rep, comment=''))
                    if rep_list:
                        break
                
                active_substances.append(ActiveSubstance(
                    name=substance_data.get('name', ''),
                    comment=substance_data.get('comment', ''),
                    specialties=specialties,
                    contraindications=subst_contraindications,
                    dosage_groups=dosage_groups,
                    repetitions=repetitions
                ))
        
        return PatientGroup(
            notarzt=group_data.get('notarzt', '') or group_data.get('physician_contact', ''),
            notarzt_comment=group_data.get('notarzt_comment', '') or group_data.get('physician_contact_comment', ''),
            contraindications=contraindications,
            active_substances=active_substances
        )
    
    def to_markdown(self) -> str:
        """Exportiert den Algorithmus als Markdown mit linearem Format"""
        lines = []
        lines.append(f"# {self.title}")
        if self.comment:
            lines.append(f"_Kommentar: {self.comment}_\n")
        else:
            lines.append("")
        
        # Symptoms
        if self.symptoms:
            lines.append("## Symptome")
            for symptom in self.symptoms:
                lines.append(self._format_property(symptom.full_text, symptom.comment))
                if symptom.highlighted:
                    lines.append(self._format_property(f"  → Hervorgehoben: {symptom.highlighted}", ""))
                if symptom.shortened:
                    lines.append(self._format_property(f"  → Kurzform: {symptom.shortened}", ""))
            lines.append("")
        
        # Kinder
        if self.apply_children and self.children:
            lines.append("## Kinderanwendung")
            lines.extend(self._patient_group_to_markdown(self.children))
        
        # Erwachsene
        if self.apply_adults and self.adults:
            lines.append("## Erwachsenenanwendung")
            lines.extend(self._patient_group_to_markdown(self.adults))
        
        return "\n".join(lines)
    
    def _format_property(self, text: str, comment: str = "") -> str:
        """Formatiert eine Eigenschaft mit optionalem Kommentar rechts"""
        if comment:
            return f"- {text:<60} _{comment}_"
        else:
            return f"- {text}"
    
    def _patient_group_to_markdown(self, group: PatientGroup) -> List[str]:
        """Konvertiert eine PatientGroup zu Markdown-Zeilen"""
        lines = []
        
        # Notarzt contact
        if group.notarzt:
            lines.append(self._format_property(
                f"Notarzt: {group.notarzt}",
                group.notarzt_comment
            ))
        
        # Contraindications
        if group.contraindications and any(c.text for c in group.contraindications):
            lines.append("\n**Kontraindikationen:**")
            for ci in group.contraindications:
                if ci.text:
                    lines.append(self._format_property(ci.text, ci.comment))
        
        # Active substances
        for substance in group.active_substances:
            lines.append(f"\n**Wirkstoff:** {substance.name}")
            if substance.comment:
                lines.append(f"_{substance.comment}_")
            
            # Specialties
            if substance.specialties:
                lines.append("\n**Handelsnamen:**")
                for spec in substance.specialties:
                    lines.append(self._format_property(spec.name, spec.comment))
            
            # Substance-specific contraindications
            if substance.contraindications and any(c.text for c in substance.contraindications):
                lines.append("\n**Kontraindikationen (spezifisch):**")
                for ci in substance.contraindications:
                    if ci.text:
                        lines.append(self._format_property(ci.text, ci.comment))
            
            # Dosage groups
            if substance.dosage_groups:
                lines.append("\n**Dosierungen:**")
                for dg in substance.dosage_groups:
                    lines.append(self._format_property(
                        f"Gewichts-/Altersklasse: {dg.weight_class}",
                        dg.weight_class_comment
                    ))
                    lines.append(self._format_property(
                        f"  → Dosierung: {dg.dosage}",
                        dg.dosage_comment
                    ))
                    lines.append(self._format_property(
                        f"  → Applikation: {dg.route}",
                        dg.route_comment
                    ))
            
            # Repetitions
            if substance.repetitions:
                lines.append("\n**Wiederholungen:**")
                for rep in substance.repetitions:
                    lines.append(self._format_property(rep.text, rep.comment))
        
        lines.append("")
        return lines


class AlgorithmDatabase:
    """Datenbank für alle Algorithmen"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.algorithms: dict[str, Algorithm] = {}
        self._load_all_algorithms()
    
    def _load_all_algorithms(self):
        """Lädt alle YAML-Dateien aus dem Datenverzeichnis"""
        for yaml_file in self.data_dir.glob("*.yaml"):
            try:
                algo = Algorithm.from_yaml(yaml_file)
                self.algorithms[yaml_file.stem] = algo
            except Exception as e:
                print(f"Fehler beim Laden von {yaml_file}: {e}")
    
    def get_algorithm(self, key: str) -> Optional[Algorithm]:
        """Gibt einen Algorithmus nach Schlüssel aus"""
        return self.algorithms.get(key)
    
    def list_algorithms(self) -> List[str]:
        """Gibt Liste aller Algorithmus-Schlüssel aus"""
        return list(self.algorithms.keys())
    
    def export_algorithm_to_markdown(self, key: str) -> Optional[str]:
        """Exportiert einen Algorithmus als Markdown"""
        algo = self.get_algorithm(key)
        if algo:
            return algo.to_markdown()
        return None
    
    def export_all_to_markdown(self, output_dir: Optional[Path] = None) -> None:
        """Exportiert alle Algorithmen als Markdown-Dateien"""
        if output_dir is None:
            output_dir = self.data_dir / "export"
        
        output_dir.mkdir(exist_ok=True)
        
        for key, algo in self.algorithms.items():
            output_file = output_dir / f"{key}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(algo.to_markdown())
            print(f"✓ Exportiert: {output_file}")
    
    def print_algorithm(self, key: str) -> None:
        """Gibt einen Algorithmus formatiert in der Konsole aus"""
        markdown = self.export_algorithm_to_markdown(key)
        if markdown:
            print(markdown)
        else:
            print(f"Algorithmus '{key}' nicht gefunden.")


# Beispiel: Verwendung
if __name__ == "__main__":
    # Initialisiere die Datenbank (übergib den Pfad zum Verzeichnis mit den YAML-Dateien)
    db = AlgorithmDatabase(Path(__file__).parent)
    
    # Liste alle Algorithmen auf
    print("Verfügbare Algorithmen:")
    for algo_key in db.list_algorithms():
        print(f"  - {algo_key}")
    
    print("\n" + "="*60 + "\n")
    
    # Exportiere einen Algorithmus
    db.print_algorithm("anaphylaxis")
    
    print("\n" + "="*60 + "\n")
    
    # Exportiere alle Algorithmen als Markdown-Dateien
    print("Exportiere alle Algorithmen...")
    db.export_all_to_markdown()

