from connectors.lambda_mysql import call_lambda

class WorkflowInstanceManager:
    
    def get_eventid_for_event(self, event_name):
        payload = {
            "action": "raw_sql",
            "sql": "SELECT e.event_name, e.event_id from event_registry WHERE e.event_name = %s AND e.active = 1;",
            "params": [event_name]
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])# Query workflow_master where trigger_event = event_code
            return records.get("event_id")
            
        except Exception as e:
            print("❌ Lambda Fetch Error (Test Steps):", e)
        return []
    
    def load_event_log(self, event_log_payload):
        payload = {
            "action": "raw_sql",
            "sql": "INSERT INTO `event_log`(`event_id`,`reference_id`,`payload`,`status`,`created_at`)VALUES(%s,%s,%s,%s,now())",
            "params": [event_log_payload["event_id"],event_log_payload["reference_id"],self.get_eventid_for_event["payload"],"PENDING"]
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])# Query workflow_master where trigger_event = event_code
            return records
            
        except Exception as e:
            print("❌ Lambda Fetch Error (Test Steps):", e)
        return []


    def get_workflow_by_event(self, event_id):
        payload = {
            "action": "raw_sql",
            "sql": "SELECT e.event_id, e.event_name, w.workflow_id,w.workflow_name FROM event_registry e JOIN event_subscriptions s ON e.event_id = s.event_id JOIN workflow_definitions w ON s.workflow_id = w.workflow_id WHERE e.event_name = %s AND s.active = 1 AND w.active = 1",
            "params": [event_id]
        }

        try:
            response = call_lambda(payload)
            records = response.get("records", [])# Query workflow_master where trigger_event = event_code
            return records
            
        except Exception as e:
            print("❌ Lambda Fetch Error (Test Steps):", e)
        return []


    def create_instance(self, workflow_id, entity_id):
        # Insert into workflow_instance
        print("Creating workflow instance")
        return 1

    def activate_first_step(self, instance_id, workflow_id):
        # Fetch first step and insert into workflow_instance_step
        print("Activating first step")
