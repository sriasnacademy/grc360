from connectors.lambda_mysql import call_lambda
from services.helper import build_lambda_payload_from_query

class TestTaskService:

    def execute_tasks(self, test_step):
        """
        Execute all tasks for a test step and collect evidence.
        Returns a list of dicts with keys:
        test_task_id, task_name, status, records_count, reason, evidence
        """
        payload = {
            "action": "select",
            "table": "test_tasks",
            "columns": [
                "test_task_id",
                "task_name",
                "evidence_query",
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
                test_task_id = r.get("test_task_id")
                task_name = r.get("task_name")
                evidence_query = r.get("evidence_query")

                if not evidence_query:
                    results.append({
                        "test_task_id": test_task_id,
                        "task_name": task_name,
                        "status": "EXECUTED",
                        "records_count": 0,
                        "reason": "No evidence query",
                        "evidence": []
                    })
                    continue

                # Build Lambda payload
                try:
                    evidence_payload = build_lambda_payload_from_query(evidence_query)
                except Exception as e:
                    results.append({
                        "test_task_id": test_task_id,
                        "task_name": task_name,
                        "status": "EXECUTED",
                        "records_count": 0,
                        "reason": f"Query decode failed: {e}",
                        "evidence": []
                    })
                    continue

                # Execute query
                evidence_response = call_lambda(evidence_payload)
                evidence_records = evidence_response.get("records", [])

                results.append({
                    "test_task_id": test_task_id,
                    "task_name": task_name,
                    "status": "EXECUTED",
                    "records_count": len(evidence_records),
                    "reason": "Evidence collected" if evidence_records else "No records returned",
                    "evidence": evidence_records
                })

            return results

        except Exception as e:
            print("❌ Lambda Fetch Error (Test Tasks):", e)
            return []
