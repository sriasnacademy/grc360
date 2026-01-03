
from connectors.lambda_mysql import call_lambda

class EvidenceExecutor:

    def execute_query(self, query):
        payload = {
            "action": "raw_query",
            "query": query
        }

        response = call_lambda(payload)
        records = response.get("records", [])

        if records:
            return list(records[0].values())[0]

        return None
