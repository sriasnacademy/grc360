from services.report_service import ReportService


class ControlReportRunner:

    def generate_control_report(self, test_plan_id):
        svc = ReportService()

        # -----------------------------
        # Test Plan
        # -----------------------------
        plans = svc.fetch_test_plan(test_plan_id)
        if not plans:
            return {"error": "Test plan not found"}

        plan = plans[0]
        control_id = plan.get("control_id")

        # -----------------------------
        # Control
        # -----------------------------
        control_rows = svc.fetch_control(control_id) if control_id else []
        control_name = (
            control_rows[0]["control_name"]
            if control_rows
            else f"UNMAPPED CONTROL ({control_id})"
        )

        # -----------------------------
        # Test Steps
        # -----------------------------
        steps = svc.fetch_test_steps(test_plan_id)

        control_result = "PASS"
        testing_procedure = []

        for step in steps:
            step_status = step["status"]

            if step_status == "FAIL":
                control_result = "FAIL"

            # -----------------------------
            # Tasks per Step
            # -----------------------------
            tasks = svc.fetch_tasks_by_step(step["test_step_id"])

            for task in tasks:
                results = svc.fetch_task_results(task["test_task_id"])

                testing_procedure.append({
                    "task_name": task["task_name"],
                    "results": [
                        {
                            "evidence_result": r["evidence_result"],
                            "executed_at": r["executed_at"]
                        }
                        for r in results
                    ]
                })

        # -----------------------------
        # Process Impact
        # -----------------------------
        process_ids = (
            svc.fetch_processes_by_control(control_id)
            if control_id else []
        )

        # -----------------------------
        # Final Report
        # -----------------------------
        return {
            "test_plan": plan["test_plan_name"],
            "controls": [
                {
                    "control_name": control_name,
                    "assertion": "See test steps below",
                    "result": control_result,
                    "testing_procedure": testing_procedure,
                    "process_impact": process_ids
                }
            ]
        }
