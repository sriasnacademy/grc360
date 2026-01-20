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
    text = raw_text.lower()

    print("INTENT detected:", intent)
    print("RAW TEXT:", raw_text)

# ======================================================
# 🔗 LINKING INTENTS (HIGHEST PRIORITY)
# ======================================================

    LINK_KEYWORDS = [
        "link", "map", "assign", "associate",
        "add", "include", "part of", "under", "connect", "belongs to"
    ]

    if any(keyword in text for keyword in LINK_KEYWORDS):

        # Risk ↔ Control
        if "risk" in text and "control" in text:
            print("🔁 Forced routing: LINK_RISK_CONTROL")
            return link_risk_control(raw_text)

        # Process ↔ Risk
        if "process" in text and "risk" in text:
            print("🔁 Forced routing: LINK_PROCESS_RISK")
            return link_process_risk(raw_text)

        # ⭐ Process ↔ Sub-process (MAIN FIX)
        if (
            "sub process" in text
            or "subprocess" in text
            or "under" in text
            or "part of" in text
            or "include" in text
        ):
            print("🔁 Forced routing: LINK_PROCESS_SUBPROCESS")
            return link_process_subprocess(raw_text)


    # Intent-based linking (normal flow)
    if intent == "LINK_RISK_CONTROL":
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

    # ======================================================
    # ❌ FALLBACK
    # ======================================================
    else:
        return "⚠ Intent not supported"
