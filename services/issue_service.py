from connectors.lambda_mysql import call_lambda
from datetime import datetime

class IssueService:
    def raise_control_failure(self, task_id, control_id,test_plan_id,test_step_id,test_cycle_num):

        payload =  {
                "test_task_id":task_id,
                "control_id": control_id,
                "test_plan_id": test_plan_id,
                "test_step_id":test_step_id,
                "issue_type": "CONTROL_FAILURE",
                "status": "OPEN",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        result = call_lambda({
            "action": "insert",
            "table": "issues",
            "data": {
                "test_task_id":task_id,
                "test_cycle_number":test_cycle_num,
                "control_id": control_id,
                "test_plan_id": test_plan_id,
                "test_step_id":test_step_id,
                "issue_type": "CONTROL_FAILURE",
                "status": "OPEN",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        })

        issue_id = result.get("inserted_id")

        result_payload = {"issue_id": issue_id,
                          "issue_payload":payload}
        return result_payload
