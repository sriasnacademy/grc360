from connectors.lambda_mysql import call_lambda
from models.my_llm_client import LLMClient


# ------------------------------------------------
# Initialize shared LLM client
# ------------------------------------------------
llm = LLMClient()


# ------------------------------------------------
# LLM helper: pick correct entity ID
# ------------------------------------------------
def llm_pick_id(entity_type: str, user_prompt: str, records: list, id_key: str, name_key: str):
    """
    Uses Groq LLM (via LLMClient) to choose the best matching entity ID
    """

    if not records:
        return None

    options = "\n".join(
        [f"{r[id_key]} | {r[name_key]}" for r in records]
    )

    llm_prompt = f"""
You are an enterprise GRC assistant.

User request:
"{user_prompt}"

Available {entity_type}s:
{options}

Rules:
- Pick the SINGLE best matching {entity_type}
- Reply ONLY with the ID
- If nothing matches, reply NONE
"""

    answer = llm.generate(llm_prompt).strip()

    if not answer or answer.upper() == "NONE":
        return None

    try:
        return int(answer)
    except ValueError:
        return None


# ------------------------------------------------
# Process ↔ Sub-process (LLM powered)
# ------------------------------------------------
def link_process_subprocess(prompt: str):

    process_result = call_lambda({
        "action": "select",
        "table": "processes"
    })

    subprocess_result = call_lambda({
        "action": "select",
        "table": "sub_processes"
    })

    processes = process_result.get("records", [])
    subprocesses = subprocess_result.get("records", [])

    process_id = llm_pick_id(
        "process",
        prompt,
        processes,
        "process_id",
        "process_name"
    )

    sub_process_id = llm_pick_id(
        "sub process",
        prompt,
        subprocesses,
        "sub_process_id",
        "sub_process_name"
    )

    if not process_id or not sub_process_id:
        return "❌ Unable to resolve Process or Sub-process using LLM"

    call_lambda({
        "action": "insert",
        "table": "process_subprocess_map",
        "data": {
            "process_id": process_id,
            "sub_process_id": sub_process_id
        }
    })

    return "✅ Sub-process linked to Process using Groq LLM"


# ------------------------------------------------
# Process / Sub-process ↔ Risk (LLM powered)
# ------------------------------------------------
def link_process_risk(prompt: str):

    # Fetch master data
    process_result = call_lambda({
        "action": "select",
        "table": "processes"
    })

    subprocess_result = call_lambda({
        "action": "select",
        "table": "sub_processes"
    })

    risk_result = call_lambda({
        "action": "select",
        "table": "risk"
    })

    processes = process_result.get("records", [])
    subprocesses = subprocess_result.get("records", [])
    risks = risk_result.get("records", [])

    # Try resolving both
    process_id = llm_pick_id(
        "process",
        prompt,
        processes,
        "process_id",
        "process_name"
    )

    sub_process_id = llm_pick_id(
        "sub process",
        prompt,
        subprocesses,
        "sub_process_id",
        "sub_process_name"
    )

    risk_id = llm_pick_id(
        "risk",
        prompt,
        risks,
        "risk_id",
        "risk_name"
    )

    if not risk_id:
        return "❌ Unable to resolve Risk using LLM"

    # Decide entity (IMPORTANT LOGIC)
    if sub_process_id:
        pro_subpro_id = sub_process_id
        pro_subpro_type = "SUB_PROCESS"
    elif process_id:
        pro_subpro_id = process_id
        pro_subpro_type = "PROCESS"
    else:
        return "❌ Unable to resolve Process or Sub-process using LLM"

    # Insert mapping (NEW STRUCTURE)
    call_lambda({
        "action": "insert",
        "table": "process_subprocess_risk_map",
        "data": {
            "pro_subpro_id": pro_subpro_id,
            "pro_subpro_type": pro_subpro_type,
            "risk_id": risk_id
        }
    })

    return f"✅ Risk linked to {pro_subpro_type.replace('_', ' ').title()} using Groq LLM"



# ------------------------------------------------
# Risk ↔ Control (LLM powered)
# ------------------------------------------------
def link_risk_control(prompt: str):

    risk_result = call_lambda({
        "action": "select",
        "table": "risk"
    })

    control_result = call_lambda({
        "action": "select",
        "table": "control"
    })

    risks = risk_result.get("records", [])
    controls = control_result.get("records", [])

    risk_id = llm_pick_id(
        "risk",
        prompt,
        risks,
        "risk_id",
        "risk_name"
    )

    control_id = llm_pick_id(
        "control",
        prompt,
        controls,
        "control_id",
        "control_name"
    )

    if not risk_id or not control_id:
        return "❌ Unable to resolve Risk or Control using LLM"

    call_lambda({
        "action": "insert",
        "table": "risk_control_map",
        "data": {
            "risk_id": risk_id,
            "control_id": control_id
        }
    })

    return "✅ Risk linked to Control using Groq LLM"
