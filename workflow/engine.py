from workflow.instance_manager import WorkflowInstanceManager
from connectors.lambda_mysql import call_lambda
from agents.attribution_agent import (
    attribution_agent, ActionType, ConfidenceLevel,
    Source, ACTOR_WORKFLOW_ENGINE,
)


class WorkflowEngine:

    def __init__(self):
        self.instance_manager = WorkflowInstanceManager()

    def start_workflow(self, event_name, payload):
        event_id = self.instance_manager.get_eventid_for_event(event_name)
        if not event_id:
            print(f"❌ Event not found or inactive: {event_name}")
            return None

        event_log_dict = {
            "event_id":    event_id,
            "reference_id": payload["reference_id"],
            "payload":     payload["payload_for_eventlog"],
        }
        log_result = self.instance_manager.load_event_log(event_log_dict)
        print("📋 Event logged:", log_result)

        workflows = self.instance_manager.get_workflow_by_event(event_name)
        if not workflows:
            print(f"❌ No active workflow found for event: {event_name}")
            return None
        workflow = workflows[0]

        initial_stage = self.instance_manager.get_initial_stage(workflow["workflow_id"])
        if not initial_stage:
            print(f"❌ No initial stage for workflow: {workflow['workflow_id']}")
            return None

        instance_id = self.instance_manager.create_instance(
            workflow_id      = workflow["workflow_id"],
            reference_id     = payload["reference_id"],
            module_name      = payload.get("module_name", ""),
            initial_stage_id = initial_stage["stage_id"],
            cycle_number     = payload["cycle_number"],
        )
        if not instance_id:
            print("❌ Failed to create workflow instance")
            return None

        self.instance_manager.log_history(
            instance_id  = instance_id,
            workflow_id  = workflow["workflow_id"],
            from_stage_id = None,
            to_stage_id  = initial_stage["stage_id"],
            action       = "WORKFLOW_STARTED",
            performed_by = payload.get("performed_by", "SYSTEM"),
            remarks      = f"Workflow '{workflow['workflow_name']}' started for ref:{payload['reference_id']}",
        )

        # ── Attribution record ───────────────────────────────────────
        attribution_agent.record(
            action_type      = ActionType.WORKFLOW_TRANSITION,
            actor            = ACTOR_WORKFLOW_ENGINE,
            sources          = [
                Source("wf-event",   "Workflow Event",    "system",   event_name),
                Source("wf-payload", "Event Payload",     "system",   str(payload["reference_id"]),
                       excerpt=str(payload.get("payload_for_eventlog", ""))[:200]),
            ],
            decision_summary = (
                f"Workflow '{workflow['workflow_name']}' (id={workflow['workflow_id']}) started. "
                f"Instance {instance_id} created at stage '{initial_stage['stage_name']}'."
            ),
            reasoning        = (
                f"Event '{event_name}' triggered workflow. "
                f"Reference: {payload['reference_id']}, performed_by: {payload.get('performed_by', 'SYSTEM')}"
            ),
            confidence       = ConfidenceLevel.HIGH,
            tags             = ["workflow", "started", event_name.lower()],
        )
        # ────────────────────────────────────────────────────────────

        self.assign_owner(
            instance_id  = instance_id,
            reference_id = payload["reference_id"],
            workflow_id  = workflow["workflow_id"],
            assigned_by  = payload.get("performed_by", "SYSTEM"),
        )

        return instance_id

    def assign_owner(self, instance_id, reference_id, workflow_id, assigned_by):
        role_payload = {
            "action": "raw_sql",
            "sql": """SELECT role_required FROM workflow_transitions
                      WHERE workflow_id = %s AND action_name = 'assign_owner' AND active = 1 LIMIT 1""",
            "params": [workflow_id],
        }
        try:
            response = call_lambda(role_payload)
            records  = response.get("records", [])
            if not records:
                print("❌ No role found for assign_owner transition")
                return False
            role = records[0]["role_required"]
        except Exception as e:
            print(f"❌ Lambda Fetch Error (assign_owner - get role): {e}")
            return False

        update_payload = {
            "action": "raw_sql",
            "sql": "UPDATE issues SET assigned_to = %s, assigned_by = %s, assigned_at = NOW() WHERE issue_id = %s",
            "params": [role, assigned_by, reference_id],
        }
        try:
            call_lambda(update_payload)
        except Exception as e:
            print(f"❌ Lambda Fetch Error (assign_owner - update issues): {e}")
            return False

        success = self.perform_action(
            instance_id  = instance_id,
            action_name  = "assign_owner",
            performed_by = assigned_by,
            remarks      = f"Owner role assigned: {role}",
        )

        if success:
            # ── Attribution record for assign_owner ─────────────────
            attribution_agent.record(
                action_type      = ActionType.WORKFLOW_TRANSITION,
                actor            = ACTOR_WORKFLOW_ENGINE,
                sources          = [
                    Source("wf-transitions", "Workflow Transitions DB", "database",
                           f"workflow_transitions[workflow_id={workflow_id}]",
                           excerpt=f"role_required={role}"),
                ],
                decision_summary = (
                    f"Issue {reference_id} assigned to role '{role}' by '{assigned_by}'. "
                    f"Workflow instance {instance_id} transitioned: Issue Created → Assign Owner."
                ),
                reasoning        = "Auto assign_owner action fires immediately after workflow start per transition config.",
                confidence       = ConfidenceLevel.HIGH,
                tags             = ["workflow", "assign-owner", role.lower()],
            )
            # ────────────────────────────────────────────────────────

        return success

    def perform_action(self, instance_id, action_name, performed_by, remarks=None):
        success = self.instance_manager.transition_stage(
            instance_id  = instance_id,
            action_name  = action_name,
            performed_by = performed_by,
            remarks      = remarks,
        )
        if not success:
            print(f"❌ Action '{action_name}' failed for instance {instance_id}")
        return success

    def get_available_actions(self, instance_id):
        return self.instance_manager.get_available_transitions(instance_id)

    def get_current_stage(self, instance_id):
        return self.instance_manager.get_current_stage(instance_id)

    def get_history(self, instance_id):
        return self.instance_manager.get_history(instance_id)
