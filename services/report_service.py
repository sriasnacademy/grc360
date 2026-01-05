from connectors.lambda_mysql import call_lambda


class ReportService:

    # -----------------------------
    # Test Plan
    # -----------------------------
    def fetch_test_plan(self, test_plan_id):
        return call_lambda({
            "action": "select",
            "table": "test_plan",
            "columns": ["test_plan_id", "control_id", "test_plan_name"],
            "where": {"test_plan_id": test_plan_id}
        }).get("records", [])


    # -----------------------------
    # Test Steps
    # -----------------------------
    def fetch_test_steps(self, test_plan_id):
        return call_lambda({
            "action": "select",
            "table": "test_steps",
            "columns": [
                "test_step_id",
                "control_assertion",
                "status",
            ],
            "where": {"test_plan_id": test_plan_id}
        }).get("records", [])


    # -----------------------------
    # Test Tasks (Runner-compatible name)
    # -----------------------------
    def fetch_tasks_by_step(self, test_step_id):
        return call_lambda({
            "action": "select",
            "table": "test_tasks",
            "columns": [
                "test_task_id",
                "task_name"
            ],
            "where": {"test_step_id": test_step_id}
        }).get("records", [])


    # -----------------------------
    # Task Results (Evidence)
    # -----------------------------
    def fetch_task_results(self, test_task_id):
        return call_lambda({
            "action": "select",
            "table": "test_task_results",
            "columns": [
                "evidence_payload",
                "evidence_result",
                "executed_at"
            ],
            "where": {"test_task_id": test_task_id}
        }).get("records", [])


    # -----------------------------
    # Control
    # -----------------------------
    def fetch_control(self, control_id):
        return call_lambda({
            "action": "select",
            "table": "control",
            "columns": [
                "control_id",
                "control_name"
            ],
            "where": {"control_id": control_id}
        }).get("records", [])


    # -----------------------------
    # Process impact via Risk
    # Control → Risk → Process
    # -----------------------------
    def fetch_processes_by_control(self, control_id):

        processes = set()

        # Step 1: Get risks for control
        risks = call_lambda({
            "action": "select",
            "table": "risk_control_map",
            "columns": ["risk_id"],
            "where": {"control_id": control_id}
        }).get("records", [])

        # Step 2: For each risk, get processes
        for r in risks:
            risk_id = r["risk_id"]

            rows = call_lambda({
                "action": "select",
                "table": "process_risk_map",
                "columns": ["process_id"],
                "where": {"risk_id": risk_id}
            }).get("records", [])

            for p in rows:
                processes.add(p["process_id"])

        return list(processes)
