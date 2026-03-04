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

    def fetch_schedules(self, status=None) -> list:
        """
        Fetch all schedule rows joined with test plan name for the report panel.
        Optionally filter by status e.g. 'PENDING', 'COMPLETED', etc.
        Returns a list of dicts.
        """
        if status:
            sql = """
                SELECT
                    s.id,
                    s.test_plan_id,
                    COALESCE(tp.test_plan_name, CONCAT('Plan #', s.test_plan_id)) AS test_plan_name,
                    s.scheduled_datetime,
                    s.recurrence,
                    s.status,
                    s.created_at
                FROM test_plan_scheduling s
                LEFT JOIN test_plan tp ON tp.test_plan_id = s.test_plan_id
                WHERE s.status = %s
                ORDER BY s.scheduled_datetime DESC
            """
            params = [status]
        else:
            sql = """
                SELECT
                    s.id,
                    s.test_plan_id,
                    COALESCE(tp.test_plan_name, CONCAT('Plan #', s.test_plan_id)) AS test_plan_name,
                    s.scheduled_datetime,
                    s.recurrence,
                    s.status,
                    s.created_at
                FROM test_plan_scheduling s
                LEFT JOIN test_plan tp ON tp.test_plan_id = s.test_plan_id
                ORDER BY s.scheduled_datetime DESC
            """
            params = []

        payload = {
            "action": "raw_sql",
            "sql": sql,
            "params": params
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])

            schedules = []
            for r in records:
                schedules.append({
                    "id":                 r.get("id"),
                    "test_plan_id":       r.get("test_plan_id"),
                    "test_plan_name":     r.get("test_plan_name"),
                    "scheduled_datetime": str(r.get("scheduled_datetime", "")),
                    "recurrence":         r.get("recurrence"),
                    "status":             r.get("status"),
                    "created_at":         str(r.get("created_at", "")),
                })

            return schedules

        except Exception as e:
            print("❌ Lambda Fetch Error (Schedules):", e)
            raise

    def delete_schedule(self, schedule_id: int):
        """
        Hard-delete a schedule row by its primary key.
        """
        payload = {
            "action": "raw_sql",
            "sql": "DELETE FROM test_plan_scheduling WHERE id = %s",
            "params": [schedule_id]
        }

        try:
            call_lambda(payload)

        except Exception as e:
            print("❌ Lambda Delete Error (Schedule):", e)
            raise

    def update_schedule_status(self, schedule_id: int, status: str):
        """
        Update the status column of a schedule row.
        e.g. status = 'CANCELLED'
        """
        payload = {
            "action": "raw_sql",
            "sql": "UPDATE test_plan_scheduling SET status = %s WHERE id = %s",
            "params": [status, schedule_id]
        }

        try:
            call_lambda(payload)

        except Exception as e:
            print("❌ Lambda Update Error (Schedule Status):", e)
            raise