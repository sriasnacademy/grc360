from connectors.lambda_mysql import call_lambda
import json


class WorkflowInstanceManager:

    # ─────────────────────────────────────────────
    # EVENT REGISTRY
    # ─────────────────────────────────────────────

    def get_eventid_for_event(self, event_name):
        payload = {
            "action": "raw_sql",
            "sql": "SELECT e.event_name, e.event_id FROM event_registry e WHERE e.event_name = %s AND e.active = 1;",
            "params": [event_name]
        }
        try:
            response = call_lambda(payload)
            records = response.get("records", [])
            return records[0]["event_id"] if records else None
        except Exception as e:
            print("❌ Lambda Fetch Error (get_eventid_for_event):", e)
        return None

    # ─────────────────────────────────────────────
    # EVENT LOG
    # ─────────────────────────────────────────────

    def load_event_log(self, event_log_payload):
        event_id = event_log_payload["event_id"]
        issue_reference_id = event_log_payload["reference_id"]
        log_payload = json.dumps(event_log_payload["payload"])

        payload = {
            "action": "raw_sql",
            "sql": "INSERT INTO `event_log`(`event_id`,`reference_id`,`payload`,`status`,`created_at`) VALUES(%s,%s,%s,%s,NOW())",
            "params": [event_id, issue_reference_id, log_payload, "PENDING"]
        }
        try:
            response = call_lambda(payload)
            return response.get("records", [])
        except Exception as e:
            print("❌ Lambda Fetch Error (load_event_log):", e)
        return []

    # ─────────────────────────────────────────────
    # WORKFLOW LOOKUP
    # ─────────────────────────────────────────────

    def get_workflow_by_event(self, event_name):
        payload = {
            "action": "raw_sql",
            "sql": """SELECT e.event_id, e.event_name, w.workflow_id, w.workflow_name 
                      FROM event_registry e 
                      JOIN event_subscriptions s ON e.event_id = s.event_id 
                      JOIN workflow_definitions w ON s.workflow_id = w.workflow_id 
                      WHERE e.event_name = %s AND s.active = 1 AND w.active = 1""",
            "params": [event_name]
        }
        try:
            response = call_lambda(payload)
            return response.get("records", [])
        except Exception as e:
            print("❌ Lambda Fetch Error (get_workflow_by_event):", e)
        return []

    # ─────────────────────────────────────────────
    # STAGES
    # ─────────────────────────────────────────────

    def get_initial_stage(self, workflow_id):
        payload = {
            "action": "raw_sql",
            "sql": """SELECT stage_id, stage_name 
                  FROM workflow_stages 
                  WHERE workflow_id = %s AND is_initial = 1 
                  LIMIT 1""",
            "params": [workflow_id]
        }
        try:
            response = call_lambda(payload)
            records = response.get("records", [])
            return records[0] if records else None
        except Exception as e:
            print("❌ Lambda Fetch Error (get_initial_stage):", e)
        return None

    def get_current_stage(self, instance_id):
        payload = {
            "action": "raw_sql",
            "sql": """SELECT ws.stage_id, ws.stage_name, ws.is_terminal 
                      FROM workflow_instance wi 
                      JOIN workflow_stages ws ON wi.current_stage_id = ws.stage_id 
                      WHERE wi.instance_id = %s""",
            "params": [instance_id]
        }
        try:
            response = call_lambda(payload)
            records = response.get("records", [])
            return records[0] if records else None
        except Exception as e:
            print("❌ Lambda Fetch Error (get_current_stage):", e)
        return None

    # ─────────────────────────────────────────────
    # TRANSITIONS
    # ─────────────────────────────────────────────

    def get_available_transitions(self, instance_id):
        payload = {
            "action": "raw_sql",
            "sql": """SELECT wt.transition_id, wt.action_name, wt.to_stage_id, wt.role_required,
                             ws.stage_name AS to_stage_name
                      FROM workflow_instance wi
                      JOIN workflow_transitions wt ON wi.current_stage_id = wt.from_stage_id
                                                   AND wi.workflow_id = wt.workflow_id
                      JOIN workflow_stages ws ON wt.to_stage_id = ws.stage_id
                      WHERE wi.instance_id = %s AND wt.active = 1""",
            "params": [instance_id]
        }
        try:
            response = call_lambda(payload)
            return response.get("records", [])
        except Exception as e:
            print("❌ Lambda Fetch Error (get_available_transitions):", e)
        return []

    def get_workflow_id_for_instance(self, instance_id):
        """Fetches workflow_id from workflow_instance for a given instance_id."""
        payload = {
            "action": "raw_sql",
            "sql": "SELECT workflow_id FROM workflow_instance WHERE instance_id = %s",
            "params": [instance_id]
        }
        try:
            response = call_lambda(payload)
            records = response.get("records", [])
            return records[0]["workflow_id"] if records else None
        except Exception as e:
            print("❌ Lambda Fetch Error (get_workflow_id_for_instance):", e)
        return None

    def transition_stage(self, instance_id, action_name, performed_by, remarks=None):
        # 1. Get current stage
        current_stage = self.get_current_stage(instance_id)
        if not current_stage:
            print("❌ Could not fetch current stage for instance:", instance_id)
            return False

        # 2. Get matching transition
        transitions = self.get_available_transitions(instance_id)
        transition = next((t for t in transitions if t["action_name"] == action_name), None)
        if not transition:
            print(f"❌ No valid transition found for action '{action_name}'")
            return False

        to_stage_id = transition["to_stage_id"]

        # 3. Update current_stage_id in workflow_instance
        update_payload = {
            "action": "raw_sql",
            "sql": "UPDATE workflow_instance SET current_stage_id = %s WHERE instance_id = %s",
            "params": [to_stage_id, instance_id]
        }
        try:
            call_lambda(update_payload)
        except Exception as e:
            print("❌ Lambda Fetch Error (transition_stage - update):", e)
            return False

        # 4. Fetch workflow_id for history log
        workflow_id = self.get_workflow_id_for_instance(instance_id)

        # 5. Log to workflow_history — now with correct workflow_id
        self.log_history(
            instance_id=instance_id,
            workflow_id=workflow_id,
            from_stage_id=current_stage["stage_id"],
            to_stage_id=to_stage_id,
            action=action_name,
            performed_by=performed_by,
            remarks=remarks
        )

        # 6. Check if terminal stage — close the instance
        if transition.get("is_terminal") or self._is_terminal_stage(to_stage_id):
            self._complete_instance(instance_id)
            print(f"✅ Workflow instance {instance_id} completed.")

        print(f"✅ Transitioned | instance={instance_id} | action={action_name} | to_stage={to_stage_id}")
        return True

    def _is_terminal_stage(self, stage_id):
        payload = {
            "action": "raw_sql",
            "sql": "SELECT is_terminal FROM workflow_stages WHERE stage_id = %s AND is_terminal = 1",
            "params": [stage_id]
        }
        try:
            response = call_lambda(payload)
            records = response.get("records", [])
            if records:
                return records[0]["is_terminal"] in [1, True, b'\x01']
        except Exception as e:
            print("❌ Lambda Fetch Error (_is_terminal_stage):", e)
        return False

    # ─────────────────────────────────────────────
    # INSTANCE MANAGEMENT
    # ─────────────────────────────────────────────

    def create_instance(self, workflow_id, reference_id, module_name, initial_stage_id):
        payload = {
            "action": "raw_sql",
            "sql": """INSERT INTO workflow_instance 
                      (workflow_id, reference_id, module_name, current_stage_id, status, started_at) 
                      VALUES (%s, %s, %s, %s, 'ACTIVE', NOW())""",
            "params": [workflow_id, reference_id, module_name, initial_stage_id]
        }
        try:
            response = call_lambda(payload)
            return response.get("inserted_id")
        except Exception as e:
            print("❌ Lambda Fetch Error (create_instance):", e)
        return None

    def _complete_instance(self, instance_id):
        payload = {
            "action": "raw_sql",
            "sql": "UPDATE workflow_instance SET status = 'COMPLETED', completed_at = NOW() WHERE instance_id = %s",
            "params": [instance_id]
        }
        try:
            call_lambda(payload)
        except Exception as e:
            print("❌ Lambda Fetch Error (_complete_instance):", e)

    # ─────────────────────────────────────────────
    # HISTORY
    # ─────────────────────────────────────────────

    def log_history(self, instance_id, workflow_id, from_stage_id, to_stage_id, action, performed_by, remarks=None):
        payload = {
            "action": "raw_sql",
            "sql": """INSERT INTO workflow_history 
                      (instance_id, workflow_id, from_stage_id, to_stage_id, action_performed, performed_by, remarks, performed_at) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
            "params": [instance_id, workflow_id, from_stage_id, to_stage_id, action, performed_by, remarks]
        }
        try:
            response = call_lambda(payload)
            return response.get("records", [])
        except Exception as e:
            print("❌ Lambda Fetch Error (log_history):", e)
        return None

    def get_history(self, instance_id):
        payload = {
            "action": "raw_sql",
            "sql": """SELECT wh.history_id, wh.action_performed, wh.performed_by, wh.remarks, wh.performed_at,
                             fs.stage_name AS from_stage, ts.stage_name AS to_stage
                      FROM workflow_history wh
                      LEFT JOIN workflow_stages fs ON wh.from_stage_id = fs.stage_id
                      LEFT JOIN workflow_stages ts ON wh.to_stage_id = ts.stage_id
                      WHERE wh.instance_id = %s
                      ORDER BY wh.performed_at ASC""",
            "params": [instance_id]
        }
        try:
            response = call_lambda(payload)
            return response.get("records", [])
        except Exception as e:
            print("❌ Lambda Fetch Error (get_history):", e)
        return []

    # ─────────────────────────────────────────────
    # ORCHESTRATOR
    # ─────────────────────────────────────────────

    def trigger_workflow(self, event_name, reference_id, module_name, performed_by, extra_payload=None):
        # 1. Get event_id
        event_id = self.get_eventid_for_event(event_name)
        if not event_id:
            print("❌ Event not found:", event_name)
            return None

        # 2. Log the event
        self.load_event_log({
            "event_id": event_id,
            "reference_id": reference_id,
            "payload": {
                "reference_id": reference_id,
                "module": module_name,
                **(extra_payload or {})
            }
        })

        # 3. Get workflow linked to this event
        workflows = self.get_workflow_by_event(event_name)
        if not workflows:
            print("❌ No active workflow found for event:", event_name)
            return None
        workflow = workflows[0]
        workflow_id = workflow["workflow_id"]

        # 4. Get initial stage
        initial_stage = self.get_initial_stage(workflow_id)
        if not initial_stage:
            print("❌ No initial stage defined for workflow:", workflow_id)
            return None

        # 5. Create workflow instance
        instance_id = self.create_instance(workflow_id, reference_id, module_name, initial_stage["stage_id"])
        if not instance_id:
            print("❌ Failed to create workflow instance")
            return None

        # 6. Log initial history entry
        self.log_history(
            instance_id=instance_id,
            workflow_id=workflow_id,
            from_stage_id=None,
            to_stage_id=initial_stage["stage_id"],
            action="WORKFLOW_STARTED",
            performed_by=performed_by,
            remarks=f"Workflow '{workflow['workflow_name']}' initiated for {module_name} ref:{reference_id}"
        )

        print(f"✅ Workflow started | instance_id={instance_id} | stage='{initial_stage['stage_name']}'")
        return instance_id