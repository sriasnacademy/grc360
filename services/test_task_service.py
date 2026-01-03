from connectors.lambda_mysql import call_lambda
from services.helper import build_lambda_payload_from_query

class TestTaskService:

    def execute_tasks(self, test_step):

        payload = {
            "action": "select",
            "table": "test_tasks",
            "columns": [
                "test_task_id",
                "task_name",
                "evidence_query",
                "expected_condition",
                "evaluation_rule",
                "status"
            ],
            "where": {
                "test_step_id": test_step.get("test_step_id"),
                "status": "ACTIVE"
            },
            "order_by": "execution_order"
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])
            results = []

            for r in records:
                task_name = r.get("task_name")
                evaluation_rule = r.get("evaluation_rule")
                evidence_query = r.get("evidence_query")

                if not evidence_query:
                    results.append({
                        "task_name": task_name,
                        "value": None,
                        "status": "FAIL",
                        "reason": "Evidence query empty"
                    })
                    continue

                # 🔹 Decode string → Lambda payload
                try:
                    evidence_payload = build_lambda_payload_from_query(evidence_query)
                except Exception as e:
                    results.append({
                        "task_name": task_name,
                        "value": None,
                        "status": "FAIL",
                        "reason": f"Query decode failed: {str(e)}"
                    })
                    continue

                # 🔹 Execute evidence query
                evidence_response = call_lambda(evidence_payload)
                evidence_records = evidence_response.get("records", [])

                value = list(evidence_records[0].values())[0] if evidence_records else 0

                status = "PASS" if str(evaluation_rule) in str(value) else "FAIL"
                reason = "Condition satisfied" if status == "PASS" else "Condition violated"

                results.append({
                    "task_name": task_name,
                    "value": value,
                    "status": status,
                    "reason": reason
                })

            return results

        except Exception as e:
            print("❌ Lambda Fetch Error (Test Tasks):", e)
            return []
