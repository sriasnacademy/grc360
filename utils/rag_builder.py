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
        
    elif entity_type == "SUB_PROCESS":
        return {
        "rag_text": f"""
Sub Process Name: {data.get('sub_process_name')}
Description: {data.get('description')}
Department: {data.get('department')}
Owner: {data.get('sub_process_owner')}
Frequency: {data.get('frequency')}
Inputs: {', '.join(data.get('triggers', []))}
Outputs: {', '.join(data.get('outcomes', []))}
""".strip(),

        "source_table": "sub_processes",
        "metadata": {
            "department": data.get("department"),
            "owner": data.get("sub_process_owner"),
            "frequency": data.get("frequency")
        }
    }
        
    elif entity_type == "TEST_PLAN":
        return {
        "rag_text": f"""
Test Plan Name: {data.get('test_plan_name')}
Description: {data.get('description')}
Module: {data.get('module')}
Status: {data.get('stauts')}
""".strip(),

        "source_table": "test_plan",
        "metadata": {
        }
    }
         
    elif entity_type == "PROCESS_SUBPROCESS_LINK":
        return {
            "rag_text": f"""
Process-Subprocess Link
Process ID: {data.get('process_id')}
Process Name: {data.get('process_name')}
Process Description: {data.get('process_description')}
Process Department: {data.get('process_department')}
Sub-Process ID: {data.get('sub_process_id')}
Sub-Process Name: {data.get('sub_process_name')}
Sub-Process Description: {data.get('sub_process_description')}
Sub-Process Department: {data.get('sub_process_department')}
Sub-Process Owner: {data.get('sub_process_owner')}
""".strip(),
            "source_table": "process_subprocess_map",
            "metadata": {
                "process_id":      data.get("process_id"),
                "process_name":    data.get("process_name"),
                "sub_process_id":  data.get("sub_process_id"),
                "sub_process_name": data.get("sub_process_name"),
            }
        }

    else:
        raise ValueError(f"Unsupported entity type: {entity_type}")