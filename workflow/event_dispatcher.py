from workflow.engine import WorkflowEngine

class WorkflowEventDispatcher:

    def __init__(self, engine):
        engine = WorkflowEngine()
        self.engine = engine

    def raise_event(self, event_name, payload):
        """
        event_code: ISSUE_CREATED
        payload: dictionary containing entity_id etc
        """
        required_keys = ["reference_id", "module_name", "performed_by", "payload_for_eventlog"]
        missing = [k for k in required_keys if k not in payload]
        if missing:
            print(f"❌ raise_event() missing keys: {missing}")
            return None
        self.engine.start_workflow(event_name, payload)
