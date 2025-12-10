from connectors.lambda_mysql import call_lambda


class GuardrailEngine:

    def __init__(self):
        pass   # ✅ No db object anymore

    # -----------------------------------------------------
    # LOAD ACTIVE RULES
    # -----------------------------------------------------
    def load_rules(self):

        payload = {
            "action": "select",
            "table": "guardrail_rules",
            "where": {"is_active": 1}
        }

        result = call_lambda(payload)   # ✅ FUNCTION CALL
        return result.get("records", [])

    # -----------------------------------------------------
    # LOAD CONDITIONS FOR A RULE
    # -----------------------------------------------------
    def load_conditions(self, rule_id):

        payload = {
            "action": "select",
            "table": "guardrail_conditions",
            "where": {"rule_id": rule_id}
        }

        result = call_lambda(payload)
        return result.get("records", [])

    # -----------------------------------------------------
    # LOAD ACTIONS FOR A RULE
    # -----------------------------------------------------
    def load_actions(self, rule_id):

        payload = {
            "action": "select",
            "table": "guardrail_actions",
            "where": {"rule_id": rule_id}
        }

        result = call_lambda(payload)
        return result.get("records", [])

    # -----------------------------------------------------
    # EVALUATE CONDITION
    # -----------------------------------------------------
    def evaluate_condition(self, condition, payload):

        key = condition["condition_key"]
        operator = condition["operator"]
        value = condition["condition_value"]

        field_value = payload.get(key, "")

        if operator == "=":
            return field_value == value
        elif operator == "!=":
            return field_value != value
        elif operator == "contains":
            return value.lower() in field_value.lower()
        elif operator == "not_contains":
            return value.lower() not in field_value.lower()

        return False

    # -----------------------------------------------------
    # DUPLICATE PROCESS CHECK
    # -----------------------------------------------------
    def check_duplicate_in_db(self, process_name):

        payload = {
            "action": "select",
            "table": "processes",
            "where": {"process_name": process_name}
        }

        result = call_lambda(payload)
        return len(result.get("records", [])) > 0

    # -----------------------------------------------------
    # MAIN GUARDRAIL EXECUTION
    # -----------------------------------------------------
    def evaluate(self, payload):

        rules = self.load_rules()

        for rule in rules:

            rule_id = rule["rule_id"]
            conditions = self.load_conditions(rule_id)
            rule_triggered = True

            for cond in conditions:

                if cond["condition_key"] == "process_name" and cond["operator"] == "contains":
                    rule_triggered = self.check_duplicate_in_db(payload["process_name"])
                else:
                    if not self.evaluate_condition(cond, payload):
                        rule_triggered = False

            if rule_triggered:
                actions = self.load_actions(rule_id)
                return self.execute_actions(actions, rule["rule_name"])

        return {"allowed": True, "message": "All guardrails passed."}

    # -----------------------------------------------------
    # EXECUTE ACTIONS
    # -----------------------------------------------------
    def execute_actions(self, actions, rule_name):

        for action in actions:
            if action["action_type"] == "block":
                return {
                    "allowed": False,
                    "message": action["action_message"],
                    "rule": rule_name
                }

        return {
            "allowed": True,
            "message": "Rule triggered but not blocking",
            "rule": rule_name
        }

    # -----------------------------------------------------
    # INSERT PROCESS
    # -----------------------------------------------------
    def insert_process(self, pname):

        payload = {
            "action": "insert",
            "table": "processes",
            "data": {
                "process_name": pname,
                "description": "",
                "department": "",
                "process_owner": "",
                "frequency": "",
                "triggers": "",
                "outcomes": ""
            }
        }

        return call_lambda(payload)

    # -----------------------------------------------------
    # FINAL ENTRY POINT (UI)
    # -----------------------------------------------------
    def submit(self, pname):

        payload = {"process_name": pname}

        # 1. Rule Check
        result = self.evaluate(payload)

        if not result["allowed"]:
            return {
                "success": False,
                "message": result["message"]
            }

        # 2. Insert Process
        try:
            self.insert_process(pname)
            return {"success": True, "message": "Process saved successfully!"}
        except Exception as e:
            return {"success": False, "message": f"Lambda DB Error: {e}"}
