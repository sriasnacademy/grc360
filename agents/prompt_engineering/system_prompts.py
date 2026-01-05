from agents.prompt_engineering.process_pipeline import run_process_pipeline
from agents.prompt_engineering.risk_pipeline import run_risk_pipeline
from agents.prompt_engineering.control_pipeline import run_control_pipeline
from agents.prompt_engineering.subprocess_pipeline import run_subporcess_pipeline
from agents.prompt_engineering.test_plan_pipeline import run_test_plan_pipeline
from agents.prompt_engineering.view_process_pipeline import run_view_process_pipeline
from agents.prompt_engineering.view_risk_pipeline import run_view_risk_pipeline
from agents.prompt_engineering.view_subprocess_pipeline import run_view_subprocess_pipeline
from agents.prompt_engineering.view_control_pipeline import run_view_control_pipeline
from agents.prompt_engineering.linking.entity_linker import (
    link_risk_control,
    link_process_risk,
    link_process_subprocess
)


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

    elif intent == "VIEW_PROCESS":
        return run_view_process_pipeline(intent, raw_text)
    elif intent in ("VIEW_RISK", "QUERY_RISK"):
        return run_view_risk_pipeline(intent, raw_text)

    elif intent in ("VIEW_SUBPROCESS", "QUERY_SUBPROCESS"):
        return run_view_subprocess_pipeline(intent, raw_text)

    elif intent in ("VIEW_CONTROL", "QUERY_CONTROL"):
        return run_view_control_pipeline(intent, raw_text)

    elif intent == "LINK_RISK_CONTROL":
       return link_risk_control(raw_text)

    elif intent == "LINK_PROCESS_RISK":
        return link_process_risk(raw_text)

    elif intent == "LINK_PROCESS_SUBPROCESS":
        return link_process_subprocess(raw_text)
    else:
        return "⚠ Intent not supported"
