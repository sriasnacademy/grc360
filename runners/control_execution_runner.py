from services.test_step_service import TestStepService
from services.test_task_service import TestTaskService
from services.test_result_service import TestResultService
from services.issue_service import IssueService
from services.report_service import ReportService
from engine.ai_evaluator import AIEvaluator
from runners.report_runner import ControlReportRunner
from workflow.engine import WorkflowEngine
from workflow.event_dispatcher import WorkflowEventDispatcher
from connectors.lambda_mysql import call_lambda


class ControlExecutionRunner:

    def execute_test_plan(self, test_plan_id):

        step_svc = TestStepService()
        task_svc = TestTaskService()
        result_svc = TestResultService()
        issue_svc = IssueService()
        report_svc = ReportService()
        evaluator = AIEvaluator()

        plan = report_svc.fetch_test_plan_with_control(test_plan_id)[0]

        failed_task_ids = []
        
        cycle_id, cycle_number = self.start_new_cycle(test_plan_id)

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
                plan["control_id"],
                cycle_number
            )
            
            

            # 4️⃣ Track failures
            if evaluated["status"] == "FAIL":
                for task in evaluated["tasks"]:
                    if task["status"] == "FAIL":
                        failed_task_ids.append(task["test_task_id"])
                    # =====================================================
                    # RAISE ISSUE ONCE PER CONTROL
                    # =====================================================
                    if failed_task_ids:
                        issue_result = issue_svc.raise_control_failure(
                            task_id=task["test_task_id"],
                            control_id=plan["control_id"],
                            test_plan_id=test_plan_id,
                            test_step_id = task["test_step_id"]
                        )
                        
                        engine = WorkflowEngine()
                        dispatcher = WorkflowEventDispatcher(engine)

                        dispatcher.raise_event(
                            event_name="ISSUE_CREATED",
                            payload={
                                "reference_id": issue_result["issue_id"],
                                "module_name": "ISSUE",          # ✅ Add this
                                "performed_by": "SYSTEM",    # ✅ Add this (whatever your user variable is)
                                "payload_for_eventlog": issue_result["issue_payload"]
                            }
                        )
      
        # =====================================================
        # GENERATE REPORT FROM DB
        # =====================================================
        return ControlReportRunner().generate_control_report(test_plan_id)

    def start_new_cycle(self,test_plan_id):
        # Get next cycle number
        results = call_lambda({
            "action": "raw_sql",
            "sql": "SELECT COUNT(*) FROM test_cycle WHERE test_plan_id = %s",
            "params": [test_plan_id]   # list is correct
        })
        records = results.get("records",[])
        cycle_number = records[0]["COUNT(*)"] + 1

        # Insert new cycle
        test_cycle_results = call_lambda({
            "action": "raw_sql",
            "sql": " INSERT INTO `test_cycle`(`test_plan_id`,`cycle_number`,`run_by`,`run_at`,`active`)VALUES (%s,%s,%s,now(),1)",
            "params": [test_plan_id,cycle_number,"siri"]   # list is correct
        })
        cycle_id = test_cycle_results.get("inserted_id")
        return cycle_id, cycle_number
