class ReportFormatter:

    def format(self, rows):
        report = {}
        
        for r in rows:
            process = r["process_name"]
            risk = r["risk_name"]
            control = r["control_name"]
            test_plan = r["test_plan_name"]

            report.setdefault(process, {}) \
                  .setdefault(risk, {}) \
                  .setdefault(control, {
                      "test_plan": test_plan,
                      "steps": {}
                  })

            step = report[process][risk][control]["steps"]
            step.setdefault(r["control_assertion"], []).append({
                "task_name": r["task_name"],
                "evidence": r["evidence_result"],
                "executed_at": r["executed_at"]
            })

        return report
