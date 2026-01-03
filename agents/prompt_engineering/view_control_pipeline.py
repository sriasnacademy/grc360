from connectors.lambda_mysql import call_lambda
from agents.prompt_engineering.common_name_extractor import extract_entity_name


def run_view_control_pipeline(intent: str, raw_text: str):
    try:
        control_name = extract_entity_name(raw_text, "control")

        payload = {
            "action": "select",
            "table": "control"
        }

        if control_name:
            payload["where"] = {
                "control_name": control_name
            }

        data = call_lambda(payload)
        records = data.get("records", [])

        if not records:
            return "No matching control found."

        return format_control_response(records)

    except Exception as e:
        return f"❌ Error fetching control: {e}"


def format_control_response(controls):
    response = "🛡 Control Details\n\n"

    for idx, c in enumerate(controls, start=1):
        response += f"{idx}. 🛡 {c.get('control_name', 'N/A')}\n"

        if c.get("description"):
            response += f"   • Description: {c['description']}\n"
        if c.get("control_type"):
            response += f"   • Control Type: {c['control_type']}\n"
        if c.get("control_category"):
            response += f"   • Category: {c['control_category']}\n"

        response += "\n"

    return response.strip()
