from datetime import datetime
from connectors.lambda_mysql import call_lambda


class TestResultService:

    def store_task_results(
        self,
        evaluated_tasks: list,
        test_plan_id: int,
        control_id: int,
        cycle_number
    ):
        for task in evaluated_tasks:
            call_lambda({
                "action": "insert",
                "table": "test_task_results",
                "data": {
                    "test_step_id": task["test_step_id"],
                    "test_task_id": task["test_task_id"],
                    "test_plan_id": test_plan_id,
                    "cycle_number":cycle_number,
                    "control_id": control_id,
                    "evidence_payload": str(task.get("evidence", [])),
                    "evidence_result": task["reason"],
                    "status": task["status"],
                    "evaluation_source": task["evaluation_source"],
                    "executed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                }
            })
