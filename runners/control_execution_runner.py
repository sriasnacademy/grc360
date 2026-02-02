from services.test_step_service import TestStepService
from services.test_task_service import TestTaskService
from services.test_result_service import TestResultService
from services.issue_service import IssueService
from services.report_service import ReportService
from engine.ai_evaluator import AIEvaluator
from runners.report_runner import ControlReportRunner


class ControlExecutionRunner:

    def execute_test_plan(self, test_plan_id):

        step_svc = TestStepService()
        task_svc = TestTaskService()
        result_svc = TestResultService()
        issue_svc = IssueService()
        report_svc = ReportService()
        ai = AIEvaluator()
        report_run = ControlReportRunner()

        plans = report_svc.fetch_test_plan_with_control(test_plan_id)
        if not plans:
            return {"error": "Test plan not found"}

        plan = plans[0]
        control_failed = False

        steps = step_svc.fetch_test_steps(test_plan_id)

        for step in steps:

            # 🔥 EXECUTE tasks
            executed_tasks = task_svc.execute_tasks(step)

            step_payload = {
                "step_name": step["control_assertion"],
                "tasks": executed_tasks
            }

            # 🔥 AI evaluation
            evaluated = ai.evaluate_test_step(step_payload)

            # 🔥 Persist execution
            result_svc.store_step_results(
                evaluated,
                step,
                test_plan_id,
                plan["control_id"]
            )

            if evaluated["status"] == "FAIL":
                control_failed = True

        # 🔥 Trigger issue
        if control_failed:
            issue_svc.raise_control_failure(
                test_plan_id,
                plan["control_id"]
            )

        # 🔥 Generate report from persisted data
        return report_run.generate_control_report(test_plan_id)
