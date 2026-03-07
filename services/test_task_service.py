from connectors.lambda_mysql import call_lambda
from services.helper import build_lambda_payload_from_query_rawSql

class TestTaskService:

    def execute_tasks(self, test_step):
        """
        Execute all tasks for a test step and collect evidence.
        Returns a list of dicts with keys:
        test_task_id, task_name, status, records_count, reason, evidence
        """
        test_step_id = test_step.get("test_step_id")
        payload = {
            "action": "raw_sql",
            "sql": " SELECT t.*,test_step_id FROM test_tasks t JOIN teststep_testtask_map m ON t.test_task_id = m.test_task_id WHERE m.test_step_id = %s ORDER BY m.execution_order ",
            "params": [test_step_id]   # list is correct
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
                    evidence_payload = build_lambda_payload_from_query_rawSql(evidence_query)
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
                    "evidence": evidence_records,
                    "evidence_records_from_table": r.get("evaluation_rule")   # <-- AI uses this
                })

            return results

        except Exception as e:
            print("❌ Lambda Fetch Error (Test Tasks):", e)
            return []
