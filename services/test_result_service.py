# services/test_result_service.py

from connectors.lambda_mysql import call_lambda
from datetime import datetime

class TestResultService:

    def store_step_results(self, evaluated_step, step, test_plan_id, control_id):

        # 🔥 Persist step result
        call_lambda({
            "action": "insert",
            "table": "test_step_results",
            "data": {
                "test_plan_id": test_plan_id,
                "test_step_id": step["test_step_id"],
                "control_id": control_id,
                "status": evaluated_step["status"],
                "reason": evaluated_step["reason"],
                "executed_at": datetime.now().isoformat()
            }
        })

        # 🔥 Persist task results
        for task in evaluated_step["tasks"]:
            call_lambda({
                "action": "insert",
                "table": "test_task_results",
                "data": {
                    "test_task_id": task["test_task_id"],
                    "test_step_id": step["test_step_id"],
                    "test_plan_id": test_plan_id,
                    "control_id": control_id,
                    "evidence_payload": str(task.get("evidence")),
                    "evidence_result": task["reason"],
                    "executed_at": datetime.now().isoformat()
                }
            })
