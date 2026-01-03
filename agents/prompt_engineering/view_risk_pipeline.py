from connectors.lambda_mysql import call_lambda


def run_view_risk_pipeline(intent: str, raw_text: str):
    try:
        payload = {
            "action": "select",
            "table": "risk"
        }

        data = call_lambda(payload)
        records = data.get("records", [])

        if not records:
            return "No risks are created yet."

        return format_risk_response(records)

    except Exception as e:
        return f"❌ Error fetching risks: {e}"


def format_risk_response(risks):
    response = "⚠️ Risks Created in the System\n\n"

    for idx, r in enumerate(risks, start=1):
        response += f"{idx}. ⚠ {r.get('risk_name', 'N/A')}\n"

        if r.get("description"):
            response += f"   • Description: {r['description']}\n"
        if r.get("impact"):
            response += f"   • Impact: {r['impact']}\n"
        if r.get("likelihood"):
            response += f"   • Likelihood: {r['likelihood']}\n"
        if r.get("severity"):
            response += f"   • Severity: {r['severity']}\n"
        if r.get("owner"):
            response += f"   • Owner: {r['owner']}\n"
        if r.get("status"):
            response += f"   • Status: {r['status']}\n"

        response += "\n"

    return response.strip()
