from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = (
    REPO_ROOT
    / "Data Sources for Hackathon"
    / "hackathon-data"
    / "track-1-clinical-ai"
    / "synthea-patients"
)

COMPLAINT_ALIASES = {
    "abdominal pain": ["abdominal pain", "stomach pain", "belly pain", "abd pain"],
    "anxiety/depression": ["anxiety", "depression", "panic attack", "low mood"],
    "back pain": ["back pain", "lower back pain", "upper back pain"],
    "chest pain": ["chest pain", "chest pressure", "tight chest"],
    "cough and cold symptoms": [
        "cough",
        "cold",
        "sore throat",
        "runny nose",
        "congestion",
    ],
    "dizziness": ["dizziness", "dizzy", "vertigo", "lightheaded"],
    "fever": ["fever", "febrile", "high temperature"],
    "headache": ["headache", "migraine", "head pain"],
    "injury from fall": ["fall", "fell", "slip and fall", "injury from fall"],
    "joint pain": ["joint pain", "knee pain", "hip pain", "shoulder pain"],
    "nausea and vomiting": ["nausea", "vomiting", "throwing up", "emesis"],
    "shortness of breath": [
        "shortness of breath",
        "sob",
        "breathless",
        "difficulty breathing",
    ],
    "skin rash": ["rash", "skin rash", "hives", "itchy skin"],
    "urinary symptoms": ["urinary", "burning urination", "dysuria", "frequency", "uti"],
    "wound/laceration": ["laceration", "wound", "cut", "bleeding cut"],
}

LAB_ALIASES = {
    "Troponin I": ["troponin", "troponin i"],
    "Glucose, Fasting": ["glucose", "fasting glucose", "blood sugar"],
    "Hemoglobin": ["hemoglobin", "haemoglobin", "hgb"],
    "HbA1c": ["hba1c", "a1c"],
    "Total Cholesterol": ["total cholesterol", "cholesterol"],
    "ALT": ["alt", "alanine aminotransferase"],
    "Sodium": ["sodium", "na"],
    "TSH": ["tsh", "thyroid stimulating hormone"],
    "White Blood Cell Count": ["white blood cell count", "wbc", "white count"],
    "Potassium": ["potassium", "k"],
    "Creatinine": ["creatinine", "cr"],
    "LDL Cholesterol": ["ldl", "ldl cholesterol"],
}


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\s/.\-]", " ", value.lower()).strip()


def _contains_alias(text: str, alias: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _extract_number_after_alias(text: str, alias: str) -> float | None:
    pattern = re.compile(
        r"(?<![a-z0-9])"
        + re.escape(alias)
        + r"(?![a-z0-9])"
        + r"[^0-9\-]{0,20}(-?\d+(?:\.\d+)?)"
    )
    match = pattern.search(text)
    if match:
        return float(match.group(1))
    return None


@dataclass
class TriageArtifacts:
    classifier: RandomForestClassifier
    complaint_to_code: dict[str, int]
    common_labs: list[str]
    common_meds: list[str]
    lab_medians: dict[str, float]
    complaint_triage_mode: dict[str, int]


def _load_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing dataset file: {path}. "
            "Expected the hackathon data under "
            "'Data Sources for Hackathon/hackathon-data/track-1-clinical-ai/synthea-patients'."
        )
    return pd.read_csv(path, parse_dates=parse_dates)


def _build_training_frame() -> tuple[pd.DataFrame, list[str], list[str]]:
    encounters = _load_csv("encounters.csv", parse_dates=["encounter_date"])
    labs = _load_csv("lab_results.csv")
    medications = _load_csv("medications.csv", parse_dates=["start_date"])
    medications["end_date"] = pd.to_datetime(medications["end_date"], errors="coerce")

    common_labs = labs["test_name"].value_counts().head(12).index.tolist()
    common_meds = medications["drug_name"].value_counts().head(20).index.tolist()

    lab_wide = (
        labs[labs["test_name"].isin(common_labs)]
        .pivot_table(
            index="encounter_id", columns="test_name", values="value", aggfunc="mean"
        )
        .rename(columns=lambda col: f"lab__{col}")
    )

    active_medications = medications[medications["active"]].copy()
    encounter_meds = encounters[["encounter_id", "patient_id", "encounter_date"]].merge(
        active_medications[["patient_id", "drug_name", "start_date", "end_date"]],
        on="patient_id",
        how="left",
    )
    active_mask = (
        encounter_meds["drug_name"].notna()
        & (encounter_meds["start_date"] <= encounter_meds["encounter_date"])
        & (
            encounter_meds["end_date"].isna()
            | (encounter_meds["end_date"] >= encounter_meds["encounter_date"])
        )
    )
    encounter_meds = encounter_meds[active_mask]
    med_wide = (
        pd.crosstab(encounter_meds["encounter_id"], encounter_meds["drug_name"])
        .reindex(columns=common_meds, fill_value=0)
        .rename(columns=lambda col: f"med__{col}")
    )

    training = encounters[["encounter_id", "chief_complaint", "triage_level"]].copy()
    training = training.join(lab_wide, on="encounter_id")
    training = training.join(med_wide, on="encounter_id")

    for lab in common_labs:
        column = f"lab__{lab}"
        training[column] = training[column].fillna(training[column].median())
    for med in common_meds:
        column = f"med__{med}"
        if column not in training:
            training[column] = 0
        training[column] = training[column].fillna(0).astype(int)

    return training, common_labs, common_meds


@lru_cache(maxsize=1)
def get_triage_artifacts() -> TriageArtifacts:
    training, common_labs, common_meds = _build_training_frame()

    complaint_categories = sorted(
        training["chief_complaint"].dropna().unique().tolist()
    )
    complaint_to_code = {
        complaint: idx for idx, complaint in enumerate(complaint_categories)
    }
    training["complaint_encoded"] = training["chief_complaint"].map(complaint_to_code)

    feature_columns = (
        ["complaint_encoded"]
        + [f"lab__{lab}" for lab in common_labs]
        + [f"med__{med}" for med in common_meds]
    )

    classifier = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced_subsample",
    )
    classifier.fit(training[feature_columns], training["triage_level"])

    complaint_triage_mode = (
        training.groupby("chief_complaint")["triage_level"]
        .agg(lambda values: int(values.mode().iloc[0]))
        .to_dict()
    )
    lab_medians = {lab: float(training[f"lab__{lab}"].median()) for lab in common_labs}

    return TriageArtifacts(
        classifier=classifier,
        complaint_to_code=complaint_to_code,
        common_labs=common_labs,
        common_meds=common_meds,
        lab_medians=lab_medians,
        complaint_triage_mode=complaint_triage_mode,
    )


def infer_chief_complaint(query: str) -> tuple[str, float]:
    normalized = _normalize_text(query)
    best_complaint = "headache"
    best_score = -1.0

    for complaint, aliases in COMPLAINT_ALIASES.items():
        score = 0.0
        for alias in aliases:
            normalized_alias = _normalize_text(alias)
            if _contains_alias(normalized, normalized_alias):
                score = max(score, 1.0 + (len(normalized_alias.split()) * 0.1))
        if score > best_score:
            best_score = score
            best_complaint = complaint

    if best_score < 0:
        artifacts = get_triage_artifacts()
        complaint_words = {
            complaint: set(_normalize_text(complaint).split())
            for complaint in artifacts.complaint_to_code
        }
        query_words = set(normalized.split())
        for complaint, words in complaint_words.items():
            overlap = len(query_words & words) / max(len(words), 1)
            if overlap > best_score:
                best_score = overlap
                best_complaint = complaint

    confidence = max(0.15, min(0.99, 0.45 + best_score / 2))
    return best_complaint, round(confidence, 2)


def extract_labs(query: str, supported_labs: list[str]) -> dict[str, float]:
    normalized = _normalize_text(query)
    extracted: dict[str, float] = {}
    for lab in supported_labs:
        aliases = LAB_ALIASES.get(lab, [lab])
        for alias in aliases:
            value = _extract_number_after_alias(normalized, _normalize_text(alias))
            if value is not None:
                extracted[lab] = value
                break
    return extracted


def extract_medications(query: str, supported_medications: list[str]) -> list[str]:
    normalized = _normalize_text(query)
    extracted = []
    for medication in supported_medications:
        if _contains_alias(normalized, _normalize_text(medication)):
            extracted.append(medication)
    return extracted


def predict_triage(
    query: str,
    labs: dict[str, float] | None = None,
    medications: list[str] | None = None,
) -> dict[str, Any]:
    artifacts = get_triage_artifacts()
    chief_complaint, complaint_confidence = infer_chief_complaint(query)

    parsed_labs = extract_labs(query, artifacts.common_labs)
    if labs:
        parsed_labs.update({name: float(value) for name, value in labs.items()})

    parsed_medications = set(extract_medications(query, artifacts.common_meds))
    if medications:
        parsed_medications.update(medications)

    feature_row: dict[str, float | int] = {
        "complaint_encoded": artifacts.complaint_to_code[chief_complaint],
    }
    for lab in artifacts.common_labs:
        feature_row[f"lab__{lab}"] = parsed_labs.get(lab, artifacts.lab_medians[lab])
    for medication in artifacts.common_meds:
        feature_row[f"med__{medication}"] = int(medication in parsed_medications)

    features = pd.DataFrame([feature_row])
    probabilities = artifacts.classifier.predict_proba(features)[0]
    classes = [int(value) for value in artifacts.classifier.classes_]
    top_index = int(probabilities.argmax())
    predicted_triage = classes[top_index]

    sorted_probabilities = sorted(
        (
            {"triage_level": triage_level, "probability": round(float(probability), 4)}
            for triage_level, probability in zip(classes, probabilities)
        ),
        key=lambda item: item["probability"],
        reverse=True,
    )

    return {
        "chief_complaint": chief_complaint,
        "chief_complaint_confidence": complaint_confidence,
        "predicted_triage_level": predicted_triage,
        "chief_complaint_baseline_triage": artifacts.complaint_triage_mode[
            chief_complaint
        ],
        "extracted_labs": dict(sorted(parsed_labs.items())),
        "extracted_medications": sorted(parsed_medications),
        "probabilities": sorted_probabilities,
        "supported_labs": artifacts.common_labs,
        "supported_medications": artifacts.common_meds,
    }
