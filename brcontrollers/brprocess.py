from connectors.lambda_mysql import call_lambda

class GetProcess:

    def fetch_all_processes(self):
        """
        Returns list of tuples exactly as DB used to return
        (process_id, process_name, description, department, owner, frequency, triggers, outcomes)
        """

        payload = {
            "action": "select",
            "table": "processes",
            "columns": [
                "process_id", "process_name", "description", "department",
                "process_owner", "frequency", "triggers", "outcomes"
            ]
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])

            # Convert dict rows to tuples like DB
            rows = [
                (
                    r.get("process_id"),
                    r.get("process_name"),
                    r.get("description"),
                    r.get("department"),
                    r.get("process_owner"),
                    r.get("frequency"),
                    r.get("triggers"),
                    r.get("outcomes")
                )
                for r in records
            ]

            return rows

        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []