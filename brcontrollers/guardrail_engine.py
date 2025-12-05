from connectors.mysqldb_engine import MySQLDatabase


class GuardrailEngine:

    def __init__(self):
        self.db = MySQLDatabase()

    # -----------------------------------------------------
    # LOAD ACTIVE RULES
    # -----------------------------------------------------
    def load_rules(self):
        sql = "SELECT * FROM guardrail_rules WHERE is_active = TRUE"
        return self.db.execute_query(sql, fetch=True)

    # -----------------------------------------------------
    # LOAD CONDITIONS FOR A RULE
    # -----------------------------------------------------
    def load_conditions(self, rule_id):
        sql = "SELECT * FROM guardrail_conditions WHERE rule_id = %s"
        return self.db.execute_query(sql, (rule_id,), fetch=True)

    # -----------------------------------------------------
    # LOAD ACTIONS FOR A RULE
    # -----------------------------------------------------
    def load_actions(self, rule_id):
        sql = "SELECT * FROM guardrail_actions WHERE rule_id = %s"
        return self.db.execute_query(sql, (rule_id,), fetch=True)

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
    # DUPLICATE PROCESS CHECK IN DB
    # -----------------------------------------------------
    def check_duplicate_in_db(self, process_name):

        sql = "SELECT * FROM processes WHERE process_name = %s"
        result = self.db.execute_query(sql, (process_name,), fetch=True)

        return len(result) > 0

    # -----------------------------------------------------
    # MAIN EVALUATION METHOD (ONLY CHECK RULES)
    # -----------------------------------------------------
    def evaluate(self, payload):

        rules = self.load_rules()

        for rule in rules:
            rule_id = rule["rule_id"]
            conditions = self.load_conditions(rule_id)

            rule_triggered = True

            for cond in conditions:

                # Duplicate detection special rule
                if cond["condition_key"] == "process_name" and cond["operator"] == "contains":
                    if self.check_duplicate_in_db(payload["process_name"]):
                        rule_triggered = True
                    else:
                        rule_triggered = False

                else:
                    if not self.evaluate_condition(cond, payload):
                        rule_triggered = False

            if rule_triggered:
                actions = self.load_actions(rule_id)
                return self.execute_actions(actions, rule["rule_name"])

        return {
            "allowed": True,
            "message": "All guardrails passed."
        }

    # -----------------------------------------------------
    # EXECUTE RULE ACTIONS
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
            "message": "Rule triggered but not blocking.",
            "rule": rule_name
        }

    # -----------------------------------------------------
    # INSERT PROCESS INTO DB (NEW)
    # -----------------------------------------------------
    def insert_process(self, pname):

        sql = """
            INSERT INTO processes 
            (process_name, description, department, process_owner, frequency, triggers, outcomes)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        data = (pname, "", "", "", "", "", "")
        self.db.execute_query(sql, data)

    # -----------------------------------------------------
    # FINAL METHOD – USED BY UI
    # -----------------------------------------------------
    def submit(self, pname):

        payload = {"process_name": pname}

        # 1. Run guardrails
        result = self.evaluate(payload)

        if not result["allowed"]:
            return {
                "success": False,
                "message": result["message"]
            }

        # 2. Safe → Insert into DB
        try:
            self.insert_process(pname)
            return {
                "success": True,
                "message": "Process saved successfully!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"DB Error: {e}"
            }
