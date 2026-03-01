from workflow.instance_manager import WorkflowInstanceManager

class WorkflowEngine:

    def __init__(self):
        self.instance_manager = WorkflowInstanceManager()

    def start_workflow(self, event_name, payload):
        
        #raise event and get eventid
        event_id = self.instance_manager.get_eventid_for_event(event_name)

        event_log_dict = {"event_id":event_id,
                          "reference_id": payload["issue_id"],
                          "payload":payload["issue_payload"]}
        #insert event_log
        logresult = self.instance_manager.load_event_log(event_log_dict)
        print(logresult.get("status"))

        # 1️⃣ Find workflow by trigger event
        workflow = self.instance_manager.get_workflow_by_event(event_id)

        if not workflow:
            return

        # 2️⃣ Create workflow instance
        instance_id = self.instance_manager.create_instance(
            workflow_id=workflow["workflow_id"],
            reference_id=payload["issue_id"]
        )

        # 3️⃣ Start first step
        self.instance_manager.activate_first_step(
            instance_id,
            workflow["workflow_id"]
        )
