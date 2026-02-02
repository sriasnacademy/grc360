from services.report_service import ReportService


class ControlReportRunner:

    def generate_control_report(self, test_plan_id):

        svc = ReportService()

        plan = svc.fetch_test_plan_with_control(test_plan_id)[0]

        steps = svc.fetch_test_steps(test_plan_id)

        control_result = "PASS"
        procedures = []

        for step in steps:

            if step["status"] == "FAIL":
                control_result = "FAIL"

            tasks = svc.fetch_executed_tasks(
                test_plan_id,
                step["test_step_id"]
            )

            procedures.append({
                "step": step["step_name"],
                "status": step["status"],
                "reason": step["reason"],
                "tasks": tasks
            })

        return {
            "test_plan": plan["test_plan_name"],
            "control": plan["control_name"],
            "result": control_result,
            "procedures": procedures
        }
