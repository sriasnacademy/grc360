from agents.prompt_engineering.process_pipeline import run_process_pipeline
from agents.prompt_engineering.risk_pipeline import run_risk_pipeline
from agents.prompt_engineering.control_pipeline import run_control_pipeline
from agents.prompt_engineering.subprocess_pipeline import run_subporcess_pipeline
from agents.prompt_engineering.test_plan_pipeline import run_test_plan_pipeline

def route_pipeline(intent: str, raw_text: str):
    intent = intent.upper()
    
    print("INTENT in prompt file: ",intent)
    
    if intent == "CREATE_PROCESS":
        return run_process_pipeline(intent, raw_text)

    elif intent == "CREATE_RISK":
        return run_risk_pipeline(intent, raw_text)
    
    elif intent == "CREATE_CONTROL":
        return run_control_pipeline(intent, raw_text)
    
    elif intent == "CREATE_SUBPROCESS":
        return run_subporcess_pipeline(intent, raw_text)
    
    elif intent == "CREATE_TEST_PLAN":
        return run_test_plan_pipeline(intent, raw_text)

    else:
        return "⚠ Intent not supported"
