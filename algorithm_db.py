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
    kommentar: str = ""


@dataclass
class SymptomProperty:
    """Ein Symptom mit voller, hervorgehobener und verkürzter Version sowie Kommentar"""
    ganzer_text: str
    hervorgehoben: str = ""
    gekuerzt: str = ""
    kommentar: str = ""


@dataclass
class Specialty:
    """Handelsnamen/Handelsname eines Wirkstoffs"""
    name: str
    kommentar: str = ""


@dataclass
class DosageGroup:
    """Dosierungsgruppe mit Gewichts-/Altersklasse und Dosierung"""
    gewichtsklasse: str = ""
    dosierung: str = ""
    applikation: str = ""


@dataclass
class ActiveSubstance:
    """Wirkstoff mit Handelsname, Kontraindikationen und Dosierungen"""
    name: str
    handelsname: str = ""
    kontraindikationen: List[str] = field(default_factory=list)
    dosierungsgruppen: List[DosageGroup] = field(default_factory=list)


@dataclass
class PatientGroup:
    """Patient-Gruppe (Kinder oder Erwachsene) mit allen Informationen"""
    kommentar: str = ""
    notarzt: str = ""
    notarzt_kommentar: str = ""
    kontraindikationen: List[str] = field(default_factory=list)
    wirkstoffe: List[ActiveSubstance] = field(default_factory=list)


@dataclass
class Algorithm:
    """Ein Algorithmus für ein bestimmtes Medikament/Indikation"""
    algorithmus: str
    kommentar: str = ""
    symptome: List[SymptomProperty] = field(default_factory=list)
    kinderanwendung: bool = False
    erwachsenenanwendung: bool = False
    kinderanwendung_aml2: bool = False
    erwachsenenanwendung_aml2: bool = False
    children: Optional[PatientGroup] = None
    adults: Optional[PatientGroup] = None
    children_aml2: Optional[PatientGroup] = None
    adults_aml2: Optional[PatientGroup] = None

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'Algorithm':
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        symptome = []
        if 'symptome' in data and data['symptome']:
            for symptom in data['symptome']:
                if isinstance(symptom, dict):
                    ganzer_text = symptom.get('ganzer_text') or symptom.get('symptom') or symptom.get('text', '')
                    hervorgehoben = symptom.get('hervorgehoben') or symptom.get('symptom_hervorgehoben', '')
                    gekuerzt = symptom.get('gekuerzt') or symptom.get('symptom_gekuerzt', '')
                    symptome.append(SymptomProperty(
                        ganzer_text=ganzer_text,
                        hervorgehoben=hervorgehoben,
                        gekuerzt=gekuerzt,
                        kommentar=symptom.get('kommentar', '') or symptom.get('comment', '')
                    ))
                else:
                    symptome.append(SymptomProperty(ganzer_text=symptom))

        children = None
        if 'kinder_aml1' in data and data['kinder_aml1']:
            children = cls._parse_patient_group(data['kinder_aml1'])
        elif 'kinder' in data and data['kinder']:
            children = cls._parse_patient_group(data['kinder'])
        elif 'children' in data and data['children']:
            children = cls._parse_patient_group(data['children'])

        adults = None
        if 'erwachsene_aml1' in data and data['erwachsene_aml1']:
            adults = cls._parse_patient_group(data['erwachsene_aml1'])
        elif 'erwachsene' in data and data['erwachsene']:
            adults = cls._parse_patient_group(data['erwachsene'])
        elif 'adults' in data and data['adults']:
            adults = cls._parse_patient_group(data['adults'])

        children_aml2 = None
        if 'kinder_aml2' in data and data['kinder_aml2']:
            children_aml2 = cls._parse_patient_group(data['kinder_aml2'])

        adults_aml2 = None
        if 'erwachsene_aml2' in data and data['erwachsene_aml2']:
            adults_aml2 = cls._parse_patient_group(data['erwachsene_aml2'])

        return cls(
            algorithmus=data.get('algorithmus', ''),
            kommentar=data.get('kommentar', '') or data.get('comment', ''),
            symptome=symptome,
            kinderanwendung=data.get('kinderanwendung_aml1', data.get('kinderanwendung', data.get('apply_children', False))),
            erwachsenenanwendung=data.get('erwachsenenanwendung_aml1', data.get('erwachsenenanwendung', data.get('apply_adults', False))),
            kinderanwendung_aml2=data.get('kinderanwendung_aml2', False),
            erwachsenenanwendung_aml2=data.get('erwachsenenanwendung_aml2', False),
            children=children,
            adults=adults,
            children_aml2=children_aml2,
            adults_aml2=adults_aml2
        )

    @staticmethod
    def _parse_patient_group(group_data: dict) -> PatientGroup:
        # Parse Kontraindikationen (einfache String-Liste)
        kontraindikationen = []
        for ci_key in ['kontraindikationen', 'contraindications']:
            if ci_key in group_data and group_data[ci_key]:
                kontraindikationen = group_data[ci_key]
                break

        # Parse Wirkstoffe
        wirkstoffe = []
        for substance_key in ['wirkstoffe', 'active_substances']:
            if substance_key in group_data and group_data[substance_key]:
                for substance_data in group_data[substance_key]:
                    # Handelsname (einzelner String oder Liste)
                    handelsname = ""
                    if substance_data.get('handelsname'):
                        handelsname = substance_data.get('handelsname')
                    elif substance_data.get('handelsnamen'):
                        handelsnamen_list = substance_data.get('handelsnamen', [])
                        if handelsnamen_list and isinstance(handelsnamen_list[0], dict):
                            handelsname = handelsnamen_list[0].get('handelsname', '')
                        elif handelsnamen_list:
                            handelsname = handelsnamen_list[0]

                    # Kontraindikationen des Wirkstoffs (String-Liste)
                    subst_kontraindikationen = []
                    for ci_list in [substance_data.get('kontraindikationen', []), substance_data.get('contraindications', [])]:
                        if ci_list:
                            if isinstance(ci_list[0], dict) and 'kontraindikation' in ci_list[0]:
                                for ci in ci_list:
                                    text = ci.get('kontraindikation')
                                    if isinstance(text, list):
                                        subst_kontraindikationen.extend(text)
                                    else:
                                        subst_kontraindikationen.append(text)
                            else:
                                subst_kontraindikationen = ci_list
                            break

                    # Parse Dosierungsgruppen
                    dosierungsgruppen = []
                    for dg_list in [substance_data.get('dosierungsgruppen', []), substance_data.get('dosage_groups', [])]:
                        for dg in dg_list:
                            dosierungsgruppen.append(DosageGroup(
                                gewichtsklasse=dg.get('gewichtsklasse') or dg.get('weight_class', ''),
                                dosierung=dg.get('dosierung') or dg.get('dosage', ''),
                                applikation=dg.get('applikation') or dg.get('route', '')
                            ))
                        if dg_list:
                            break

                    wirkstoffe.append(ActiveSubstance(
                        name=substance_data.get('name', ''),
                        handelsname=handelsname,
                        kontraindikationen=subst_kontraindikationen,
                        dosierungsgruppen=dosierungsgruppen
                    ))
                break

        return PatientGroup(
            kommentar=group_data.get('kommentar', ''),
            notarzt=group_data.get('notarzt', '') or group_data.get('physician_contact', ''),
            notarzt_kommentar=group_data.get('notarzt_kommentar', '') or group_data.get('notarzt_comment', '') or group_data.get('physician_contact_kommentar', '') or group_data.get('physician_contact_comment', ''),
            kontraindikationen=kontraindikationen,
            wirkstoffe=wirkstoffe
        )

    def to_markdown(self) -> str:
        """Exportiert den Algorithmus als Markdown"""
        lines = []
        
        # Titel
        lines.append(f"# {self.algorithmus}\n")
        
        # Symptome
        if self.symptome:
            lines.append("## Symptome\n")
            for symptom in self.symptome:
                if symptom.ganzer_text:
                    lines.append(f"{symptom.ganzer_text}")
            lines.append("")
        
        # Helper-Funktion für Patient-Gruppen
        def render_patient_group(group, title):
            if not group:
                return
            
            lines.append(f"### {title}\n")
            
            # Notarzt
            if group.notarzt:
                notarzt_text = f"**Notarzt:** {group.notarzt}"
                if group.notarzt_kommentar:
                    notarzt_text += f" *(Kommentar: {group.notarzt_kommentar})*"
                lines.append(notarzt_text)
            
            # Block-Kommentar
            if group.kommentar:
                lines.append(f"*(Kommentar: {group.kommentar})*")
            
            # Kontraindikationen (Block-Ebene)
            if group.kontraindikationen:
                kontra_str = ", ".join(filter(None, group.kontraindikationen))
                if kontra_str and kontra_str != "":
                    lines.append(f"**Kontraindikationen:** {kontra_str}")
            
            lines.append("")
            
            # Wirkstoffe
            for i, wirkstoff in enumerate(group.wirkstoffe, 1):
                # Wirkstoff und Handelsname auf einer Zeile
                wirkstoff_text = f"**{i}. {wirkstoff.name}**"
                if wirkstoff.handelsname:
                    wirkstoff_text += f", Handelsname: {wirkstoff.handelsname}"
                lines.append(wirkstoff_text)
                lines.append("")
                
                # Kontraindikationen des Wirkstoffs
                if wirkstoff.kontraindikationen:
                    kontra_str = ", ".join(filter(None, wirkstoff.kontraindikationen))
                    if kontra_str:
                        lines.append(f"Kontraindikationen: {kontra_str}")
                        lines.append("")
                
                # Dosierungsgruppen (Tabelle ohne Kommentarspalte)
                if wirkstoff.dosierungsgruppen:
                    lines.append("| Gewichts-/Altersklasse | Dosierung | Applikation |")
                    lines.append("| -------- | ------- | ------- |")
                    for dg in wirkstoff.dosierungsgruppen:
                        gewicht = dg.gewichtsklasse or "keine"
                        dosierung = dg.dosierung or ""
                        applikation = dg.applikation or ""
                        lines.append(f"| {gewicht} | {dosierung} | {applikation} |")
                    lines.append("")
        
        # AML1
        if self.kinderanwendung or self.erwachsenenanwendung:
            lines.append("## AML1\n")
            if self.kinderanwendung and self.children:
                render_patient_group(self.children, "Kinderanwendung (AML1)")
            if self.erwachsenenanwendung and self.adults:
                render_patient_group(self.adults, "Erwachsenenanwendung (AML1)")
        
        # AML2
        if self.kinderanwendung_aml2 or self.erwachsenenanwendung_aml2:
            lines.append("## AML2\n")
            if self.kinderanwendung_aml2 and self.children_aml2:
                render_patient_group(self.children_aml2, "Kinderanwendung (AML2)")
            if self.erwachsenenanwendung_aml2 and self.adults_aml2:
                render_patient_group(self.adults_aml2, "Erwachsenenanwendung (AML2)")
        
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Export-Verzeichnis anlegen
    export_dir = Path("export")
    export_dir.mkdir(exist_ok=True)

    # Alle YAML-Dateien im aktuellen Verzeichnis finden
    yaml_files = list(Path(".").glob("*.yaml"))

    if not yaml_files:
        print("Keine .yaml-Dateien gefunden.")
    else:
        for yaml_file in yaml_files:
            try:
                # Algorithmus laden
                algorithm = Algorithm.from_yaml(yaml_file)

                # Markdown erzeugen
                markdown = algorithm.to_markdown()

                # Zieldatei erstellen
                output_file = export_dir / f"{yaml_file.stem}.md"
                output_file.write_text(markdown, encoding="utf-8")

                print(f"✓ Exportiert: {yaml_file.name} -> {output_file}")
            except Exception as e:
                print(f"✗ Fehler bei {yaml_file.name}: {e}")
