def build_rag_payload(entity_type: str, data: dict) -> dict:

    # ──────────────────────────────────────────────────────────
    # CORE ENTITIES
    # ──────────────────────────────────────────────────────────

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
                "owner":      data.get("process_owner"),
                "frequency":  data.get("frequency"),
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
                "owner":      data.get("sub_process_owner"),
                "frequency":  data.get("frequency"),
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
                "impact":        data.get("impact"),
                "likelihood":    data.get("likelihood"),
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
                "frequency":    data.get("frequency"),
                "owner":        data.get("control_owner"),
            }
        }

    elif entity_type == "TEST_PLAN":
        return {
            "rag_text": f"""
Test Plan Name: {data.get('test_plan_name')}
Description: {data.get('description')}
Module: {data.get('module')}
Status: {data.get('status')}
""".strip(),
            "source_table": "test_plan",
            "metadata": {}
        }

    # ──────────────────────────────────────────────────────────
    # LINK ENTITIES
    # ──────────────────────────────────────────────────────────

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
                "process_id":       data.get("process_id"),
                "process_name":     data.get("process_name"),
                "sub_process_id":   data.get("sub_process_id"),
                "sub_process_name": data.get("sub_process_name"),
            }
        }

    elif entity_type == "PROCESS_RISK_LINK":
        return {
            "rag_text": f"""
Process/Subprocess-Risk Link
Entity Type: {data.get('pro_subpro_type')}
Entity ID: {data.get('pro_subpro_id')}
Entity Name: {data.get('entity_name')}
Risk ID: {data.get('risk_id')}
Risk Name: {data.get('risk_name')}
Risk Description: {data.get('risk_description')}
Risk Likelihood: {data.get('risk_likelihood')}
Risk Impact: {data.get('risk_impact')}
""".strip(),
            "source_table": "process_subprocess_risk_map",
            "metadata": {
                "pro_subpro_id":   data.get("pro_subpro_id"),
                "pro_subpro_type": data.get("pro_subpro_type"),
                "entity_name":     data.get("entity_name"),
                "risk_id":         data.get("risk_id"),
                "risk_name":       data.get("risk_name"),
            }
        }

    elif entity_type == "RISK_CONTROL_LINK":
        return {
            "rag_text": f"""
Risk-Control Link
Risk ID: {data.get('risk_id')}
Risk Name: {data.get('risk_name')}
Risk Description: {data.get('risk_description')}
Control ID: {data.get('control_id')}
Control Name: {data.get('control_name')}
Control Type: {data.get('control_type')}
Control Description: {data.get('control_description')}
""".strip(),
            "source_table": "risk_control_map",
            "metadata": {
                "risk_id":      data.get("risk_id"),
                "risk_name":    data.get("risk_name"),
                "control_id":   data.get("control_id"),
                "control_name": data.get("control_name"),
            }
        }

    elif entity_type == "TEST_PLAN_CONTROL_LINK":
        return {
            "rag_text": f"""
Test Plan-Control Link
Test Plan ID: {data.get('test_plan_id')}
Test Plan Name: {data.get('test_plan_name')}
Test Plan Module: {data.get('test_plan_module')}
Control ID: {data.get('control_id')}
Control Name: {data.get('control_name')}
Control Type: {data.get('control_type')}
Control Description: {data.get('control_description')}
""".strip(),
            "source_table": "test_plan_control_map",
            "metadata": {
                "test_plan_id":   data.get("test_plan_id"),
                "test_plan_name": data.get("test_plan_name"),
                "control_id":     data.get("control_id"),
                "control_name":   data.get("control_name"),
            }
        }

    elif entity_type == "TEST_STEP_CONTROL_LINK":
        return {
            "rag_text": f"""
Test Step-Control Link
Test Step ID: {data.get('test_step_id')}
Control Assertion: {data.get('control_assertion')}
Step Order: {data.get('step_order')}
Control Area: {data.get('control_area')}
Control ID: {data.get('control_id')}
Control Name: {data.get('control_name')}
Control Type: {data.get('control_type')}
Control Description: {data.get('control_description')}
""".strip(),
            "source_table": "test_step_control_map",
            "metadata": {
                "test_step_id":    data.get("test_step_id"),
                "control_assertion": data.get("control_assertion"),
                "control_id":      data.get("control_id"),
                "control_name":    data.get("control_name"),
            }
        }

    elif entity_type == "TEST_PLAN_STEP_LINK":
        return {
            "rag_text": f"""
Test Plan-Test Step Link
Test Plan ID: {data.get('test_plan_id')}
Test Plan Name: {data.get('test_plan_name')}
Test Plan Module: {data.get('test_plan_module')}
Test Step ID: {data.get('test_step_id')}
Control Assertion: {data.get('control_assertion')}
Step Order: {data.get('step_order')}
Control Area: {data.get('control_area')}
""".strip(),
            "source_table": "test_plan_step_map",
            "metadata": {
                "test_plan_id":      data.get("test_plan_id"),
                "test_plan_name":    data.get("test_plan_name"),
                "test_step_id":      data.get("test_step_id"),
                "control_assertion": data.get("control_assertion"),
            }
        }

    else:
        raise ValueError(f"Unsupported entity type: {entity_type}")