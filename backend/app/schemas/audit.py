"""Audit log schema for tracking human verification and field edits."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    """Represents an audit entry recorded whenever human edits or verifications occur."""

    entry_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the audit log entry",
    )
    action: str = Field(
        description="Action performed (e.g., 'edit', 'verify', 'override')",
    )
    entity_type: str = Field(
        description="Type of entity modified (e.g., 'observation', 'patient_record', 'report')",
    )
    entity_id: str = Field(
        description="Identifier of the specific entity modified",
    )
    field_name: Optional[str] = Field(
        default=None,
        description="Name of the field modified, if field-level edit",
    )
    old_value: Optional[str] = Field(
        default=None,
        description="Previous value before modification",
    )
    new_value: Optional[str] = Field(
        default=None,
        description="Updated value after modification",
    )
    edited_by: str = Field(
        description="Identifier or username of the reviewer who made the edit",
    )
    timestamp: datetime = Field(
        description="Timestamp when the edit occurred",
    )
