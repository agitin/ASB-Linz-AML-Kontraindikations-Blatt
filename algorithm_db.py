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
    ganzer_text: str
    hervorgehoben: str = ""
    gekuerzt: str = ""
    comment: str = ""


@dataclass
class Specialty:
    """Handelsnamen/Handelsname eines Wirkstoffs"""
    name: str
    comment: str = ""


@dataclass
class DosageGroup:
    """Dosierungsgruppe mit Gewichts-/Altersklasse und Dosierung"""
    gewichtsklasse: str = ""
    gewichtsklasse_comment: str = ""
    dosierung: str = ""
    dosierung_comment: str = ""
    applikation: str = ""
    applikation_comment: str = ""


@dataclass
class ActiveSubstance:
    """Wirkstoff mit Spezialitäten, Kontraindikationen, Dosierungen und Wiederholungen"""
    name: str
    comment: str = ""
    handelsnamen: List[Specialty] = field(default_factory=list)
    kontraindikationen: List[PropertyWithComment] = field(default_factory=list)
    dosierungsgruppen: List[DosageGroup] = field(default_factory=list)
    wiederholungen: List[PropertyWithComment] = field(default_factory=list)


@dataclass
class PatientGroup:
    """Patient-Gruppe (Kinder oder Erwachsene) mit allen Informationen"""
    notarzt: str = ""
    notarzt_comment: str = ""
    kontraindikationen: List[PropertyWithComment] = field(default_factory=list)
    wirkstoffe: List[ActiveSubstance] = field(default_factory=list)


@dataclass
class Algorithm:
    """Ein Algorithmus für ein bestimmtes Medikament/Indikation"""
    algorithmus: str
    comment: str = ""
    symptoms: List[SymptomProperty] = field(default_factory=list)
    kinderanwendung: bool = False
    erwachsenenanwendung: bool = False
    children: Optional[PatientGroup] = None
    adults: Optional[PatientGroup] = None

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'Algorithm':
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        symptoms = []
        if 'symptoms' in data and data['symptoms']:
            for symptom in data['symptoms']:
                if isinstance(symptom, dict):
                    ganzer_text = symptom.get('ganzer_text') or symptom.get('symptom') or symptom.get('text', '')
                    hervorgehoben = symptom.get('hervorgehoben') or symptom.get('symptom_hervorgehoben', '')
                    gekuerzt = symptom.get('gekuerzt') or symptom.get('symptom_gekuerzt', '')
                    symptoms.append(SymptomProperty(
                        ganzer_text=ganzer_text,
                        hervorgehoben=hervorgehoben,
                        gekuerzt=gekuerzt,
                        comment=symptom.get('comment', '')
                    ))
                else:
                    symptoms.append(SymptomProperty(ganzer_text=symptom))

        children = None
        if 'kinder' in data and data['kinder']:
            children = cls._parse_patient_group(data['kinder'])
        elif 'children' in data and data['children']:
            children = cls._parse_patient_group(data['children'])

        adults = None
        if 'erwachsene' in data and data['erwachsene']:
            adults = cls._parse_patient_group(data['erwachsene'])
        elif 'adults' in data and data['adults']:
            adults = cls._parse_patient_group(data['adults'])

        return cls(
            algorithmus=data.get('algorithmus', ''),
            comment=data.get('comment', ''),
            symptoms=symptoms,
            kinderanwendung=data.get('kinderanwendung', data.get('apply_children', False)),
            erwachsenenanwendung=data.get('erwachsenenanwendung', data.get('apply_adults', False)),
            children=children,
            adults=adults
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
                            comment=ci.get('comment', '')
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
                                    comment=spec.get('comment', '')
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
                                    comment=ci.get('comment', '')
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
                                gewichtsklasse_comment=dg.get('gewichtsklasse_comment') or dg.get('weight_class_comment', ''),
                                dosierung=dg.get('dosierung') or dg.get('dosage', ''),
                                dosierung_comment=dg.get('dosierung_comment') or dg.get('dosage_comment', ''),
                                applikation=dg.get('applikation') or dg.get('route', ''),
                                applikation_comment=dg.get('applikation_comment') or dg.get('route_comment', '')
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
                                    comment=rep.get('comment', '')
                                ))
                            else:
                                wiederholungen.append(PropertyWithComment(text=rep))
                        if rep_list:
                            break

                    wirkstoffe.append(ActiveSubstance(
                        name=substance_data.get('name', ''),
                        comment=substance_data.get('comment', ''),
                        handelsnamen=handelsnamen,
                        kontraindikationen=subst_kontraindikationen,
                        dosierungsgruppen=dosierungsgruppen,
                        wiederholungen=wiederholungen
                    ))
                break

        return PatientGroup(
            notarzt=group_data.get('notarzt', '') or group_data.get('physician_contact', ''),
            notarzt_comment=group_data.get('notarzt_comment', '') or group_data.get('physician_contact_comment', ''),
            kontraindikationen=kontraindikationen,
            wirkstoffe=wirkstoffe
        )