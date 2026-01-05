from connectors.lambda_mysql import call_lambda
from agents.prompt_engineering.common_name_extractor import extract_names


# ------------------------------------------------
# Process ↔ Subprocess
# ------------------------------------------------
def link_process_subprocess(prompt: str):
    names = extract_names(prompt)

    process_name = names.get("process")
    subprocess_name = names.get("sub_process")

    if not process_name or not subprocess_name:
        return "❌ Process or Sub-process not found in prompt"

    payload = {
        "action": "select",
        "query": "SELECT process_id FROM processes WHERE process_name = %s",
        "params": [process_name]
    }
    result = call_lambda(payload)

    if not result:
        return "❌ Process not found in DB"

    process_id = result[0]["process_id"]

    payload = {
        "action": "update",
        "query": """
            UPDATE sub_processes
            SET process_id = %s
            WHERE sub_process_name = %s
        """,
        "params": [process_id, subprocess_name]
    }
    call_lambda(payload)

    return "✅ Sub-process linked to process"


# ------------------------------------------------
# Process / Subprocess ↔ Risk
# ------------------------------------------------
def link_process_risk(prompt: str):
    names = extract_names(prompt)

    process_name = names.get("process")
    subprocess_name = names.get("sub_process")
    risk_name = names.get("risk")

    if not process_name or not risk_name:
        return "❌ Process or Risk not found in prompt"

    payload = {
        "action": "select",
        "query": "SELECT process_id FROM processes WHERE process_name = %s",
        "params": [process_name]
    }
    result = call_lambda(payload)

    if not result:
        return "❌ Process not found"

    process_id = result[0]["process_id"]

    sub_process_id = None
    if subprocess_name:
        payload = {
            "action": "select",
            "query": "SELECT sub_process_id FROM sub_processes WHERE sub_process_name = %s",
            "params": [subprocess_name]
        }
        sub_result = call_lambda(payload)
        if sub_result:
            sub_process_id = sub_result[0]["sub_process_id"]

    payload = {
        "action": "select",
        "query": "SELECT risk_id FROM risks WHERE risk_name = %s",
        "params": [risk_name]
    }
    risk_result = call_lambda(payload)

    if not risk_result:
        return "❌ Risk not found"

    risk_id = risk_result[0]["risk_id"]

    payload = {
        "action": "insert",
        "query": """
            INSERT INTO process_risk_map (process_id, sub_process_id, risk_id)
            VALUES (%s, %s, %s)
        """,
        "params": [process_id, sub_process_id, risk_id]
    }
    call_lambda(payload)

    return "✅ Risk linked to process"


# ------------------------------------------------
# Risk ↔ Control
# ------------------------------------------------
def link_risk_control(prompt: str):
    """
    Links a risk to a control based on names extracted from the prompt.
    Robust against case differences, extra spaces, and partial matches.
    """

    names = extract_names(prompt)
    risk_name = names.get("risk")
    control_name = names.get("control")

    if not risk_name or not control_name:
        return "❌ Risk or Control name not found in prompt"

    # --- 1. Fetch all risks ---
    payload = {"action": "select", "table": "risk"}
    risk_result = call_lambda(payload)
    risk_id = None

    # First try exact match
    for r in risk_result.get("records", []):
        if r["risk_name"].strip().lower() == risk_name.strip().lower():
            risk_id = r["risk_id"]
            break

    # If not found, try partial match (LIKE)
    if not risk_id:
        for r in risk_result.get("records", []):
            if risk_name.strip().lower() in r["risk_name"].strip().lower():
                risk_id = r["risk_id"]
                break

    if not risk_id:
        print("DB risks:", [repr(r["risk_name"]) for r in risk_result.get("records", [])])
        print("Prompt risk:", repr(risk_name))
        return "❌ Risk not found in DB"

    # --- 2. Fetch all controls ---
    payload = {"action": "select", "table": "control"}
    control_result = call_lambda(payload)
    control_id = None

    # Exact match
    for c in control_result.get("records", []):
        if c["control_name"].strip().lower() == control_name.strip().lower():
            control_id = c["control_id"]
            break

    # Partial match fallback
    if not control_id:
        for c in control_result.get("records", []):
            if control_name.strip().lower() in c["control_name"].strip().lower():
                control_id = c["control_id"]
                break

    if not control_id:
        print("DB controls:", [repr(c["control_name"]) for c in control_result.get("records", [])])
        print("Prompt control:", repr(control_name))
        return "❌ Control not found in DB"

    # --- 3. Insert mapping ---
    payload = {
        "action": "insert",
        "table": "risk_control_map",
        "data": {
            "risk_id": risk_id,
            "control_id": control_id
        }
    }
    call_lambda(payload)

    return "✅ Control linked to risk successfully"
