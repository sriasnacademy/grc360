from connectors.lambda_mysql import call_lambda

class TestStepService:

    def fetch_test_steps(self, test_plan_id):
        """
        Fetch all active test steps for a given test plan.
        Returns a list of dictionaries with keys:
        test_step_id, control_assertion, assertion_description, control_area, risk_type, status
        """

        payload = {
            "action": "raw_sql",
            "sql": "SELECT ts.test_step_id, ts.control_assertion,ts.assertion_description,ts.control_area,ts.risk_type,ts.status FROM test_steps ts join testplan_teststep_map tptsmp on ts.test_step_id = tptsmp.test_step_id WHERE tptsmp.test_plan_id = %s AND status = 'ACTIVE' ORDER BY tptsmp.step_order",
            "params": [test_plan_id]
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
