#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$(pwd)}"
FACTORY_DIR="${ROOT_DIR}/agi1_factory"

mkdir -p \
  "${FACTORY_DIR}/core" \
  "${FACTORY_DIR}/departments" \
  "${FACTORY_DIR}/specialists" \
  "${FACTORY_DIR}/harness" \
  "${FACTORY_DIR}/intelligence_laws"

cat <<'PY' > "${FACTORY_DIR}/__init__.py"
"""AGI-1 Autonomous Factory package."""

__all__ = [
    "core",
    "departments",
    "specialists",
    "harness",
    "intelligence_laws",
]
PY

cat <<'PY' > "${FACTORY_DIR}/core/__init__.py"
"""Core orchestration primitives for AGI-1 Autonomous Factory."""

from .consensus import ConsensusResult, ExecutiveConsensus
from .message_bus import AsyncMessageBus
from .mission_planner import AGIGPSMissionPlanner
from .models import AgentProfile, AgentTier, ExecutionLayer, InstantiationPlan, MissionRequest
from .resource_governor import BurnRateGovernor
from .role_instantiation import RoleInstantiationEngine

__all__ = [
    "AgentProfile",
    "AgentTier",
    "AsyncMessageBus",
    "BurnRateGovernor",
    "ConsensusResult",
    "ExecutionLayer",
    "ExecutiveConsensus",
    "InstantiationPlan",
    "MissionRequest",
    "RoleInstantiationEngine",
    "AGIGPSMissionPlanner",
]
PY

cat <<'PY' > "${FACTORY_DIR}/core/models.py"
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class AgentTier(str, Enum):
    EXECUTIVE = "executive"
    LEADERSHIP = "leadership"
    CORE = "core"
    SPECIALIST = "specialist"


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    display_name: str
    title: str
    department: str
    tier: AgentTier
    skills: List[str] = field(default_factory=list)
    max_parallel_tasks: int = 1


@dataclass(frozen=True)
class MissionRequest:
    mission_id: str
    objective: str
    domains: List[str]
    risk_level: str
    budget_tokens: int
    budget_usd: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionLayer:
    layer: int
    name: str
    owner: str
    status: str = "PLANNED"
    detail: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class InstantiationPlan:
    executives: List[AgentProfile] = field(default_factory=list)
    leadership: List[AgentProfile] = field(default_factory=list)
    core_team: List[AgentProfile] = field(default_factory=list)
    specialists: List[AgentProfile] = field(default_factory=list)
    variety_score: float = 0.0
    rationale: str = ""
PY

cat <<'PY' > "${FACTORY_DIR}/core/consensus.py"
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ConsensusResult:
    approved: bool
    approvals: int
    rejections: int
    rationale: str


class ExecutiveConsensus:
    """3/4 executive consensus for corporate directives."""

    EXECUTIVES = ("jack", "julia", "singularity", "aegis")
    REQUIRED_APPROVALS = 3

    def evaluate(self, votes: Dict[str, bool], rationales: Dict[str, str] | None = None) -> ConsensusResult:
        rationales = rationales or {}
        missing = [name for name in self.EXECUTIVES if name not in votes]
        if missing:
            return ConsensusResult(
                approved=False,
                approvals=0,
                rejections=0,
                rationale=f"Missing executive votes: {', '.join(sorted(missing))}",
            )

        approvals = sum(1 for key in self.EXECUTIVES if bool(votes[key]))
        rejections = len(self.EXECUTIVES) - approvals
        approved = approvals >= self.REQUIRED_APPROVALS

        if approved:
            rationale = "Consensus approved by executive board."
        else:
            rejection_reasons = [f"{name}:{rationales.get(name, 'reject')}" for name in self.EXECUTIVES if not votes[name]]
            rationale = "Consensus denied. " + " | ".join(rejection_reasons)

        return ConsensusResult(
            approved=approved,
            approvals=approvals,
            rejections=rejections,
            rationale=rationale,
        )
PY

cat <<'PY' > "${FACTORY_DIR}/core/message_bus.py"
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List

MessageHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass(frozen=True)
class BusMessage:
    topic: str
    payload: Dict[str, Any]


class AsyncMessageBus:
    """Simple async departmental message bus for request/response exchanges."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[MessageHandler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: MessageHandler) -> None:
        self._handlers[topic].append(handler)

    async def publish(self, topic: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        handlers = self._handlers.get(topic, [])
        if not handlers:
            return []
        return await asyncio.gather(*(handler(payload) for handler in handlers))

    async def request(self, topic: str, payload: Dict[str, Any], timeout_seconds: float = 5.0) -> Dict[str, Any]:
        handlers = self._handlers.get(topic, [])
        if not handlers:
            return {"status": "no_handler", "topic": topic, "payload": payload}

        task = asyncio.create_task(handlers[0](payload))
        try:
            return await asyncio.wait_for(task, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            task.cancel()
            return {"status": "timeout", "topic": topic}
PY

cat <<'PY' > "${FACTORY_DIR}/core/mission_planner.py"
from __future__ import annotations

from typing import List

from agi1_factory.core.models import ExecutionLayer, MissionRequest


class AGIGPSMissionPlanner:
    """Builds the 6-layer deterministic mission flow (AGI GPS)."""

    def build_layers(self, mission: MissionRequest) -> List[ExecutionLayer]:
        return [
            ExecutionLayer(
                layer=1,
                name="Intent",
                owner="Julia",
                detail=f"Align mission with long-horizon company vision: {mission.objective}",
            ),
            ExecutionLayer(
                layer=2,
                name="Logic",
                owner="Senior Engineer",
                detail="Map mission into an executable, dependency-aware DAG.",
            ),
            ExecutionLayer(
                layer=3,
                name="Swarm",
                owner="Jack",
                detail="Instantiate executive, leadership, core, and specialist workforce.",
            ),
            ExecutionLayer(
                layer=4,
                name="Execution",
                owner="Autonomous Harness",
                detail="Execute parallel workstreams with rollback checkpoints.",
            ),
            ExecutionLayer(
                layer=5,
                name="Synthesis",
                owner="Business Intelligence",
                detail="Merge outputs into a single source of truth.",
            ),
            ExecutionLayer(
                layer=6,
                name="Correction",
                owner="Aegis + Executives",
                detail="Run deterministic audit before completion and release.",
            ),
        ]
PY

cat <<'PY' > "${FACTORY_DIR}/core/resource_governor.py"
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BurnRateSnapshot:
    tokens_used: int
    token_budget: int
    usd_spent: float
    usd_budget: float
    utilization_tokens: float
    utilization_usd: float
    status: str


class BurnRateGovernor:
    """Tracks token/compute spend to enforce Landauer-inspired efficiency discipline."""

    def __init__(self, token_budget: int, usd_budget: float) -> None:
        self.token_budget = max(1, token_budget)
        self.usd_budget = max(0.01, usd_budget)
        self.tokens_used = 0
        self.usd_spent = 0.0

    def consume(self, *, tokens: int, usd_cost: float) -> None:
        self.tokens_used += max(0, int(tokens))
        self.usd_spent += max(0.0, float(usd_cost))

    def snapshot(self) -> BurnRateSnapshot:
        token_util = min(2.0, self.tokens_used / self.token_budget)
        usd_util = min(2.0, self.usd_spent / self.usd_budget)

        status = "GREEN"
        if token_util >= 1.0 or usd_util >= 1.0:
            status = "RED"
        elif token_util >= 0.8 or usd_util >= 0.8:
            status = "YELLOW"

        return BurnRateSnapshot(
            tokens_used=self.tokens_used,
            token_budget=self.token_budget,
            usd_spent=round(self.usd_spent, 4),
            usd_budget=self.usd_budget,
            utilization_tokens=round(token_util, 4),
            utilization_usd=round(usd_util, 4),
            status=status,
        )
PY

cat <<'PY' > "${FACTORY_DIR}/core/role_instantiation.py"
from __future__ import annotations

from agi1_factory.core.models import AgentProfile, InstantiationPlan, MissionRequest
from agi1_factory.departments.organization import (
    build_core_team,
    build_executive_team,
    build_leadership_team,
)
from agi1_factory.intelligence_laws.requisite_variety import RequisiteVarietyEngine
from agi1_factory.specialists.catalog import generate_specialist_swarm


class RoleInstantiationEngine:
    """Instantiates workforce based on mission variety and risk profile."""

    def __init__(self, specialist_pool_size: int = 1000) -> None:
        self.variety_engine = RequisiteVarietyEngine()
        self.specialist_pool = generate_specialist_swarm(total=specialist_pool_size)

    def instantiate(self, mission: MissionRequest) -> InstantiationPlan:
        executives = build_executive_team()
        leadership = build_leadership_team()
        core_team = build_core_team()

        assessment = self.variety_engine.assess(
            domains=mission.domains,
            risk_level=mission.risk_level,
            objective=mission.objective,
        )

        selected_specialists = self._select_specialists(
            required=max(1, assessment.recommended_specialists),
            domains=mission.domains,
        )

        return InstantiationPlan(
            executives=executives,
            leadership=leadership,
            core_team=core_team,
            specialists=selected_specialists,
            variety_score=assessment.variety_score,
            rationale=assessment.rationale,
        )

    def _select_specialists(self, *, required: int, domains: list[str]) -> list[AgentProfile]:
        lowered_domains = {domain.strip().lower() for domain in domains}
        ranked: list[tuple[int, AgentProfile]] = []
        for specialist in self.specialist_pool:
            specialist_skills = {skill.lower() for skill in specialist.skills}
            overlap = len(lowered_domains.intersection(specialist_skills))
            ranked.append((overlap, specialist))

        ranked.sort(key=lambda item: item[0], reverse=True)
        chosen = [profile for _, profile in ranked[: min(required, len(ranked))]]
        return chosen
PY

cat <<'PY' > "${FACTORY_DIR}/departments/__init__.py"
"""Departmental roster and org configuration."""

from .organization import (
    CORE_RESEARCH_ENGINEERING_35,
    EXECUTIVE_TIER,
    LEADERSHIP_LAYER,
    SPECIALIZED_BUSINESS_UNITS,
    build_core_team,
    build_executive_team,
    build_leadership_team,
)

__all__ = [
    "EXECUTIVE_TIER",
    "LEADERSHIP_LAYER",
    "CORE_RESEARCH_ENGINEERING_35",
    "SPECIALIZED_BUSINESS_UNITS",
    "build_executive_team",
    "build_leadership_team",
    "build_core_team",
]
PY

cat <<'PY' > "${FACTORY_DIR}/departments/organization.py"
from __future__ import annotations

from agi1_factory.core.models import AgentProfile, AgentTier

EXECUTIVE_TIER = [
    ("jack", "Jack", "AGI-1 CEO", ["execution", "systems", "delivery"]),
    ("julia", "Julia", "AGI-1 CFO & CMO", ["strategy", "finance", "go_to_market"]),
    ("singularity", "Singularity", "CTEO + CREL", ["research", "optimization", "recursion"]),
    ("aegis", "Aegis", "Safety / Alignment Executive", ["safety", "security", "governance"]),
]

LEADERSHIP_LAYER = [
    ("vp_engineering", "VP Engineering", "Engineering", ["platform", "architecture"]),
    ("vp_product", "VP Product", "Product", ["roadmap", "user_outcomes"]),
    ("vp_growth", "VP Growth", "Growth", ["acquisition", "retention"]),
    ("vp_marketing", "VP Marketing", "Marketing", ["brand", "demand_gen"]),
    ("vp_sales", "VP Sales", "Sales", ["pipeline", "enterprise_sales"]),
    ("vp_data", "VP Data", "Data", ["analytics", "experimentation"]),
    ("vp_ops", "VP Operations", "Operations", ["runbooks", "execution"]),
]

# Exactly 35 core R&E roles.
CORE_RESEARCH_ENGINEERING_35 = [
    ("core_01", "Principal Systems Architect", "Engineering"),
    ("core_02", "Staff Backend Engineer", "Engineering"),
    ("core_03", "Staff Frontend Engineer", "Engineering"),
    ("core_04", "Infrastructure Engineer", "Engineering"),
    ("core_05", "Site Reliability Engineer", "Engineering"),
    ("core_06", "Security Engineer", "Engineering"),
    ("core_07", "AI Platform Engineer", "Engineering"),
    ("core_08", "MLOps Engineer", "Engineering"),
    ("core_09", "Data Engineer", "Data"),
    ("core_10", "Analytics Engineer", "Data"),
    ("core_11", "Applied Scientist", "Research"),
    ("core_12", "Research Scientist", "Research"),
    ("core_13", "Evaluation Scientist", "Research"),
    ("core_14", "Model Safety Scientist", "Research"),
    ("core_15", "Agentic Systems Researcher", "Research"),
    ("core_16", "Simulation Engineer", "Research"),
    ("core_17", "Optimization Engineer", "Research"),
    ("core_18", "Prompt Architect", "Research"),
    ("core_19", "Knowledge Graph Engineer", "Research"),
    ("core_20", "Vector Memory Engineer", "Research"),
    ("core_21", "Product Analyst", "Product"),
    ("core_22", "UX Researcher", "Product"),
    ("core_23", "Technical Program Manager", "Operations"),
    ("core_24", "QA Automation Engineer", "Engineering"),
    ("core_25", "Release Engineer", "Engineering"),
    ("core_26", "Platform Reliability Analyst", "Operations"),
    ("core_27", "Data Quality Analyst", "Data"),
    ("core_28", "Benchmarking Engineer", "Research"),
    ("core_29", "Cost Optimization Engineer", "Operations"),
    ("core_30", "Compliance Engineer", "Security"),
    ("core_31", "Observability Engineer", "Engineering"),
    ("core_32", "Tooling Engineer", "Engineering"),
    ("core_33", "Documentation Engineer", "Product"),
    ("core_34", "Incident Response Lead", "Security"),
    ("core_35", "Experimental Design Lead", "Research"),
]

SPECIALIZED_BUSINESS_UNITS = {
    "Growth & Launch": ["Pre-launch Team", "Launch Team", "PMF Finder"],
    "Marketing & Sales": ["Digital Marketing", "PR", "Social Media", "Sales Ops"],
    "Data & Intelligence": ["CDO", "Data Science", "Data Engineering", "Business Intelligence"],
    "User Operations": ["Customer Acquisition", "User Satisfaction", "Retention Growth"],
}


def build_executive_team() -> list[AgentProfile]:
    return [
        AgentProfile(
            agent_id=agent_id,
            display_name=name,
            title=title,
            department="Executive",
            tier=AgentTier.EXECUTIVE,
            skills=skills,
            max_parallel_tasks=4,
        )
        for agent_id, name, title, skills in EXECUTIVE_TIER
    ]


def build_leadership_team() -> list[AgentProfile]:
    return [
        AgentProfile(
            agent_id=agent_id,
            display_name=title,
            title=title,
            department=department,
            tier=AgentTier.LEADERSHIP,
            skills=skills,
            max_parallel_tasks=3,
        )
        for agent_id, title, department, skills in LEADERSHIP_LAYER
    ]


def build_core_team() -> list[AgentProfile]:
    out: list[AgentProfile] = []
    for agent_id, title, department in CORE_RESEARCH_ENGINEERING_35:
        skills = [department.lower(), "execution", "analysis"]
        out.append(
            AgentProfile(
                agent_id=agent_id,
                display_name=title,
                title=title,
                department=department,
                tier=AgentTier.CORE,
                skills=skills,
                max_parallel_tasks=2,
            )
        )
    return out
PY

cat <<'PY' > "${FACTORY_DIR}/specialists/__init__.py"
"""Specialist swarm catalog and provisioning."""

from .catalog import DOMAIN_CLUSTERS, generate_specialist_swarm

__all__ = ["DOMAIN_CLUSTERS", "generate_specialist_swarm"]
PY

cat <<'PY' > "${FACTORY_DIR}/specialists/catalog.py"
from __future__ import annotations

from agi1_factory.core.models import AgentProfile, AgentTier

DOMAIN_CLUSTERS = [
    "law", "medicine", "finance", "robotics", "supply_chain", "education", "energy", "agriculture",
    "cybersecurity", "cloud", "devops", "machine_learning", "product", "marketing", "sales", "biotech",
    "pharma", "materials_science", "quantum", "economics", "venture_capital", "tax", "real_estate",
    "manufacturing", "automotive", "aerospace", "defense", "compliance", "risk", "behavioral_psychology",
    "ux", "narrative_design", "operations", "customer_success", "growth", "branding", "public_policy",
    "international_trade", "payments", "fraud", "iot", "telecom", "media", "gaming", "healthcare_ops",
    "logistics", "retail", "hospitality", "climate", "water_systems", "construction", "insurance",
]


def generate_specialist_swarm(total: int = 1000) -> list[AgentProfile]:
    total = max(1, int(total))
    profiles: list[AgentProfile] = []
    cluster_count = len(DOMAIN_CLUSTERS)

    for idx in range(total):
        domain = DOMAIN_CLUSTERS[idx % cluster_count]
        secondary = DOMAIN_CLUSTERS[(idx * 7) % cluster_count]
        agent_id = f"specialist_{idx + 1:04d}"
        profiles.append(
            AgentProfile(
                agent_id=agent_id,
                display_name=f"{domain.title()} Specialist {idx + 1:04d}",
                title="On-demand Specialist",
                department="Specialist Swarm",
                tier=AgentTier.SPECIALIST,
                skills=[domain, secondary, "execution", "verification"],
                max_parallel_tasks=1,
            )
        )

    return profiles
PY

cat <<'PY' > "${FACTORY_DIR}/intelligence_laws/__init__.py"
"""Physics and intelligence law primitives used by the factory."""

from .invariants import InvariantFinder, InvariantReport
from .least_action import LeastActionPlanner, PathOption
from .requisite_variety import RequisiteVarietyAssessment, RequisiteVarietyEngine

__all__ = [
    "InvariantFinder",
    "InvariantReport",
    "LeastActionPlanner",
    "PathOption",
    "RequisiteVarietyAssessment",
    "RequisiteVarietyEngine",
]
PY

cat <<'PY' > "${FACTORY_DIR}/intelligence_laws/least_action.py"
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PathOption:
    name: str
    time_cost: float
    token_cost: int
    usd_cost: float
    complexity: float


class LeastActionPlanner:
    """Hamilton-inspired least-action planner across time, tokens, cost, and complexity."""

    def score(self, option: PathOption) -> float:
        return (
            (option.time_cost * option.complexity)
            + (option.token_cost * 0.0002)
            + (option.usd_cost * 8.0)
        )

    def choose(self, options: list[PathOption]) -> PathOption:
        if not options:
            raise ValueError("At least one path option is required.")
        return min(options, key=self.score)
PY

cat <<'PY' > "${FACTORY_DIR}/intelligence_laws/requisite_variety.py"
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequisiteVarietyAssessment:
    variety_score: float
    environment_variety: int
    control_variety: int
    recommended_specialists: int
    rationale: str


class RequisiteVarietyEngine:
    """Ashby's law implementation for specialist swarm sizing."""

    _RISK_MULTIPLIER = {
        "low": 1.0,
        "medium": 1.3,
        "high": 1.8,
        "critical": 2.4,
    }

    def assess(self, *, domains: list[str], risk_level: str, objective: str) -> RequisiteVarietyAssessment:
        unique_domains = {domain.strip().lower() for domain in domains if domain.strip()}
        environment_variety = max(1, len(unique_domains))
        objective_complexity = max(1, len(objective.split()) // 8)
        multiplier = self._RISK_MULTIPLIER.get(risk_level.strip().lower(), 1.2)

        control_variety = int((environment_variety + objective_complexity) * multiplier)
        recommended = min(1000, max(10, control_variety * 4))
        variety_score = min(1.0, recommended / 1000.0)

        rationale = (
            f"domains={environment_variety}, objective_complexity={objective_complexity}, "
            f"risk_multiplier={multiplier}"
        )
        return RequisiteVarietyAssessment(
            variety_score=round(variety_score, 4),
            environment_variety=environment_variety,
            control_variety=control_variety,
            recommended_specialists=recommended,
            rationale=rationale,
        )
PY

cat <<'PY' > "${FACTORY_DIR}/intelligence_laws/invariants.py"
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean


@dataclass(frozen=True)
class InvariantReport:
    stable_metrics: list[str] = field(default_factory=list)
    unstable_metrics: list[str] = field(default_factory=list)


class InvariantFinder:
    """Noether-inspired invariant detector for recurring market/system signals."""

    def identify(self, metric_windows: dict[str, list[float]], tolerance_ratio: float = 0.05) -> InvariantReport:
        stable: list[str] = []
        unstable: list[str] = []

        for metric, values in metric_windows.items():
            if len(values) < 2:
                unstable.append(metric)
                continue
            avg = mean(values)
            if avg == 0:
                unstable.append(metric)
                continue
            span = max(values) - min(values)
            variation = abs(span / avg)
            if variation <= tolerance_ratio:
                stable.append(metric)
            else:
                unstable.append(metric)

        return InvariantReport(stable_metrics=stable, unstable_metrics=unstable)
PY

cat <<'PY' > "${FACTORY_DIR}/harness/__init__.py"
"""Autonomous Factory execution harness."""

from .autonomous_factory import AutonomousFactory

__all__ = ["AutonomousFactory"]
PY

cat <<'PY' > "${FACTORY_DIR}/harness/autonomous_factory.py"
from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Any

from agi1_factory.core.consensus import ExecutiveConsensus
from agi1_factory.core.message_bus import AsyncMessageBus
from agi1_factory.core.mission_planner import AGIGPSMissionPlanner
from agi1_factory.core.models import MissionRequest
from agi1_factory.core.resource_governor import BurnRateGovernor
from agi1_factory.core.role_instantiation import RoleInstantiationEngine
from agi1_factory.intelligence_laws.invariants import InvariantFinder
from agi1_factory.intelligence_laws.least_action import LeastActionPlanner, PathOption


class AutonomousFactory:
    """Top-level orchestrator for AGI-1 Autonomous Agentics Factory."""

    def __init__(self) -> None:
        self.consensus = ExecutiveConsensus()
        self.message_bus = AsyncMessageBus()
        self.mission_planner = AGIGPSMissionPlanner()
        self.role_engine = RoleInstantiationEngine(specialist_pool_size=1000)
        self.invariant_finder = InvariantFinder()
        self.action_planner = LeastActionPlanner()
        self._register_department_handlers()

    async def run_mission(
        self,
        *,
        objective: str,
        domains: list[str],
        risk_level: str,
        budget_tokens: int = 1_500_000,
        budget_usd: float = 250.0,
    ) -> dict[str, Any]:
        mission = MissionRequest(
            mission_id=f"mission_{uuid.uuid4().hex[:10]}",
            objective=objective,
            domains=domains,
            risk_level=risk_level,
            budget_tokens=budget_tokens,
            budget_usd=budget_usd,
        )

        layers = self.mission_planner.build_layers(mission)
        instantiation = self.role_engine.instantiate(mission)
        burn_rate = BurnRateGovernor(token_budget=budget_tokens, usd_budget=budget_usd)

        votes = {
            "jack": True,
            "julia": True,
            "singularity": True,
            "aegis": risk_level.lower() not in {"critical"},
        }
        rationale = {
            "aegis": "critical risk requires additional controls",
        }
        consensus = self.consensus.evaluate(votes=votes, rationales=rationale)

        action = self.action_planner.choose(
            [
                PathOption("Conservative", time_cost=6.0, token_cost=220_000, usd_cost=35.0, complexity=1.1),
                PathOption("Balanced", time_cost=4.0, token_cost=300_000, usd_cost=42.0, complexity=1.0),
                PathOption("Aggressive", time_cost=2.5, token_cost=480_000, usd_cost=68.0, complexity=1.4),
            ]
        )

        burn_rate.consume(tokens=action.token_cost, usd_cost=action.usd_cost)
        data_response = await self.message_bus.request(
            "data.intelligence.request",
            {
                "mission_id": mission.mission_id,
                "objective": objective,
                "domains": domains,
            },
        )
        growth_response = await self.message_bus.request(
            "growth.launch.request",
            {
                "mission_id": mission.mission_id,
                "objective": objective,
                "market_signals": data_response.get("market_signals", []),
            },
        )

        invariants = self.invariant_finder.identify(
            {
                "daily_active_users": [10200, 10180, 10210, 10205],
                "conversion_rate": [0.054, 0.0542, 0.0539, 0.0541],
                "infrastructure_cost": [780.0, 790.0, 785.0, 788.0],
            }
        )

        for layer in layers:
            if consensus.approved:
                layer.status = "DONE"
                layer.evidence.append("consensus_approved")
            else:
                layer.status = "BLOCKED"
                layer.evidence.append("consensus_denied")

        return {
            "pm": "OpenClaw",
            "exec": "Jack | Julia | Singularity | Aegis",
            "mission": asdict(mission),
            "consensus": asdict(consensus),
            "selected_action_path": asdict(action),
            "burn_rate": asdict(burn_rate.snapshot()),
            "layers": [asdict(item) for item in layers],
            "instantiation_summary": {
                "executives": len(instantiation.executives),
                "leadership": len(instantiation.leadership),
                "core_team": len(instantiation.core_team),
                "specialists": len(instantiation.specialists),
                "variety_score": instantiation.variety_score,
                "rationale": instantiation.rationale,
            },
            "department_exchange": {
                "data_intelligence": data_response,
                "growth_launch": growth_response,
            },
            "invariants": asdict(invariants),
        }

    def _register_department_handlers(self) -> None:
        async def data_intelligence_handler(payload: dict[str, Any]) -> dict[str, Any]:
            objective = str(payload.get("objective", ""))
            return {
                "status": "ok",
                "mission_id": payload.get("mission_id", ""),
                "market_signals": [
                    "enterprise_ai_budget_growth",
                    "increased_whatsapp_workflow_adoption",
                    "demand_for_governed_agentic_ops",
                ],
                "insight": f"CDO validated demand trends for objective: {objective[:120]}",
            }

        async def growth_launch_handler(payload: dict[str, Any]) -> dict[str, Any]:
            market_signals = payload.get("market_signals", [])
            return {
                "status": "ok",
                "mission_id": payload.get("mission_id", ""),
                "launch_plan": [
                    "internal_alpha",
                    "closed_beta",
                    "graduated_rollout_5_20_50_100",
                ],
                "signals_used": market_signals,
            }

        self.message_bus.subscribe("data.intelligence.request", data_intelligence_handler)
        self.message_bus.subscribe("growth.launch.request", growth_launch_handler)
PY

cat <<'PY' > "${FACTORY_DIR}/harness/run_demo.py"
from __future__ import annotations

import asyncio
import json

from agi1_factory.harness.autonomous_factory import AutonomousFactory


async def main() -> None:
    factory = AutonomousFactory()
    report = await factory.run_mission(
        objective="Launch AGI-1 to 1M users with reliable governance, growth funnel execution, and cost discipline.",
        domains=["engineering", "finance", "marketing", "operations", "legal"],
        risk_level="high",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
PY

cat <<'MD' > "${FACTORY_DIR}/README.md"
# AGI-1 Autonomous Factory

This scaffold initializes a multi-tier agentic corporation runtime:

- `core/`: consensus, message bus, mission planning, role instantiation, resource governance
- `departments/`: executive + leadership + 35 core R&E roster
- `specialists/`: deterministic 1,000-agent specialist swarm generator
- `intelligence_laws/`: Least Action, Requisite Variety, Invariants
- `harness/`: end-to-end mission execution harness

## Quick start

```bash
python3 -m agi1_factory.harness.run_demo
```
MD

# Smoke check importability without writing bytecode caches.
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from agi1_factory.harness.autonomous_factory import AutonomousFactory

factory = AutonomousFactory()
assert factory is not None
PY

echo "PM: OpenClaw"
echo "Exec: Jack | Julia | Singularity | Aegis"
echo "Autonomous Factory scaffold generated at: ${FACTORY_DIR}"
