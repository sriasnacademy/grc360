def build_rag_payload(entity_type: str, data: dict) -> dict:
    if entity_type == "PROCESS":
        return {
            "rag_text": f"""
Process Name: {data.get('process_name')}
Description: {data.get('description')}
Department: {data.get('department')}
Owner: {data.get('process_owner')}
Frequency: {data.get('frequency')}
Triggers: {', '.join(data.get('triggers', []))}
Outcomes: {', '.join(data.get('outcomes', []))}
""".strip(),

            "source_table": "processes",
            "metadata": {
                "department": data.get("department"),
                "owner": data.get("process_owner"),
                "frequency": data.get("frequency")
            }
        }

    elif entity_type == "RISK":
        return {
            "rag_text": f"""
Risk Name: {data.get('risk_name')}
Description: {data.get('description')}
Risk Category: {data.get('risk_category')}
Impact Level: {data.get('impact')}
Likelihood: {data.get('likelihood')}
Related Process ID: {data.get('process_id')}
""".strip(),

            "source_table": "risk",
            "metadata": {
                "risk_category": data.get("risk_category"),
                "impact": data.get("impact"),
                "likelihood": data.get("likelihood")
            }
        }

    elif entity_type == "CONTROL":
        return {
            "rag_text": f"""
Control Name: {data.get('control_name')}
Description: {data.get('description')}
Control Type: {data.get('control_type')}
Frequency: {data.get('frequency')}
Owner: {data.get('control_owner')}
Related Risk ID: {data.get('risk_id')}
""".strip(),

            "source_table": "control",
            "metadata": {
                "control_type": data.get("control_type"),
                "frequency": data.get("frequency"),
                "owner": data.get("control_owner")
            }
        }

    else:
        raise ValueError(f"Unsupported entity type: {entity_type}")
