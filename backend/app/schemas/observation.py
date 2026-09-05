"""Observation schema representing extracted clinical measurements and lab test results."""

import datetime as dt
from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.provenance import Provenance


class Observation(BaseModel):
    """Clinical observation or laboratory result with reference range and provenance."""

    test_name: str = Field(
        description="Name of the test or clinical parameter",
    )
    value: Optional[float] = Field(
        default=None,
        description="Parsed numerical value of the result",
    )
    value_raw: Optional[str] = Field(
        default=None,
        description="Exact raw value as printed in the report (e.g. 'positive', '<0.01')",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Measurement unit (e.g. 'mg/dL', 'mmol/L')",
    )
    reference_range_low: Optional[float] = Field(
        default=None,
        description="Lower bound of reference range parsed from source document",
    )
    reference_range_high: Optional[float] = Field(
        default=None,
        description="Upper bound of reference range parsed from source document",
    )
    reference_range_raw: Optional[str] = Field(
        default=None,
        description="Reference range string exactly as printed in the source document",
    )
    flag: Optional[Literal["LOW", "NORMAL", "HIGH", "UNKNOWN"]] = Field(
        default=None,
        description="Deterministic reference-range flag: LOW, NORMAL, HIGH, or UNKNOWN",
    )
    date: Optional[dt.date] = Field(
        default=None,
        description="Date of specimen collection or test execution",
    )
    provenance: Provenance = Field(
        description="Provenance tracking origin, confidence, and human edits",
    )
