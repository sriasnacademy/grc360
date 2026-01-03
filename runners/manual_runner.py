from services.test_step_service import TestStepService
from services.test_task_service import TestTaskService
from engine.evidence_executor import EvidenceExecutor
from engine.ai_evaluator import AIEvaluator

class ManualRunner:

    def run(self, test_plan_id):
        step_service = TestStepService()
        task_service = TestTaskService()
        executor = EvidenceExecutor()
        evaluator = AIEvaluator()

        step = step_service.fetch_test_steps(test_plan_id)
        if not step:
            return {"error": "No test step found"}

        test_step_id, step_name = step

        results = {
            "step_name": step_name,
            "tasks": []
        }

        tasks = task_service.execute_tasks(test_step_id)

        for task in tasks:
            task_id, name, query, rule, expected = task

            value = executor.execute_query(query)
            status, reason = evaluator.evaluate(value, rule)

            results["tasks"].append({
                "task_name": name,
                "value": value,
                "status": status,
                "reason": reason
            })

        return results
