import re
from connectors.lambda_mysql import call_lambda

class InputSanitizer:

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Cleans and normalizes user input
        """

        if not text:
            return ""

        # Remove HTML / script tags
        text = re.sub(r'<.*?>', '', text)

        # Remove SQL comments
        text = re.sub(r'--.*', '', text)

        # Allow only letters, numbers and space
        text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Normalize case
        return text.title()
    
class GuardrailEngine:

    # -------------------------------
    # DUPLICATE PROCESS CHECK
    # -------------------------------
    def check_duplicate_process(self, process_name):

        #sql = "SELECT process_id FROM processes WHERE process_name = %s"
        payload = {
            "action": "select",
            "table": "processes",
            "where": {"process_name: %s"}
        }

        result = call_lambda(payload)   # ✅ FUNCTION CALL
        return result.get("records", [])

    # -------------------------------
    # MAIN GUARDRAIL EVALUATION
    # -------------------------------
    def evaluate(self, payload):

        # 1️⃣ SANITIZATION GUARDRAIL
        if "process_name" in payload:
            payload["process_name"] = InputSanitizer.sanitize_text(
                payload["process_name"]
            )

        # 2️⃣ DUPLICATE PROCESS GUARDRAIL
        if self.check_duplicate_process(payload["process_name"]):
            return {
                "allowed": False,
                "message": "Duplicate process detected. Process already exists.",
                "sanitized_payload": payload
            }

        # 3️⃣ ALL GUARDRAILS PASSED
        return {
            "allowed": True,
            "message": "All guardrails passed.",
            "sanitized_payload": payload
        }
