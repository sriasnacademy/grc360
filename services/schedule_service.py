from connectors.lambda_mysql import call_lambda


class ScheduleRepository:

    def fetch_test_plans(self):
        """
        Fetch all test plans for the schedule tab combobox.
        Returns a list of dicts: {test_plan_id, test_plan_name}
        """
        payload = {
            "action": "raw_sql",
            "sql": "SELECT test_plan_id AS test_plan_id, test_plan_name FROM test_plan ORDER BY test_plan_name",
            "params": []
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])

            plans = []
            for r in records:
                plans.append({
                    "test_plan_id":   r.get("test_plan_id"),
                    "test_plan_name": r.get("test_plan_name")
                })

            return plans

        except Exception as e:
            print("❌ Lambda Fetch Error (Test Plans):", e)
            return []

    def insert_schedule(self, test_plan_id: int, utc_datetime: str, recurrence: str):
        """
        Insert a new PENDING schedule row.
        utc_datetime : 'YYYY-MM-DD HH:MM:SS'  (already converted from IST)
        Returns the new row id or None on failure.
        """
        payload = {
            "action": "raw_sql",
            "sql": """
                INSERT INTO test_plan_scheduling
                    (test_plan_id, status, scheduled_datetime, recurrence)
                VALUES (%s, 'PENDING', %s, %s)
            """,
            "params": [test_plan_id, utc_datetime, recurrence]
        }

        try:
            response = call_lambda(payload)
            return response.get("last_insert_id")

        except Exception as e:
            print("❌ Lambda Insert Error (Schedule):", e)
            return None