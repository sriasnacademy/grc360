from connectors.lambda_mysql import call_lambda

class TestStepService:

    def fetch_test_steps(self, test_plan_id):
        """
        Fetch all active test steps for a given test plan.
        Returns a list of dictionaries with keys:
        test_step_id, control_assertion, assertion_description, control_area, risk_type, status
        """

        payload = {
            "action": "select",
            "table": "test_steps",  # ✅ required for Lambda
            "columns": [
                "test_step_id",
                "control_assertion",
                "assertion_description",
                "control_area",
                "risk_type",
                "status"
            ],
            "where": {
                "test_plan_id": test_plan_id,
                "status": "ACTIVE"
            },
            "order_by": "step_order"
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])

            steps = []
            for r in records:
                steps.append({
                    "test_step_id": r.get("test_step_id"),
                    "control_assertion": r.get("control_assertion"),  # this is step_name in GUI
                    "control_area": r.get("control_area"),
                    "risk_type": r.get("risk_type"),
                    "status": r.get("status", "ACTIVE")
            })

            return steps

        except Exception as e:
            print("❌ Lambda Fetch Error (Test Steps):", e)
        return []
