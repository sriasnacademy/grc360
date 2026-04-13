from models.my_llm_client import LLMClient
from datetime import datetime
import re
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_AI_EVALUATOR, ACTOR_GROQ_LLAMA_70B,
)


class AIEvaluator:
    """
    Authoritative evaluator.
    - Manual rules FIRST
    - LLM only if undecidable
    Every evaluation — manual or LLM — is recorded in the Attribution Agent.
    """

    def __init__(self):
        self.llm = LLMClient()

    def evaluate_step(self, step_name: str, tasks: list) -> dict:
        evaluated_tasks = []
        for task in tasks:
            evaluated_tasks.append(self.evaluate_task(task, step_name))

        step_status = "PASS"
        for t in evaluated_tasks:
            if t["status"] == "FAIL":
                step_status = "FAIL"
                break

        return {
            "status": step_status,
            "reason": "One or more tasks failed" if step_status == "FAIL" else "All tasks passed",
            "tasks":  evaluated_tasks,
        }

    def evaluate_task(self, task: dict, step_name: str) -> dict:
        evidence = task.get("evidence", [])
        rule     = task.get("evaluation_rule", "")
        expected = task.get("expected_condition", "")

        manual = self.manual_rule_evaluation(evidence, rule)
        if manual["decided"]:
            task.update(manual)
            task["evaluation_source"] = "MANUAL"

            # ── Attribution: manual rule ─────────────────────────────
            attribution_agent.record(
                action_type      = ActionType.AI_EVALUATION,
                actor            = ACTOR_AI_EVALUATOR,
                sources          = [
                    Source("eval-evidence", "Evidence Records", "database",
                           f"test_task_id={task.get('test_task_id', 'unknown')}",
                           excerpt=str(evidence)[:200]),
                ],
                decision_summary = f"Task '{task.get('task_name', '')}': {manual.get('status')} (manual rule)",
                reasoning        = f"Rule: '{rule}' | Result: {manual.get('reason')}",
                confidence       = ConfidenceLevel.HIGH,
                tags             = ["evaluation", "manual-rule", manual.get("status", "").lower()],
            )
            # ────────────────────────────────────────────────────────
            return task

        llm_result = self.llm_evaluate_task(
            step_name, task["task_name"], evidence, rule, expected
        )
        task.update(llm_result)
        task["evaluation_source"] = "LLM"

        # ── Attribution: LLM evaluation ──────────────────────────────
        attribution_agent.record(
            action_type      = ActionType.AI_EVALUATION,
            actor            = ACTOR_GROQ_LLAMA_70B,
            sources          = [
                Source("eval-evidence", "Evidence Records", "database",
                       f"test_task_id={task.get('test_task_id', 'unknown')}",
                       excerpt=str(evidence)[:200]),
                Source("eval-rule", "Evaluation Rule", "text", rule, excerpt=rule[:200]),
            ],
            decision_summary = f"Task '{task.get('task_name', '')}': {llm_result.get('status')} (LLM)",
            reasoning        = f"LLM evaluated step '{step_name}' | Reason: {llm_result.get('reason')}",
            confidence       = ConfidenceLevel.MEDIUM,
            tags             = ["evaluation", "llm", llm_result.get("status", "").lower()],
        )
        # ────────────────────────────────────────────────────────────
        return task

    def manual_rule_evaluation(self, evidence, rule):
        count = len(evidence)

        if re.search(r"count\s*>\s*0", rule, re.I):
            return self._pass("Records found") if count > 0 else self._fail("No records found")
        if re.search(r"count\s*==\s*0", rule, re.I):
            return self._pass("No records as expected") if count == 0 else self._fail("Unexpected records")
        if "NOT NULL" in rule.upper():
            field = rule.split("NOT NULL")[-1].strip()
            for r in evidence:
                if not r.get(field):
                    return self._fail(f"{field} is NULL")
            return self._pass(f"{field} populated")
        if "MAX(" in rule.upper():
            match = re.search(r"MAX\((.*?)\)", rule, re.I)
            field = match.group(1)
            dates = [r.get(field) for r in evidence if r.get(field)]
            return self._pass("Valid date exists") if dates else self._fail("No valid dates")

        return {"decided": False}

    def llm_evaluate_task(self, step, task, evidence, rule, expected):
        evidence_str = "\n".join(str(e) for e in evidence) if evidence else "No records"
        prompt = f"""
You are an IT auditor.

Step: {step}
Task: {task}

Rule: {rule}
Expected: {expected}

Evidence:
{evidence_str}

Reply ONLY:
PASS: <reason> OR FAIL: <reason>
"""
        out = self.llm.generate(prompt)

        if not out or not out.strip():
            return {"status": "FAIL", "reason": "LLM returned empty response"}

        line = next((l for l in out.splitlines() if l.strip()), None)
        if not line:
            return {"status": "FAIL", "reason": "LLM response had no readable content"}
        if ":" not in line:
            return {"status": "FAIL", "reason": f"LLM response format unexpected: {line}"}

        status = "FAIL" if line.upper().startswith("FAIL") else "PASS"
        return {"status": status, "reason": line.split(":", 1)[1].strip()}

    @staticmethod
    def _pass(reason):
        return {"decided": True, "status": "PASS", "reason": reason}

    @staticmethod
    def _fail(reason):
        return {"decided": True, "status": "FAIL", "reason": reason}
