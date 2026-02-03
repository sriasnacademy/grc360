from connectors.lambda_mysql import call_lambda
from datetime import datetime

class IssueService:

    def raise_control_failure(self, task_id, test_plan_id, control_id):

        call_lambda({
            "action": "insert",
            "table": "issues",
            "data": {
                "test_task_id":task_id,
                "control_id": control_id,
                "test_plan_id": test_plan_id,
                "issue_type": "CONTROL_FAILURE",
                "status": "OPEN",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        })
