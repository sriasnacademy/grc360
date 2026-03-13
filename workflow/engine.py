from workflow.instance_manager import WorkflowInstanceManager
from connectors.lambda_mysql import call_lambda


class WorkflowEngine:

    def __init__(self):
        self.instance_manager = WorkflowInstanceManager()

    # ─────────────────────────────────────────────
    # START WORKFLOW
    # ─────────────────────────────────────────────

    def start_workflow(self, event_name, payload):
        """
        Kicks off a workflow for a given event.

        Expected payload structure:
        {
            "reference_id": <int>,
            "module_name": <str>,
            "performed_by": <str>,
            "payload_for_eventlog": { ... }
        }
        """

        # 1. Resolve event name → event_id
        event_id = self.instance_manager.get_eventid_for_event(event_name)
        if not event_id:
            print(f"❌ Event not found or inactive: {event_name}")
            return None

        # 2. Log the event
        event_log_dict = {
            "event_id": event_id,
            "reference_id": payload["reference_id"],
            "payload": payload["payload_for_eventlog"]
        }
        log_result = self.instance_manager.load_event_log(event_log_dict)
        print("📋 Event logged:", log_result)

        # 3. Find workflow linked to this event
        workflows = self.instance_manager.get_workflow_by_event(event_name)
        if not workflows:
            print(f"❌ No active workflow found for event: {event_name}")
            return None
        workflow = workflows[0]
        print(f"🔗 Workflow found: [{workflow['workflow_id']}] {workflow['workflow_name']}")

        # 4. Get initial stage
        initial_stage = self.instance_manager.get_initial_stage(workflow["workflow_id"])
        if not initial_stage:
            print(f"❌ No initial stage defined for workflow: {workflow['workflow_id']}")
            return None
        print(f"🚦 Initial stage: [{initial_stage['stage_id']}] {initial_stage['stage_name']}")

        # 5. Create workflow instance
        instance_id = self.instance_manager.create_instance(
            workflow_id=workflow["workflow_id"],
            reference_id=payload["reference_id"],
            module_name=payload.get("module_name", ""),
            initial_stage_id=initial_stage["stage_id"],
            cycle_number = payload["cycle_number"]
        )
        if not instance_id:
            print("❌ Failed to create workflow instance")
            return None
        print(f"✅ Workflow instance created: instance_id={instance_id}")

        # 6. Log initial history entry — Row 1
        self.instance_manager.log_history(
            instance_id=instance_id,
            workflow_id=workflow["workflow_id"],
            from_stage_id=None,
            to_stage_id=initial_stage["stage_id"],
            action="WORKFLOW_STARTED",
            performed_by=payload.get("performed_by", "SYSTEM"),
            remarks=f"Workflow '{workflow['workflow_name']}' started for ref:{payload['reference_id']}"
        )
        print(f"📝 History Row 1 logged: WORKFLOW_STARTED → {initial_stage['stage_name']}")

        # 7. Auto assign owner role — logs Row 2
        self.assign_owner(
            instance_id=instance_id,
            reference_id=payload["reference_id"],
            workflow_id=workflow["workflow_id"],
            assigned_by=payload.get("performed_by", "SYSTEM")
        )

        return instance_id

    # ─────────────────────────────────────────────
    # ASSIGN OWNER
    # ─────────────────────────────────────────────

    def assign_owner(self, instance_id, reference_id, workflow_id, assigned_by):
        """
        Automatically called after workflow starts.
        1. Looks up role_required from workflow_transitions for assign_owner action
        2. Updates issues table with that role
        3. Transitions workflow to Assign Owner stage → logs Row 2 in workflow_history
        """

        # 1. Get role from workflow_transitions for assign_owner action
        role_payload = {
            "action": "raw_sql",
            "sql": """SELECT role_required 
                      FROM workflow_transitions 
                      WHERE workflow_id = %s 
                      AND action_name = 'assign_owner' 
                      AND active = 1 
                      LIMIT 1""",
            "params": [workflow_id]
        }
        try:
            response = call_lambda(role_payload)
            records = response.get("records", [])
            if not records:
                print("❌ No role found for assign_owner transition")
                return False
            role = records[0]["role_required"]
            print(f"👤 Role found for assignment: {role}")
        except Exception as e:
            print(f"❌ Lambda Fetch Error (assign_owner - get role): {e}")
            return False

        # 2. Update issues table with role
        update_payload = {
            "action": "raw_sql",
            "sql": """UPDATE issues 
                      SET assigned_to = %s, assigned_by = %s, assigned_at = NOW() 
                      WHERE issue_id = %s""",
            "params": [role, assigned_by, reference_id]
        }
        try:
            call_lambda(update_payload)
            print(f"✅ issues.assigned_to = '{role}' for issue_id={reference_id}")
        except Exception as e:
            print(f"❌ Lambda Fetch Error (assign_owner - update issues): {e}")
            return False

        # 3. Transition workflow stage → this logs Row 2 in workflow_history
        success = self.perform_action(
            instance_id=instance_id,
            action_name="assign_owner",
            performed_by=assigned_by,
            remarks=f"Owner role assigned: {role}"
        )

        if success:
            print(f"📝 History Row 2 logged: Issue Created → Assign Owner")

        return success

    # ─────────────────────────────────────────────
    # TRANSITION STAGE
    # ─────────────────────────────────────────────

    def perform_action(self, instance_id, action_name, performed_by, remarks=None):
        """
        Moves the workflow instance to the next stage via the given action.
        """
        success = self.instance_manager.transition_stage(
            instance_id=instance_id,
            action_name=action_name,
            performed_by=performed_by,
            remarks=remarks
        )
        if not success:
            print(f"❌ Action '{action_name}' failed for instance {instance_id}")
        return success

    # ─────────────────────────────────────────────
    # QUERY HELPERS
    # ─────────────────────────────────────────────

    def get_available_actions(self, instance_id):
        """
        Returns list of actions the current user can take on this instance.
        """
        transitions = self.instance_manager.get_available_transitions(instance_id)
        if not transitions:
            print(f"⚠️ No available transitions for instance {instance_id}")
        return transitions

    def get_current_stage(self, instance_id):
        """
        Returns the current stage of the workflow instance.
        """
        return self.instance_manager.get_current_stage(instance_id)

    def get_history(self, instance_id):
        """
        Returns the full audit trail for a workflow instance.
        """
        return self.instance_manager.get_history(instance_id)