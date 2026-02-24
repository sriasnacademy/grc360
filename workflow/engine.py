from workflow.instance_manager import WorkflowInstanceManager

class WorkflowEngine:

    def __init__(self):
        self.instance_manager = WorkflowInstanceManager()

    def start_workflow(self, event_name, payload):
        
        event_code = self.instance_manager.get_eventcode_for_event(event_name)

        # 1️⃣ Find workflow by trigger event
        workflow = self.instance_manager.get_workflow_by_event(event_code)

        if not workflow:
            return

        # 2️⃣ Create workflow instance
        instance_id = self.instance_manager.create_instance(
            workflow_id=workflow["workflow_id"],
            entity_id=payload["entity_id"]
        )

        # 3️⃣ Start first step
        self.instance_manager.activate_first_step(
            instance_id,
            workflow["workflow_id"]
        )
