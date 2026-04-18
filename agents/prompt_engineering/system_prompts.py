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
# Add at the top with other imports
from agents.prompt_engineering.report_pipeline import run_report_pipeline
from agents.prompt_engineering.linking.entity_linker import (
    smart_link_router,
    link_risk_control,
    link_process_risk,
    link_process_subprocess,
    link_test_plan_control,
    link_test_step_control,
    link_test_plan_step,
)


# ─────────────────────────────────────────────────────────────
# LINK KEYWORDS — any of these means the user wants to link
# ─────────────────────────────────────────────────────────────
LINK_KEYWORDS = [
    "link", "map", "assign", "associate",
    "add", "include", "part of", "under",
    "connect", "belongs to", "attach", "relate",
    "bind", "join", "tie",
]


def route_pipeline(intent: str, raw_text: str):
    intent_upper = intent.upper().strip()
    text_lower   = raw_text.lower()

    print("INTENT detected:", intent_upper)
    print("RAW TEXT:", raw_text)

    # ── 1. LINK ROUTING ─────────────────────────────────────
    is_link_intent = (
        any(kw in text_lower for kw in LINK_KEYWORDS)
        or intent_upper.startswith("LINK_")
    )
    if is_link_intent:
        print("🔁 Routing to smart_link_router")
        return smart_link_router(raw_text)

    # ── 2. REPORT ROUTING (Put this HIGH in the order) ───────
    if (intent_upper.startswith("REPORT_") or 
        any(kw in text_lower for kw in ["report", "statistic", "stats", "audit", "trail", 
                                        "summary", "analytics", "confidence levels", "enhanced report"])):
        print("📊 Routing to Enhanced Report Pipeline")
        try:
            from agents.prompt_engineering.report_pipeline import run_report_pipeline
            return run_report_pipeline(intent_upper, raw_text)
        except Exception as e:
            print(f"❌ Report pipeline import error: {e}")
            return f"❌ Report pipeline failed to load: {str(e)}"

    # ── 3. CREATE INTENTS ───────────────────────────────────
    elif intent_upper == "CREATE_PROCESS":
        return run_process_pipeline(intent_upper, raw_text)

    elif intent_upper == "CREATE_RISK":
        return run_risk_pipeline(intent_upper, raw_text)

    elif intent_upper == "CREATE_CONTROL":
        return run_control_pipeline(intent_upper, raw_text)

    elif intent_upper == "CREATE_SUBPROCESS":
        return run_subporcess_pipeline(intent_upper, raw_text)

    elif intent_upper == "CREATE_TEST_PLAN":
        return run_test_plan_pipeline(intent_upper, raw_text)

    # ── 4. VIEW / QUERY INTENTS ─────────────────────────────
    elif intent_upper in ("VIEW_PROCESS", "QUERY_PROCESS"):
        return run_view_process_pipeline(intent_upper, raw_text)

    elif intent_upper in ("VIEW_RISK", "QUERY_RISK"):
        return run_view_risk_pipeline(intent_upper, raw_text)

    elif intent_upper in ("VIEW_SUBPROCESS", "QUERY_SUBPROCESS"):
        return run_view_subprocess_pipeline(intent_upper, raw_text)

    elif intent_upper in ("VIEW_CONTROL", "QUERY_CONTROL"):
        return run_view_control_pipeline(intent_upper, raw_text)

    elif intent_upper in ("VIEW_TEST_PLAN", "QUERY_TEST_PLAN"):
        return run_view_test_plan_pipeline(intent_upper, raw_text)

    # ── 5. FALLBACK ─────────────────────────────────────────
    else:
        return f"⚠ Intent not supported: '{intent_upper}'\n\nTry:\n• 'show me confidence levels across pipelines'\n• 'statistical report on controls'\n• 'audit trail of AI decisions'"