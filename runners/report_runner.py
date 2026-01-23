from services.report_service import ReportService


class ControlReportRunner:

    def generate_control_report(self, test_plan_id):
        svc = ReportService()

        plans = svc.fetch_test_plan_with_control(test_plan_id)
        if not plans:
            return {"error": "Test plan not found"}

        plan = plans[0]
        control_id = plan["control_id"]
        control_name = plan["control_name"]

        steps = svc.fetch_test_steps(test_plan_id)

        control_result = "PASS"
        testing_procedure = []

        for step in steps:
            if step["status"] == "FAIL":
                control_result = "FAIL"

            tasks = svc.fetch_tasks_by_step(step["test_step_id"])

            testing_procedure.append({
                "step": step["control_assertion"],
                "tasks": [
                    {
                        "task_name": t["task_name"],
                        "results": svc.fetch_task_results(t["test_task_id"])
                    }
                    for t in tasks
                ]
            })

        return {
            "test_plan": plan["test_plan_name"],
            "control": control_name,
            "result": control_result,
            "procedures": testing_procedure
        }


    