from connectors.lambda_mysql import call_lambda

class GetDataFromMySql:

    def get_processes(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from processes"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []
    
    def get_risks(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from risk"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []
        
    def get_subprocesses(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from sub_processes"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []
        
    def get_controls(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from control"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []
    
    def get_testplan(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from test_plan"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []
    
    def get_teststeps(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from test_steps"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []
    
    def get_testtasks(self):
        payload = {
            "action": "raw_sql",
            "sql":"Select * from test_tasks"
        }

        try:
            response = call_lambda(payload)

            records = response.get("records", [])
            return records
        
        except Exception as e:
            print("❌ Lambda Fetch Error:", e)
            return []