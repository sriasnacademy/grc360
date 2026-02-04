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
        evaluator = AIEvaluator()

        plan = report_svc.fetch_test_plan_with_control(test_plan_id)[0]

        control_failed = False
        failed_task_ids = []

        # =====================================================
        # EXECUTE EACH STEP
        # =====================================================
        for step in step_svc.fetch_test_steps(test_plan_id):

            # 1️⃣ Execute tasks (LIST)
            tasks = task_svc.execute_tasks(step)

            # 2️⃣ Evaluate tasks + derive step status
            evaluated = evaluator.evaluate_step(
                step["control_assertion"],
                tasks
            )

            # 3️⃣ Persist task results
            result_svc.store_task_results(
                evaluated["tasks"],
                test_plan_id,
                plan["control_id"]
            )

            # 4️⃣ Track failures
            if evaluated["status"] == "FAIL":
                control_failed = True

                for task in evaluated["tasks"]:
                    if task["status"] == "FAIL":
                        failed_task_ids.append(task["test_task_id"])
                    # =====================================================
                    # RAISE ISSUE ONCE PER CONTROL
                    # =====================================================
                    if control_failed:
                        issue_svc.raise_control_failure(
                            task_id=task["test_task_id"],
                            control_id=plan["control_id"],
                            test_plan_id=test_plan_id,
                        )
      
        # =====================================================
        # GENERATE REPORT FROM DB
        # =====================================================
        return ControlReportRunner().generate_control_report(test_plan_id)
