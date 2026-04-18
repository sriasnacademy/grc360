from services.report_service import ReportService
# path: runners/report_runner.py


class ControlReportRunner:

    '''
    Docstring for ControlReportRunner
    
    def generate_control_report(self, test_plan_id):
        svc = ReportService()
        tasks = svc.fetch_executed_tasks(test_plan_id)

        control_result = "PASS"
        for t in tasks:
            if t["status"] == "FAIL":
                control_result = "FAIL"
                break

        return {
            "test_plan": test_plan_id,
            "result": control_result,
            "tasks": tasks
        }
    '''
    def generate_control_report(self, test_plan_id):

        svc = ReportService()

        plan = svc.fetch_test_plan_with_control(test_plan_id)[0]
        
        control_result = "PASS"
        tasks = svc.fetch_executed_tasks(
                test_plan_id
            )

        for t in tasks:

            if t["status"] == "FAIL":
                control_result = "FAIL"

        return {
            "test_plan": plan["test_plan_name"],
            "control": plan["control_name"],
            "result": control_result,
            "tasks": tasks
        }
