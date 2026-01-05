from models.my_llm_client import LLMClient

class AIEvaluator:

    def __init__(self):
        self.llm = LLMClient()

    def evaluate_test_step(self, test_step_result):
        """
        Evaluate a test step using LLM and store concise PASS/FAIL reason.
        """
        step_name = test_step_result.get("step_name")
        tasks = test_step_result.get("tasks", [])

        prompt = f"Test Step: {step_name}\nFor each task, review the evidence and determine if the test step should PASS or FAIL.\n"
        for task in tasks:
            evidence = task.get("evidence", [])
            evidence_str = "\n".join([str(r) for r in evidence]) if evidence else "No records"
            prompt += f"\nTask: {task['task_name']}\nEvidence:\n{evidence_str}\n"

        prompt += "\nQuestion: Based on this evidence, should this test step PASS or FAIL? Give a concise reason."

        llm_output = self.llm.generate(prompt)

        # Extract first meaningful line as concise reason
        reason_lines = [line.strip() for line in llm_output.splitlines() if line.strip()]
        concise_reason = reason_lines[0] if reason_lines else "Evaluation completed"

        # Determine overall step status
        step_status = "FAIL" if "FAIL" in concise_reason.upper() else "PASS"
        test_step_result["status"] = step_status
        test_step_result["reason"] = concise_reason

        # Update all tasks with same concise reason
        for task in tasks:
            task["reason"] = concise_reason

        return test_step_result
