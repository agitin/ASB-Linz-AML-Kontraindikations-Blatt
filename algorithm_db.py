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
    gewichtsklasse_kommentar: str = ""
    dosierung: str = ""
    dosierung_kommentar: str = ""
    applikation: str = ""
    applikation_kommentar: str = ""


@dataclass
class ActiveSubstance:
    """Wirkstoff mit Spezialitäten, Kontraindikationen, Dosierungen und Wiederholungen"""
    name: str
    kommentar: str = ""
    handelsnamen: List[Specialty] = field(default_factory=list)
    kontraindikationen: List[PropertyWithComment] = field(default_factory=list)
    dosierungsgruppen: List[DosageGroup] = field(default_factory=list)
    wiederholungen: List[PropertyWithComment] = field(default_factory=list)


@dataclass
class PatientGroup:
    """Patient-Gruppe (Kinder oder Erwachsene) mit allen Informationen"""
    notarzt: str = ""
    notarzt_kommentar: str = ""
    kontraindikationen: List[PropertyWithComment] = field(default_factory=list)
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
        kontraindikationen = []
        for ci_key in ['kontraindikationen', 'contraindications']:
            if ci_key in group_data and group_data[ci_key]:
                for ci in group_data[ci_key]:
                    if isinstance(ci, dict):
                        text = ci.get('kontraindikation') or ci.get('contraindication') or ci.get('text', '')
                        kontraindikationen.append(PropertyWithComment(
                            text=text,
                            kommentar=ci.get('kommentar', '') or ci.get('comment', '')
                        ))
                    else:
                        kontraindikationen.append(PropertyWithComment(text=ci))
                break

        wirkstoffe = []
        for substance_key in ['wirkstoffe', 'active_substances']:
            if substance_key in group_data and group_data[substance_key]:
                for substance_data in group_data[substance_key]:

                    handelsnamen = []
                    for spec_list in [substance_data.get('handelsnamen', []), substance_data.get('specialties', [])]:
                        for spec in spec_list:
                            if isinstance(spec, dict):
                                name = spec.get('handelsname') or spec.get('specialty') or spec.get('name', '')
                                handelsnamen.append(Specialty(
                                    name=name,
                                    kommentar=spec.get('kommentar', '') or spec.get('comment', '')
                                ))
                            else:
                                handelsnamen.append(Specialty(name=spec))
                        if spec_list:
                            break

                    subst_kontraindikationen = []
                    for ci_list in [substance_data.get('kontraindikationen', []), substance_data.get('contraindications', [])]:
                        for ci in ci_list:
                            if isinstance(ci, dict):
                                text = ci.get('kontraindikation') or ci.get('contraindication') or ci.get('text', '')
                                subst_kontraindikationen.append(PropertyWithComment(
                                    text=text,
                                    kommentar=ci.get('kommentar', '') or ci.get('comment', '')
                                ))
                            else:
                                subst_kontraindikationen.append(PropertyWithComment(text=ci))
                        if ci_list:
                            break

                    dosierungsgruppen = []
                    for dg_list in [substance_data.get('dosierungsgruppen', []), substance_data.get('dosage_groups', [])]:
                        for dg in dg_list:
                            dosierungsgruppen.append(DosageGroup(
                                gewichtsklasse=dg.get('gewichtsklasse') or dg.get('weight_class', ''),
                                gewichtsklasse_kommentar=dg.get('gewichtsklasse_kommentar') or dg.get('gewichtsklasse_comment') or dg.get('weight_class_kommentar') or dg.get('weight_class_comment', ''),
                                dosierung=dg.get('dosierung') or dg.get('dosage', ''),
                                dosierung_kommentar=dg.get('dosierung_kommentar') or dg.get('dosierung_comment') or dg.get('dosage_kommentar') or dg.get('dosage_comment', ''),
                                applikation=dg.get('applikation') or dg.get('route', ''),
                                applikation_kommentar=dg.get('applikation_kommentar') or dg.get('applikation_comment') or dg.get('route_kommentar') or dg.get('route_comment', '')
                            ))
                        if dg_list:
                            break

                    wiederholungen = []
                    for rep_list in [substance_data.get('wiederholungen', []), substance_data.get('repetitions', [])]:
                        for rep in rep_list:
                            if isinstance(rep, dict):
                                text = rep.get('wiederholung') or rep.get('repetition') or rep.get('text', '')
                                wiederholungen.append(PropertyWithComment(
                                    text=text,
                                    kommentar=rep.get('kommentar', '') or rep.get('comment', '')
                                ))
                            else:
                                wiederholungen.append(PropertyWithComment(text=rep))
                        if rep_list:
                            break

                    wirkstoffe.append(ActiveSubstance(
                        name=substance_data.get('name', ''),
                        kommentar=substance_data.get('kommentar', '') or substance_data.get('comment', ''),
                        handelsnamen=handelsnamen,
                        kontraindikationen=subst_kontraindikationen,
                        dosierungsgruppen=dosierungsgruppen,
                        wiederholungen=wiederholungen
                    ))
                break

        return PatientGroup(
            notarzt=group_data.get('notarzt', '') or group_data.get('physician_contact', ''),
            notarzt_kommentar=group_data.get('notarzt_kommentar', '') or group_data.get('notarzt_comment', '') or group_data.get('physician_contact_kommentar', '') or group_data.get('physician_contact_comment', ''),
            kontraindikationen=kontraindikationen,
            wirkstoffe=wirkstoffe
        )

    def to_markdown(self) -> str:
        """Exportiert den Algorithmus als hierarchische Markdown mit Überschriften"""
        lines = []
        
        # Titel
        lines.append(f"# {self.algorithmus}\n")
        
        # Symptome (nicht in Tabelle)
        if self.symptome:
            lines.append("## Symptome\n")
            for symptom in self.symptome:
                if symptom.ganzer_text:
                    text = f"**Ganzer Text:** {symptom.ganzer_text}"
                    if symptom.kommentar:
                        text += f" *(Kommentar: {symptom.kommentar})*"
                    lines.append(text)
                if symptom.hervorgehoben:
                    text = f"\n **Hervorgehoben:** {symptom.hervorgehoben}"
                    if symptom.kommentar:
                        text += f" *(Kommentar: {symptom.kommentar})*"
                    lines.append(text)
                if symptom.gekuerzt:
                    text = f"\n **Gekürzt:** {symptom.gekuerzt}"
                    if symptom.kommentar:
                        text += f" *(Kommentar: {symptom.kommentar})*"
                    lines.append(text)
            lines.append("")
        
        # AML1
        if self.kinderanwendung or self.erwachsenenanwendung:
            lines.append("## AML1\n")
            
            # Kinderanwendung AML1
            if self.kinderanwendung and self.children:
                lines.append("### Kinderanwendung (AML1)\n")
                notarzt_text = f"**Notarzt:** {self.children.notarzt}"
                if self.children.notarzt_kommentar:
                    notarzt_text += f" *(Kommentar: {self.children.notarzt_kommentar})*"
                lines.append(notarzt_text)
                
                if self.children.kontraindikationen and any(ci.text for ci in self.children.kontraindikationen):
                    kontra_items = []
                    kontra_kommentar = ""
                    for ci in self.children.kontraindikationen:
                        if ci.text:
                            if isinstance(ci.text, list):
                                kontra_items.extend(ci.text)
                            else:
                                kontra_items.append(ci.text)
                            if ci.kommentar:
                                kontra_kommentar = ci.kommentar
                    if kontra_items:
                        kontra_str = ", ".join(kontra_items)
                        kontra_text = f"**Kontraindikationen:** {kontra_str}"
                        if kontra_kommentar:
                            kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                        lines.append(kontra_text)
                lines.append("")
                
                for wirkstoff in self.children.wirkstoffe:
                    lines.append(f"#### Wirkstoff: {wirkstoff.name}\n")
                    
                    if wirkstoff.handelsnamen:
                        for spec in wirkstoff.handelsnamen:
                            text = f"Handelsname: {spec.name}"
                            if spec.kommentar:
                                text += f" *(Kommentar: {spec.kommentar})*"
                            lines.append(text)
                        lines.append("")
                    
                    if wirkstoff.kontraindikationen and any(ci.text for ci in wirkstoff.kontraindikationen):
                        kontra_items = []
                        kontra_kommentar = ""
                        for ci in wirkstoff.kontraindikationen:
                            if isinstance(ci.text, list):
                                kontra_items.extend(ci.text)
                            elif ci.text:
                                kontra_items.append(ci.text)
                            if ci.kommentar:
                                kontra_kommentar = ci.kommentar
                        if kontra_items:
                            kontra_str = ", ".join(kontra_items)
                            kontra_text = f"Kontraindikationen: {kontra_str}"
                            if kontra_kommentar:
                                kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                            lines.append(kontra_text)
                            lines.append("")
                    
                    if wirkstoff.dosierungsgruppen:
                        lines.append("| Gewichts-/Altersklasse | Dosierung | Applikation | Kommentar |")
                        lines.append("| -------- | ------- | ------- | ------- |")
                        for dg in wirkstoff.dosierungsgruppen:
                            gewicht = dg.gewichtsklasse or "keine"
                            dosierung = dg.dosierung or ""
                            applikation = dg.applikation or ""
                            kommentar = dg.gewichtsklasse_kommentar or dg.dosierung_kommentar or dg.applikation_kommentar or ""
                            lines.append(f"| {gewicht} | {dosierung} | {applikation} | {kommentar} |")
                        lines.append("")
                    
                    if wirkstoff.wiederholungen:
                        for rep in wirkstoff.wiederholungen:
                            text = f"Wiederholung: {rep.text}"
                            if rep.kommentar:
                                text += f" *(Kommentar: {rep.kommentar})*"
                            lines.append(text)
                        lines.append("")
            
            # Erwachsenenanwendung AML1
            if self.erwachsenenanwendung and self.adults:
                lines.append("### Erwachsenenanwendung (AML1)\n")
                notarzt_text = f"**Notarzt:** {self.adults.notarzt}"
                if self.adults.notarzt_kommentar:
                    notarzt_text += f" *(Kommentar: {self.adults.notarzt_kommentar})*"
                lines.append(notarzt_text)
                
                if self.adults.kontraindikationen and any(ci.text for ci in self.adults.kontraindikationen):
                    kontra_items = []
                    kontra_kommentar = ""
                    for ci in self.adults.kontraindikationen:
                        if isinstance(ci.text, list):
                            kontra_items.extend(ci.text)
                        elif ci.text:
                            kontra_items.append(ci.text)
                        if ci.kommentar:
                            kontra_kommentar = ci.kommentar
                    if kontra_items:
                        kontra_str = ", ".join(kontra_items)
                        kontra_text = f"**Kontraindikationen:** {kontra_str}"
                        if kontra_kommentar:
                            kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                        lines.append(kontra_text)
                lines.append("")
                
                for wirkstoff in self.adults.wirkstoffe:
                    lines.append(f"#### Wirkstoff: {wirkstoff.name}\n")
                    
                    if wirkstoff.handelsnamen:
                        for spec in wirkstoff.handelsnamen:
                            text = f"Handelsname: {spec.name}"
                            if spec.kommentar:
                                text += f" *(Kommentar: {spec.kommentar})*"
                            lines.append(text)
                        lines.append("")
                    
                    if wirkstoff.kontraindikationen and any(ci.text for ci in wirkstoff.kontraindikationen):
                        kontra_items = []
                        kontra_kommentar = ""
                        for ci in wirkstoff.kontraindikationen:
                            if isinstance(ci.text, list):
                                kontra_items.extend(ci.text)
                            elif ci.text:
                                kontra_items.append(ci.text)
                            if ci.kommentar:
                                kontra_kommentar = ci.kommentar
                        if kontra_items:
                            kontra_str = ", ".join(kontra_items)
                            kontra_text = f"Kontraindikationen: {kontra_str}"
                            if kontra_kommentar:
                                kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                            lines.append(kontra_text)
                            lines.append("")
                    
                    if wirkstoff.dosierungsgruppen:
                        lines.append("| Gewichts-/Altersklasse | Dosierung | Applikation | Kommentar |")
                        lines.append("| -------- | ------- | ------- | ------- |")
                        for dg in wirkstoff.dosierungsgruppen:
                            gewicht = dg.gewichtsklasse or "keine"
                            dosierung = dg.dosierung or ""
                            applikation = dg.applikation or ""
                            kommentar = dg.gewichtsklasse_kommentar or dg.dosierung_kommentar or dg.applikation_kommentar or ""
                            lines.append(f"| {gewicht} | {dosierung} | {applikation} | {kommentar} |")
                        lines.append("")
                    
                    if wirkstoff.wiederholungen:
                        for rep in wirkstoff.wiederholungen:
                            text = f"Wiederholung: {rep.text}"
                            if rep.kommentar:
                                text += f" *(Kommentar: {rep.kommentar})*"
                            lines.append(text)
                            lines.append("")
        
        # AML2
        if self.kinderanwendung_aml2 or self.erwachsenenanwendung_aml2:
            lines.append("## AML2\n")
            
            # Kinderanwendung AML2
            if self.kinderanwendung_aml2 and self.children_aml2:
                lines.append("### Kinderanwendung (AML2)\n")
                notarzt_text = f"**Notarzt:** {self.children_aml2.notarzt}"
                if self.children_aml2.notarzt_kommentar:
                    notarzt_text += f" *(Kommentar: {self.children_aml2.notarzt_kommentar})*"
                lines.append(notarzt_text)
                
                if self.children_aml2.kontraindikationen and any(ci.text for ci in self.children_aml2.kontraindikationen):
                    kontra_items = []
                    kontra_kommentar = ""
                    for ci in self.children_aml2.kontraindikationen:
                        if ci.text:
                            if isinstance(ci.text, list):
                                kontra_items.extend(ci.text)
                            else:
                                kontra_items.append(ci.text)
                            if ci.kommentar:
                                kontra_kommentar = ci.kommentar
                    if kontra_items:
                        kontra_str = ", ".join(kontra_items)
                        kontra_text = f"**Kontraindikationen:** {kontra_str}"
                        if kontra_kommentar:
                            kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                        lines.append(kontra_text)
                lines.append("")
                
                for wirkstoff in self.children_aml2.wirkstoffe:
                    lines.append(f"#### Wirkstoff: {wirkstoff.name}\n")
                    
                    if wirkstoff.handelsnamen:
                        for spec in wirkstoff.handelsnamen:
                            text = f"Handelsname: {spec.name}"
                            if spec.kommentar:
                                text += f" *(Kommentar: {spec.kommentar})*"
                            lines.append(text)
                        lines.append("")
                    
                    if wirkstoff.kontraindikationen and any(ci.text for ci in wirkstoff.kontraindikationen):
                        kontra_items = []
                        kontra_kommentar = ""
                        for ci in wirkstoff.kontraindikationen:
                            if isinstance(ci.text, list):
                                kontra_items.extend(ci.text)
                            elif ci.text:
                                kontra_items.append(ci.text)
                            if ci.kommentar:
                                kontra_kommentar = ci.kommentar
                        if kontra_items:
                            kontra_str = ", ".join(kontra_items)
                            kontra_text = f"Kontraindikationen: {kontra_str}"
                            if kontra_kommentar:
                                kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                            lines.append(kontra_text)
                            lines.append("")
                    
                    if wirkstoff.dosierungsgruppen:
                        lines.append("| Gewichts-/Altersklasse | Dosierung | Applikation | Kommentar |")
                        lines.append("| -------- | ------- | ------- | ------- |")
                        for dg in wirkstoff.dosierungsgruppen:
                            gewicht = dg.gewichtsklasse or "keine"
                            dosierung = dg.dosierung or ""
                            applikation = dg.applikation or ""
                            kommentar = dg.gewichtsklasse_kommentar or dg.dosierung_kommentar or dg.applikation_kommentar or ""
                            lines.append(f"| {gewicht} | {dosierung} | {applikation} | {kommentar} |")
                        lines.append("")
                    
                    if wirkstoff.wiederholungen:
                        for rep in wirkstoff.wiederholungen:
                            text = f"Wiederholung: {rep.text}"
                            if rep.kommentar:
                                text += f" *(Kommentar: {rep.kommentar})*"
                            lines.append(text)
                        lines.append("")
            
            # Erwachsenenanwendung AML2
            if self.erwachsenenanwendung_aml2 and self.adults_aml2:
                lines.append("### Erwachsenenanwendung (AML2)\n")
                notarzt_text = f"**Notarzt:** {self.adults_aml2.notarzt}"
                if self.adults_aml2.notarzt_kommentar:
                    notarzt_text += f" *(Kommentar: {self.adults_aml2.notarzt_kommentar})*"
                lines.append(notarzt_text)
                
                if self.adults_aml2.kontraindikationen and any(ci.text for ci in self.adults_aml2.kontraindikationen):
                    kontra_items = []
                    kontra_kommentar = ""
                    for ci in self.adults_aml2.kontraindikationen:
                        if isinstance(ci.text, list):
                            kontra_items.extend(ci.text)
                        elif ci.text:
                            kontra_items.append(ci.text)
                        if ci.kommentar:
                            kontra_kommentar = ci.kommentar
                    if kontra_items:
                        kontra_str = ", ".join(kontra_items)
                        kontra_text = f"**Kontraindikationen:** {kontra_str}"
                        if kontra_kommentar:
                            kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                        lines.append(kontra_text)
                lines.append("")
                
                for wirkstoff in self.adults_aml2.wirkstoffe:
                    lines.append(f"#### Wirkstoff: {wirkstoff.name}\n")
                    
                    if wirkstoff.handelsnamen:
                        for spec in wirkstoff.handelsnamen:
                            text = f"Handelsname: {spec.name}"
                            if spec.kommentar:
                                text += f" *(Kommentar: {spec.kommentar})*"
                            lines.append(text)
                        lines.append("")
                    
                    if wirkstoff.kontraindikationen and any(ci.text for ci in wirkstoff.kontraindikationen):
                        kontra_items = []
                        kontra_kommentar = ""
                        for ci in wirkstoff.kontraindikationen:
                            if isinstance(ci.text, list):
                                kontra_items.extend(ci.text)
                            elif ci.text:
                                kontra_items.append(ci.text)
                            if ci.kommentar:
                                kontra_kommentar = ci.kommentar
                        if kontra_items:
                            kontra_str = ", ".join(kontra_items)
                            kontra_text = f"Kontraindikationen: {kontra_str}"
                            if kontra_kommentar:
                                kontra_text += f" *(Kommentar: {kontra_kommentar})*"
                            lines.append(kontra_text)
                            lines.append("")
                    
                    if wirkstoff.dosierungsgruppen:
                        lines.append("| Gewichts-/Altersklasse | Dosierung | Applikation | Kommentar |")
                        lines.append("| -------- | ------- | ------- | ------- |")
                        for dg in wirkstoff.dosierungsgruppen:
                            gewicht = dg.gewichtsklasse or "keine"
                            dosierung = dg.dosierung or ""
                            applikation = dg.applikation or ""
                            kommentar = dg.gewichtsklasse_kommentar or dg.dosierung_kommentar or dg.applikation_kommentar or ""
                            lines.append(f"| {gewicht} | {dosierung} | {applikation} | {kommentar} |")
                        lines.append("")
                    
                    if wirkstoff.wiederholungen:
                        for rep in wirkstoff.wiederholungen:
                            text = f"Wiederholung: {rep.text}"
                            if rep.kommentar:
                                text += f" *(Kommentar: {rep.kommentar})*"
                            lines.append(text)
                        lines.append("")
        
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
