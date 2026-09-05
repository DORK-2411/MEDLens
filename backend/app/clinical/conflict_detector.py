"""Pure deterministic conflict detector comparing patient intake assertions with extracted records.

Principle: LLMs extract. Code decides.
No LLM, DB, API, or network.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Set

from app.schemas.conflict import Conflict

# Standard negation / non-presence terms in patient intake
NEGATION_TERMS = {
    "none",
    "nil",
    "n/a",
    "na",
    "no",
    "no known",
    "no known allergies",
    "no known allergy",
    "no known drug allergies",
    "no known drug allergy",
    "nkda",
    "no allergies",
    "no allergy",
    "no known conditions",
    "no conditions",
    "no medical conditions",
    "no known medical history",
    "no medications",
    "no current medications",
    "none reported",
    "denies",
    "denies all",
    "denies allergies",
    "denies medications",
    "negative",
    "none known",
    "not applicable",
}

FIELDS_TO_CHECK = ["allergies", "conditions", "medications"]


def normalize_string(text: Optional[str]) -> str:
    """Normalize whitespace and lowercase a string safely."""
    if text is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(text).strip())
    return cleaned.lower()


def is_negation_or_empty(text: Optional[str]) -> bool:
    """Check if the text represents an explicit denial, negation, or empty statement."""
    normalized = normalize_string(text)
    if not normalized or normalized in NEGATION_TERMS:
        return True
    return any(normalized.startswith(term + " ") for term in ["no", "denies", "none"])


def _extract_items(value: Any) -> List[str]:
    """Safely extract list of non-empty item strings from string, list, or dict structures."""
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return []
        # Split on commas or newlines if it's a comma-separated list of items
        if "," in cleaned and not is_negation_or_empty(cleaned):
            return [part.strip() for part in cleaned.split(",") if part.strip()]
        return [cleaned]
    if isinstance(value, (list, set, tuple)):
        items: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str) and item.strip():
                items.append(item.strip())
            elif isinstance(item, dict):
                # E.g. {"name": "Penicillin"}
                name = item.get("name") or item.get("item") or item.get("value")
                if name and isinstance(name, str) and name.strip():
                    items.append(name.strip())
        return items
    if isinstance(value, dict):
        return _extract_items(value.get("items") or value.get("values") or list(value.values()))
    return [str(value).strip()]


def detect_conflicts(
    patient_reported: Optional[Dict[str, Any]],
    extracted_history: Optional[Dict[str, Any]],
) -> List[Conflict]:
    """Deterministically detect conflicts between patient self-reports and extracted clinical documents.

    Identifies discrepancies such as:
    - Patient states 'no known allergies' / 'none' / empty, but extracted history documents an allergy.
    - Patient denies conditions/medications, but prior records document them.
    - Contradictions between patient reported assertions and documented history.

    Args:
        patient_reported: Dictionary of patient intake data (e.g. allergies, conditions, medications).
        extracted_history: Dictionary of extracted clinical document findings.

    Returns:
        List of Conflict models with details, source document ID, and detection timestamp.
    """
    if not patient_reported or not isinstance(patient_reported, dict):
        patient_reported = {}
    if not extracted_history or not isinstance(extracted_history, dict):
        extracted_history = {}

    # Determine source document ID
    doc_id = (
        extracted_history.get("source_document_id")
        or extracted_history.get("document_id")
        or "unknown_document"
    )

    conflicts: List[Conflict] = []
    seen_conflict_keys: Set[tuple] = set()
    now = datetime.now(timezone.utc)

    for field in FIELDS_TO_CHECK:
        patient_val = patient_reported.get(field)
        # Also check singular key fallback (e.g. "allergy")
        if patient_val is None and field.endswith("s"):
            patient_val = patient_reported.get(field[:-1])

        extracted_val = extracted_history.get(field)
        if extracted_val is None and field.endswith("s"):
            extracted_val = extracted_history.get(field[:-1])

        p_items = _extract_items(patient_val)
        e_items = _extract_items(extracted_val)

        # Case 1: Patient reports negation or empty, but extracted history has positive items
        patient_claims_none = (
            len(p_items) == 0
            or all(is_negation_or_empty(item) for item in p_items)
        )

        extracted_has_positive = [
            item for item in e_items if not is_negation_or_empty(item)
        ]

        if patient_claims_none and extracted_has_positive:
            reported_desc = (
                p_items[0] if p_items and p_items[0].strip() else f"No {field} reported"
            )
            for ext_item in extracted_has_positive:
                norm_key = (field, normalize_string(reported_desc), normalize_string(ext_item), doc_id)
                if norm_key not in seen_conflict_keys:
                    seen_conflict_keys.add(norm_key)
                    conflicts.append(
                        Conflict(
                            field=field,
                            patient_reported_value=reported_desc,
                            extracted_value=ext_item,
                            source_document_id=doc_id,
                            detected_at=now,
                        )
                    )
            continue

        # Case 2: Extracted report states negation/none, but patient explicitly reported positive items
        extracted_claims_none = (
            len(e_items) > 0 and all(is_negation_or_empty(item) for item in e_items)
        )
        patient_has_positive = [
            item for item in p_items if not is_negation_or_empty(item)
        ]

        if extracted_claims_none and patient_has_positive:
            ext_desc = e_items[0] if e_items else f"No {field} in report"
            for p_item in patient_has_positive:
                norm_key = (field, normalize_string(p_item), normalize_string(ext_desc), doc_id)
                if norm_key not in seen_conflict_keys:
                    seen_conflict_keys.add(norm_key)
                    conflicts.append(
                        Conflict(
                            field=field,
                            patient_reported_value=p_item,
                            extracted_value=ext_desc,
                            source_document_id=doc_id,
                            detected_at=now,
                        )
                    )

    return conflicts
