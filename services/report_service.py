from connectors.lambda_mysql import call_lambda


class ReportService:

    def fetch_executed_tasks(self, test_plan_id):
        return call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT
                    t.task_name,
                    r.status,
                    r.evidence_result,
                    r.executed_at
                FROM test_task_results r
                JOIN test_tasks t ON t.test_task_id = r.test_task_id
                WHERE r.test_plan_id = %s
                ORDER BY r.executed_at
            """,
            "params": [test_plan_id]
        }).get("records", [])
    
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
