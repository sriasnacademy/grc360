from connectors.lambda_mysql import call_lambda


class ReportService:

    def fetch_executable_test_plans(self):
        return call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT
                    tp.test_plan_id,
                    tp.test_plan_name,

                    MIN(c.control_name) AS control_name,
                    MIN(r.risk_name) AS risk_name,

                    COALESCE(
                        MIN(p.process_name),
                        MIN(sp.sub_process_name)
                    ) AS process_name

                FROM test_plan tp

                JOIN testplan_teststep_map ttsm
                    ON tp.test_plan_id = ttsm.test_plan_id
                    AND ttsm.Active = 1

                JOIN test_steps ts
                    ON ttsm.test_step_id = ts.test_step_id
                    AND ts.status = 'ACTIVE'

                JOIN test_plan_control_map tpcm
                    ON tp.test_plan_id = tpcm.test_plan_id

                JOIN control c
                    ON tpcm.control_id = c.control_id

                JOIN risk_control_map rcm
                    ON c.control_id = rcm.control_id

                JOIN risk r
                    ON rcm.risk_id = r.risk_id

                JOIN process_subprocess_risk_map psrm
                    ON r.risk_id = psrm.risk_id
                    AND psrm.status = 'ACTIVE'

                LEFT JOIN processes p
                    ON psrm.pro_subpro_type = 'PROCESS'
                    AND psrm.pro_subpro_id = p.process_id

                LEFT JOIN sub_processes sp
                    ON psrm.pro_subpro_type = 'SUB_PROCESS'
                    AND psrm.pro_subpro_id = sp.sub_process_id

                GROUP BY
                    tp.test_plan_id,
                    tp.test_plan_name

                ORDER BY tp.test_plan_name
            """
        }).get("records", [])


    # -----------------------------
    # Test Plan
    # -----------------------------
    def fetch_test_plan(self, test_plan_id):
        return call_lambda({
            "action": "select",
            "table": "test_plan",
            "columns": ["test_plan_id", "test_plan_name"],
            "where": {"test_plan_id": test_plan_id}
        }).get("records", [])


    def fetch_all_test_plans(self):
        return call_lambda({
            "action": "select",
            "table": "test_plan",
            "columns": ["test_plan_id", "test_plan_name"]
        }).get("records", [])
        
    # -----------------------------
    # Test Steps
    # -----------------------------
    def fetch_test_steps(self, test_plan_id):
        return call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT 
                    tsr.test_step_id,
                    ts.control_assertion,
                    tsr.status,
                    tsr.reason
                FROM test_step_results tsr
                JOIN test_steps ts 
                    ON ts.test_step_id = tsr.test_step_id
                WHERE tsr.test_plan_id = %s
                ORDER BY tsr.executed_at
            """,
            "params": [test_plan_id]
        }).get("records", [])

    
    def fetch_executed_tasks(self, test_plan_id):
        return call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT 
                    tsr.test_step_id,
                    ts.control_assertion,
                    tsr.status,
                    tsr.reason
                FROM test_step_results tsr
                JOIN test_steps ts 
                    ON ts.test_step_id = tsr.test_step_id
                WHERE tsr.test_plan_id = %s
                ORDER BY tsr.executed_at
            """,
            "params": [test_plan_id]
        }).get("records", [])

    # -----------------------------
    # Test Tasks (Runner-compatible name)
    # -----------------------------
    def fetch_tasks_by_step(self, test_step_id):
        return call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT
                    tt.test_task_id,
                    tt.task_name,
                    tsttmp.execution_order
                FROM test_tasks tt
                JOIN teststep_testtask_map tsttmp
                    ON tt.test_task_id = tsttmp.test_task_id
                WHERE tsttmp.test_step_id = %s
            """,
            "params": [test_step_id]
        }).get("records", [])
        
        
    def fetch_test_plan_with_control(self, test_plan_id):
        return call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT
                    tp.test_plan_id,
                    tp.test_plan_name,
                    c.control_id,
                    c.control_name
                FROM test_plan tp
                JOIN test_plan_control_map tpcm
                    ON tp.test_plan_id = tpcm.test_plan_id
                JOIN control c
                    ON tpcm.control_id = c.control_id
                WHERE tp.test_plan_id = %s
            """,
            "params": [test_plan_id]
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
