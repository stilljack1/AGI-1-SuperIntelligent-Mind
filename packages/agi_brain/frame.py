from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class TaskFrame(BaseModel):
    intent: str = Field(min_length=1)
    actor: str = Field(default="jack")
    user_message: str = Field(min_length=1)
    priority: str = Field(default="normal")
    mode: str = Field(default="staging")
    language: str = Field(default="en")
    constraints: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    tools_needed: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    permissions_required: List[str] = Field(default_factory=list)


def build_frame(
    *,
    user_message: str,
    actor: str,
    priority: str,
    mode: str,
    language: str = "en",
) -> TaskFrame:
    clean_message = user_message.strip()
    risks: list[str] = []
    permissions: list[str] = []
    lowered = clean_message.lower()
    if any(token in lowered for token in ("call", "meeting", "phone")):
        permissions.append("communications")
        risks.append("external_communication")
    if any(token in lowered for token in ("pay", "wire", "bank", "transfer")):
        permissions.append("payments")
        risks.append("financial_action")
    if any(token in lowered for token in ("delete", "wipe", "drop table", "reset")):
        permissions.append("destructive")
        risks.append("destructive_action")

    return TaskFrame(
        intent=clean_message,
        actor=actor,
        user_message=clean_message,
        priority=priority,
        mode=mode,
        language=language,
        constraints=[
            "must_be_truthful",
            "must_preserve_safety",
            "must_avoid_unverified_claims",
        ],
        risks=risks,
        tools_needed=["task_runtime", "adapter_registry"],
        success_criteria=[
            "response_is_consistent",
            "response_is_actionable",
            "response_declares_uncertainty_when_needed",
        ],
        permissions_required=permissions,
    )

