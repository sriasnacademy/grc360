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
        self.engine.start_workflow(event_name, payload)
