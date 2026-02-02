from models.my_llm_client import LLMClient
from datetime import datetime
import re


class AIEvaluator:
    """
    Hybrid evaluator:
    1. Manual rule-based evaluation (authoritative)
    2. LLM fallback for ambiguity
    """

    def __init__(self):
        self.llm = LLMClient()

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================
    def evaluate_test_step(self, test_step_result: dict) -> dict:
        """
        Evaluate each task, then derive step result.
        """

        step_name = test_step_result.get("step_name")
        tasks = test_step_result.get("tasks", [])

        evaluated_tasks = []

        for task in tasks:
            evaluated_task = self.evaluate_task(task, step_name)
            evaluated_tasks.append(evaluated_task)

        # 🔥 STEP FAILS IF ANY TASK FAILS
        step_status = "PASS"
        for t in evaluated_tasks:
            if t["status"] == "FAIL":
                step_status = "FAIL"
                break

        test_step_result["tasks"] = evaluated_tasks
        test_step_result["status"] = step_status
        test_step_result["reason"] = (
            "One or more tasks failed"
            if step_status == "FAIL"
            else "All tasks passed"
        )

        return test_step_result

    # ==========================================================
    # TASK EVALUATION
    # ==========================================================
    def evaluate_task(self, task: dict, step_name: str) -> dict:
        """
        Evaluate a single task using:
        - Manual rules first
        - LLM fallback
        """

        evidence = task.get("evidence", [])
        evaluation_rule = task.get("evaluation_rule", "")
        expected_condition = task.get("expected_condition", "")

        # 1️⃣ Manual evaluation
        manual_result = self.manual_rule_evaluation(
            evidence, evaluation_rule, expected_condition
        )

        if manual_result["decided"]:
            task["status"] = manual_result["status"]
            task["reason"] = manual_result["reason"]
            return task

        # 2️⃣ LLM fallback
        llm_result = self.llm_evaluate_task(
            step_name=step_name,
            task_name=task.get("task_name"),
            evidence=evidence,
            evaluation_rule=evaluation_rule,
            expected_condition=expected_condition,
        )

        task["status"] = llm_result["status"]
        task["reason"] = llm_result["reason"]

        return task

    # ==========================================================
    # MANUAL RULE ENGINE
    # ==========================================================
    def manual_rule_evaluation(self, evidence, rule, expected):
        """
        Returns:
        {
            decided: bool,
            status: PASS/FAIL,
            reason: str
        }
        """

        count = len(evidence)

        # ---- Rule: COUNT > 0
        if re.search(r"count\s*>\s*0", rule, re.I):
            if count > 0:
                return self._pass("Records found")
            return self._fail("No records found")

        # ---- Rule: COUNT == 0
        if re.search(r"count\s*==\s*0", rule, re.I):
            if count == 0:
                return self._pass("No records as expected")
            return self._fail("Unexpected records found")

        # ---- Rule: NOT NULL field
        if "NOT NULL" in rule.upper():
            field = rule.split("NOT NULL")[-1].strip()
            for r in evidence:
                if not r.get(field):
                    return self._fail(f"{field} is NULL")
            return self._pass(f"{field} populated")

        # ---- Rule: MAX(date) >= threshold
        if "MAX(" in rule.upper():
            match = re.search(r"MAX\((.*?)\)", rule, re.I)
            if match:
                field = match.group(1)
                dates = [
                    r.get(field)
                    for r in evidence
                    if isinstance(r.get(field), datetime)
                ]
                if not dates:
                    return self._fail("No valid dates found")
                return self._pass("Valid date exists")

        # ❓ Not decidable
        return {"decided": False}

    # ==========================================================
    # LLM EVALUATION
    # ==========================================================
    def llm_evaluate_task(
        self,
        step_name: str,
        task_name: str,
        evidence: list,
        evaluation_rule: str,
        expected_condition: str,
    ) -> dict:

        evidence_str = (
            "\n".join(str(e) for e in evidence) if evidence else "No records"
        )

        prompt = f"""
You are an IT audit expert.

Test Step:
{step_name}

Task:
{task_name}

Evaluation Rule:
{evaluation_rule}

Expected Condition:
{expected_condition}

Evidence:
{evidence_str}

Instructions:
- Decide strictly PASS or FAIL
- If evidence violates rule → FAIL
- If evidence satisfies rule → PASS
- Respond in ONE LINE only:
  PASS: <reason> OR FAIL: <reason>
"""

        llm_output = self.llm.generate(prompt)

        first_line = next(
            (l.strip() for l in llm_output.splitlines() if l.strip()),
            "FAIL: Unable to evaluate",
        )

        status = "FAIL" if first_line.upper().startswith("FAIL") else "PASS"
        reason = first_line.split(":", 1)[-1].strip()

        return {"status": status, "reason": reason}

    # ==========================================================
    # HELPERS
    # ==========================================================
    def _pass(self, reason):
        return {"decided": True, "status": "PASS", "reason": reason}

    def _fail(self, reason):
        return {"decided": True, "status": "FAIL", "reason": reason}
