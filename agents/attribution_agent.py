"""
Attribution Agent — GRC360
===========================
Tracks EVERY AI decision in the system:
  • Intent classification (IntentAgent)
  • Pipeline executions  (control / risk / process / subprocess / test_plan)
  • AI evaluation       (AIEvaluator — manual rule + LLM fallback)
  • Evidence execution  (EvidenceExecutor)
  • Guardrail outcomes  (GuardrailEngine / Bedrock guardrails)
  • Workflow transitions (WorkflowEngine)

Usage
-----
    from agents.attribution_agent import attribution_agent, ActionType, ActorType, Actor, Source

    # record any AI action
    record = attribution_agent.record(
        action_type=ActionType.CONTROL_UPDATE,
        actor=Actor("llm-groq", "Groq LLaMA", ActorType.AI_AGENT, version="llama-3.1-8b"),
        sources=[Source("s1", "User Input", "text", raw_text, excerpt=raw_text[:120])],
        decision_summary="Control inserted",
        reasoning="LLM extracted structured control from free text",
    )
"""

import uuid
import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum
from connectors.lambda_mysql import call_lambda


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class ActorType(str, Enum):
    HUMAN          = "human"
    AI_AGENT       = "ai_agent"
    SYSTEM         = "system"
    EXTERNAL_TOOL  = "external_tool"


class ActionType(str, Enum):
    INTENT_CLASSIFICATION = "intent_classification"
    CONTROL_PIPELINE      = "control_pipeline"
    RISK_PIPELINE         = "risk_pipeline"
    PROCESS_PIPELINE      = "process_pipeline"
    SUBPROCESS_PIPELINE   = "subprocess_pipeline"
    TEST_PLAN_PIPELINE    = "test_plan_pipeline"
    AI_EVALUATION         = "ai_evaluation"
    EVIDENCE_EXECUTION    = "evidence_execution"
    GUARDRAIL_CHECK       = "guardrail_check"
    WORKFLOW_TRANSITION   = "workflow_transition"
    RAG_RETRIEVAL         = "rag_retrieval"
    CUSTOM                = "custom"


class ConfidenceLevel(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


# ─────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────

@dataclass
class Source:
    source_id:       str
    name:            str
    source_type:     str          # "text", "database", "api", "llm", "rag"
    reference:       str          # table name, URL, file path, model name …
    excerpt:         Optional[str] = None
    relevance_score: float         = 1.0
    retrieved_at:    str           = field(default_factory=lambda: _now())


@dataclass
class Actor:
    actor_id:   str
    name:       str
    actor_type: ActorType
    version:    Optional[str] = None
    metadata:   dict          = field(default_factory=dict)


@dataclass
class AttributionRecord:
    record_id:        str
    action_type:      ActionType
    actor:            Actor
    sources:          list
    decision_summary: str
    reasoning:        str
    confidence:       ConfidenceLevel
    framework_refs:   list
    tags:             list
    timestamp:        str
    parent_record_id: Optional[str]
    checksum:         str


# ─────────────────────────────────────────────
# Pre-built Actors (reusable across the app)
# ─────────────────────────────────────────────

ACTOR_GROQ_LLAMA_70B = Actor(
    actor_id="groq-llama-70b",
    name="Groq LLaMA 3.3 70B",
    actor_type=ActorType.AI_AGENT,
    version="llama-3.3-70b-versatile",
)

ACTOR_GROQ_LLAMA_8B = Actor(
    actor_id="groq-llama-8b",
    name="Groq LLaMA 3.1 8B",
    actor_type=ActorType.AI_AGENT,
    version="llama-3.1-8b-instant",
)

ACTOR_AI_EVALUATOR = Actor(
    actor_id="ai-evaluator",
    name="GRC360 AI Evaluator",
    actor_type=ActorType.AI_AGENT,
    version="1.0",
)

ACTOR_GUARDRAIL_ENGINE = Actor(
    actor_id="guardrail-engine",
    name="GRC360 Guardrail Engine",
    actor_type=ActorType.SYSTEM,
    version="1.0",
)

ACTOR_BEDROCK_GUARDRAIL = Actor(
    actor_id="bedrock-guardrail",
    name="AWS Bedrock Guardrail",
    actor_type=ActorType.EXTERNAL_TOOL,
    version="bedrock-guardrails-v1",
)

ACTOR_WORKFLOW_ENGINE = Actor(
    actor_id="workflow-engine",
    name="GRC360 Workflow Engine",
    actor_type=ActorType.SYSTEM,
    version="1.0",
)

ACTOR_EVIDENCE_EXECUTOR = Actor(
    actor_id="evidence-executor",
    name="GRC360 Evidence Executor",
    actor_type=ActorType.SYSTEM,
    version="1.0",
)

ACTOR_RAG_SERVICE = Actor(
    actor_id="rag-service",
    name="GRC360 RAG Retrieval",
    actor_type=ActorType.SYSTEM,
    version="pgvector-1.0",
)

ACTOR_SYSTEM = Actor(
    actor_id="system",
    name="GRC360 System",
    actor_type=ActorType.SYSTEM,
)


# ─────────────────────────────────────────────
# Attribution Agent
# ─────────────────────────────────────────────

class AttributionAgent:
    """
    Central attribution store for GRC360.
    Append-only. Every record gets a SHA-256 integrity checksum.
    """

    def __init__(self, agent_id: str = "grc360-attribution-v1"):
        self.agent_id = agent_id
        self._log: list[AttributionRecord] = []

    # ── record ──────────────────────────────

    def record(
        self,
        action_type: ActionType,
        actor: Actor,
        sources: list,
        decision_summary: str,
        reasoning: str,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        framework_refs: Optional[list] = None,
        tags: Optional[list] = None,
        parent_record_id: Optional[str] = None,
    ) -> AttributionRecord:
        rec = AttributionRecord(
            record_id        = str(uuid.uuid4()),
            action_type      = action_type,
            actor            = actor,
            sources          = sources,
            decision_summary = decision_summary,
            reasoning        = reasoning,
            confidence       = confidence,
            framework_refs   = framework_refs or [],
            tags             = tags or [],
            timestamp        = _now(),
            parent_record_id = parent_record_id,
            checksum         = "",
        )
        rec.checksum = self._checksum(rec)
        self._log.append(rec)
        self._save_to_db(rec)
        print(f"[ATTRIBUTION] {action_type.value} → {rec.record_id[:8]}…  actor={actor.name}")
        return rec

    # ── explain ─────────────────────────────

    def explain(self, record_id: str) -> str:
        rec = self._get(record_id)
        if not rec:
            return f"No record: {record_id}"

        src_lines = "\n".join(
            f"  [{i+1}] {s.name} ({s.source_type}) — {s.reference}"
            f"{(' | ' + s.excerpt[:100]) if s.excerpt else ''}"
            f" [relevance: {s.relevance_score:.0%}]"
            for i, s in enumerate(rec.sources)
        )
        fw = ", ".join(rec.framework_refs) or "None"
        return (
            f"\nAttribution Report\n{'='*60}\n"
            f"Record ID   : {rec.record_id}\n"
            f"Timestamp   : {rec.timestamp}\n"
            f"Action      : {rec.action_type.value}\n"
            f"Actor       : {rec.actor.name} ({rec.actor.actor_type.value})"
            f"{f' v{rec.actor.version}' if rec.actor.version else ''}\n"
            f"Confidence  : {rec.confidence.value.upper()}\n"
            f"Frameworks  : {fw}\n"
            f"Tags        : {', '.join(rec.tags) or 'none'}\n"
            f"\nDecision\n{'-'*40}\n{rec.decision_summary}\n"
            f"\nReasoning\n{'-'*40}\n{rec.reasoning}\n"
            f"\nSources ({len(rec.sources)})\n{'-'*40}\n{src_lines or '  (none)'}\n"
            f"\nIntegrity   : {'✅ valid' if self.verify(record_id) else '❌ TAMPERED'}\n"
            f"Checksum    : {rec.checksum}\n"
            f"{'='*60}\n"
        )

    # ── verify ──────────────────────────────

    def verify(self, record_id: str) -> bool:
        rec = self._get(record_id)
        if not rec:
            return False
        stored = rec.checksum
        rec.checksum = ""
        expected = self._checksum(rec)
        rec.checksum = stored
        return stored == expected

    # ── query ───────────────────────────────

    def get_trail(
        self,
        actor_id:    Optional[str] = None,
        action_type: Optional[ActionType] = None,
        tag:         Optional[str] = None,
    ) -> list:
        results = self._log
        if actor_id:
            results = [r for r in results if r.actor.actor_id == actor_id]
        if action_type:
            results = [r for r in results if r.action_type == action_type]
        if tag:
            results = [r for r in results if tag in r.tags]
        return results

    # ── export ──────────────────────────────

    def export_json(self, record_id: Optional[str] = None) -> str:
        if record_id:
            rec = self._get(record_id)
            data = asdict(rec) if rec else {}
        else:
            data = [asdict(r) for r in self._log]
        return json.dumps(data, indent=2, default=str)

    def summary(self) -> dict:
        if not self._log:
            return {"total_records": 0}
        by_action: dict = {}
        by_actor:  dict = {}
        for r in self._log:
            by_action[r.action_type.value] = by_action.get(r.action_type.value, 0) + 1
            by_actor[r.actor.name]         = by_actor.get(r.actor.name, 0) + 1
        return {
            "total_records": len(self._log),
            "by_action": by_action,
            "by_actor":  by_actor,
            "earliest":  self._log[0].timestamp,
            "latest":    self._log[-1].timestamp,
        }

    # ── private ─────────────────────────────

    def _get(self, record_id: str) -> Optional[AttributionRecord]:
        return next((r for r in self._log if r.record_id == record_id), None)

    @staticmethod
    def _checksum(rec: AttributionRecord) -> str:
        payload = json.dumps(asdict(rec), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def _save_to_db(self, rec):
        payload = {
            "action": "raw_sql",
            "sql": """
                INSERT INTO attribution_records (
                    record_id, action_type,
                    actor_id, actor_name, actor_type, actor_version,
                    decision_summary, reasoning, confidence,
                    sources, tags, framework_refs,
                    parent_record_id, timestamp, checksum
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            "params": [
                rec.record_id,
                rec.action_type.value,

                rec.actor.actor_id,
                rec.actor.name,
                rec.actor.actor_type.value,
                rec.actor.version,

                rec.decision_summary,
                rec.reasoning,
                rec.confidence.value,

                json.dumps([asdict(s) for s in rec.sources], default=str),
                json.dumps(rec.tags),
                json.dumps(rec.framework_refs),

                rec.parent_record_id,
                rec.timestamp.replace("T", " ").split(".")[0],
                rec.checksum
            ]
        }

        try:
            call_lambda(payload)
        except Exception as e:
            print("❌ Attribution DB ERROR:", e)


# ─────────────────────────────────────────────
# Singleton — import and use everywhere
# ─────────────────────────────────────────────
attribution_agent = AttributionAgent()


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
