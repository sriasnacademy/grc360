from connectors.lambda_mysql import call_lambda
from difflib import SequenceMatcher
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_GUARDRAIL_ENGINE,
)


class GuardrailEngine:

    def __init__(self):
        pass

    def fuzzy_match(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def load_rules(self):
        result = call_lambda({"action": "select", "table": "guardrail_rules", "where": {"is_active": 1}})
        return result.get("records", [])

    def load_conditions(self, rule_id):
        result = call_lambda({"action": "select", "table": "guardrail_conditions", "where": {"rule_id": rule_id}})
        return result.get("records", [])

    def load_actions(self, rule_id):
        result = call_lambda({"action": "select", "table": "guardrail_actions", "where": {"rule_id": rule_id}})
        return result.get("records", [])

    def evaluate_condition(self, condition, payload):
        key   = condition["condition_key"]
        op    = condition["operator"]
        value = condition["condition_value"]
        fv    = payload.get(key, "")
        if op == "=":           return fv == value
        if op == "!=":          return fv != value
        if op == "contains":    return value.lower() in fv.lower()
        if op == "not_contains": return value.lower() not in fv.lower()
        return False

    def check_duplicate_in_db(self, process_name):
        result  = call_lambda({"action": "select", "table": "processes"})
        records = result.get("records", [])
        for row in records:
            if self.fuzzy_match(process_name, row.get("process_name", "")) >= 0.80:
                return True
        return False

    def evaluate(self, payload):
        rules = self.load_rules()
        for rule in rules:
            rule_id     = rule["rule_id"]
            conditions  = self.load_conditions(rule_id)
            triggered   = True
            for cond in conditions:
                if cond["condition_key"] == "process_name" and cond["operator"] == "contains":
                    triggered = self.check_duplicate_in_db(payload["process_name"])
                else:
                    if not self.evaluate_condition(cond, payload):
                        triggered = False
            if triggered:
                actions = self.load_actions(rule_id)
                result  = self.execute_actions(actions, rule["rule_name"])

                # ── Attribution record ──────────────────────────────
                attribution_agent.record(
                    action_type      = ActionType.GUARDRAIL_CHECK,
                    actor            = ACTOR_GUARDRAIL_ENGINE,
                    sources          = [
                        Source("gr-rules", "Guardrail Rules DB", "database",
                               f"guardrail_rules[rule_id={rule_id}]",
                               excerpt=rule.get("rule_name", "")),
                    ],
                    decision_summary = (
                        f"Guardrail rule '{rule['rule_name']}' triggered. "
                        f"Outcome: {'BLOCKED' if not result['allowed'] else 'ALLOWED'}"
                    ),
                    reasoning        = result.get("message", ""),
                    confidence       = ConfidenceLevel.HIGH,
                    tags             = [
                        "guardrail",
                        "blocked" if not result["allowed"] else "allowed",
                    ],
                )
                # ────────────────────────────────────────────────────
                return result

        return {"allowed": True, "message": "All guardrails passed."}

    def execute_actions(self, actions, rule_name):
        for action in actions:
            if action["action_type"] == "block":
                return {"allowed": False, "message": action["action_message"], "rule": rule_name}
        return {"allowed": True, "message": "Rule triggered but not blocking", "rule": rule_name}

    def insert_process(self, pname):
        return call_lambda({
            "action": "insert",
            "table":  "processes",
            "data": {"process_name": pname, "description": "", "department": "",
                     "process_owner": "", "frequency": "", "triggers": "", "outcomes": ""}
        })

    def submit(self, pname):
        result = self.evaluate({"process_name": pname})
        if not result["allowed"]:
            return {"success": False, "message": result["message"]}
        try:
            self.insert_process(pname)
            return {"success": True, "message": "Process saved successfully!"}
        except Exception as e:
            return {"success": False, "message": f"Lambda DB Error: {e}"}
