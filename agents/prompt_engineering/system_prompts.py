from agents.prompt_engineering.process_pipeline import run_process_pipeline
from agents.prompt_engineering.risk_pipeline import run_risk_pipeline
from agents.prompt_engineering.control_pipeline import run_control_pipeline
from agents.prompt_engineering.subprocess_pipeline import run_subporcess_pipeline
from agents.prompt_engineering.test_plan_pipeline import run_test_plan_pipeline

from agents.prompt_engineering.view_process_pipeline import run_view_process_pipeline
from agents.prompt_engineering.view_risk_pipeline import run_view_risk_pipeline
from agents.prompt_engineering.view_subprocess_pipeline import run_view_subprocess_pipeline
from agents.prompt_engineering.view_control_pipeline import run_view_control_pipeline
from agents.prompt_engineering.view_test_plan_pipeline import run_view_test_plan_pipeline

from agents.prompt_engineering.linking.entity_linker import (
    link_risk_control,
    link_process_risk,
    link_process_subprocess,
    link_test_plan_control
)


def route_pipeline(intent: str, raw_text: str):
    intent = intent.upper()
    text = raw_text.lower()

    print("INTENT detected:", intent)
    print("RAW TEXT:", raw_text)

    LINK_KEYWORDS = [
        "link", "map", "assign", "associate",
        "add", "include", "part of", "under", "connect", "belongs to"
    ]

    # ======================================================
    # 🔗 FORCED LINK ROUTING (HIGHEST PRIORITY)
    # ======================================================
    if any(keyword in text for keyword in LINK_KEYWORDS):

        # ⭐⭐⭐ TEST PLAN ↔ CONTROL (MOST SPECIFIC – CHECK FIRST)
        if "test plan" in text and "control" in text:
            print("🔁 Forced routing: LINK_TEST_PLAN_CONTROL")
            return link_test_plan_control(raw_text)

        # Risk ↔ Control
        if "risk" in text and "control" in text:
            print("🔁 Forced routing: LINK_RISK_CONTROL")
            return link_risk_control(raw_text)

        # Process ↔ Risk
        if "process" in text and "risk" in text:
            print("🔁 Forced routing: LINK_PROCESS_RISK")
            return link_process_risk(raw_text)

        # Process ↔ Sub-process (KEEP THIS LAST)
        if (
            "sub process" in text
            or "subprocess" in text
            or "under" in text
            or "part of" in text
            or "include" in text
        ):
            print("🔁 Forced routing: LINK_PROCESS_SUBPROCESS")
            return link_process_subprocess(raw_text)

    # ======================================================
    # 🔁 NORMAL INTENT-BASED ROUTING
    # ======================================================
    if intent == "LINK_TEST_PLAN_CONTROL":
        return link_test_plan_control(raw_text)

    elif intent == "LINK_RISK_CONTROL":
        return link_risk_control(raw_text)

    elif intent == "LINK_PROCESS_RISK":
        return link_process_risk(raw_text)

    elif intent == "LINK_PROCESS_SUBPROCESS":
        return link_process_subprocess(raw_text)

    # ======================================================
    # ➕ CREATE INTENTS
    # ======================================================
    elif intent == "CREATE_PROCESS":
        return run_process_pipeline(intent, raw_text)

    elif intent == "CREATE_RISK":
        return run_risk_pipeline(intent, raw_text)

    elif intent == "CREATE_CONTROL":
        return run_control_pipeline(intent, raw_text)

    elif intent == "CREATE_SUBPROCESS":
        return run_subporcess_pipeline(intent, raw_text)

    elif intent == "CREATE_TEST_PLAN":
        return run_test_plan_pipeline(intent, raw_text)

    # ======================================================
    # 👀 VIEW / QUERY INTENTS
    # ======================================================
    elif intent in ("VIEW_PROCESS", "QUERY_PROCESS"):
        return run_view_process_pipeline(intent, raw_text)

    elif intent in ("VIEW_RISK", "QUERY_RISK"):
        return run_view_risk_pipeline(intent, raw_text)

    elif intent in ("VIEW_SUBPROCESS", "QUERY_SUBPROCESS"):
        return run_view_subprocess_pipeline(intent, raw_text)

    elif intent in ("VIEW_CONTROL", "QUERY_CONTROL"):
        return run_view_control_pipeline(intent, raw_text)
    
    elif intent in ("VIEW_TEST_PLAN", "QUERY_TEST_PLAN"):
        return run_view_test_plan_pipeline(intent, raw_text)


    # ======================================================
    # ❌ FALLBACK
    # ======================================================
    else:
        return "⚠ Intent not supported"
