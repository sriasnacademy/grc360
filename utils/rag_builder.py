def build_process_rag_text(data: dict) -> str:
    return f"""
Process Name: {data.get("process_name")}
Description: {data.get("description")}
Department: {data.get("department")}
Owner: {data.get("owner")}
Frequency: {data.get("frequency")}
Triggers: {data.get("triggers")}
Outcomes: {data.get("outcomes")}
""".strip()
