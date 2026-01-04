from services.test_step_service import TestStepService
from services.test_task_service import TestTaskService
from engine.ai_evaluator import AIEvaluator

class ManualRunner:

    def run(self, test_plan_id):
        step_service = TestStepService()
        task_service = TestTaskService()
        evaluator = AIEvaluator()

        steps = step_service.fetch_test_steps(test_plan_id)
        all_results = []

        for step in steps:
            test_step_id = step["test_step_id"]
            step_name = step.get("control_assertion")

            tasks = task_service.execute_tasks(step)

            step_result = {
                "test_step_id": test_step_id,
                "step_name": step_name,
                "tasks": tasks
            }

            # AI evaluates the step
            step_result = evaluator.evaluate_test_step(step_result)
            all_results.append(step_result)

        return all_results
