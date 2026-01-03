from connectors.lambda_mysql import call_lambda


def run_view_subprocess_pipeline(intent: str, raw_text: str):
    try:
        payload = {
            "action": "select",
            "table": "sub_processes"
        }

        data = call_lambda(payload)
        records = data.get("records", [])

        if not records:
            return "No sub-processes are created yet."

        return format_subprocess_response(records)

    except Exception as e:
        return f"❌ Error fetching sub-processes: {e}"


def format_subprocess_response(sub_processes):
    response = "🔹 Sub-Processes Created in the System\n\n"

    for idx, sp in enumerate(sub_processes, start=1):
        response += f"{idx}. 🔸 {sp.get('sub_process_name', 'N/A')}\n"

        if sp.get("process_id"):
            response += f"   • Process ID: {sp['process_id']}\n"
        if sp.get("department"):
            response += f"   • Department: {sp['department']}\n"
        if sp.get("sub_process_owner"):
            response += f"   • Owner: {sp['sub_process_owner']}\n"
        if sp.get("frequency"):
            response += f"   • Frequency: {sp['frequency']}\n"
        if sp.get("status"):
            response += f"   • Status: {sp['status']}\n"
        if sp.get("description"):
            response += f"   • Description: {sp['description']}\n"

        response += "\n"

    return response.strip()
