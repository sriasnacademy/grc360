import json
from connectors.lambda_mysql import call_lambda
from models.my_llm_client import LLMClient
from services.rag_service import save_process_to_rag

# ─────────────────────────────────────────────────────────────
# Shared LLM client
# ─────────────────────────────────────────────────────────────
llm = LLMClient()


# ─────────────────────────────────────────────────────────────
# HELPER: LLM picks best matching ID from a list
# ─────────────────────────────────────────────────────────────
def llm_pick_id(entity_type: str, user_prompt: str, records: list,
                id_key: str, name_key: str):
    if not records:
        return None

    options = "\n".join([f"{r[id_key]} | {r[name_key]}" for r in records])

    prompt = f"""
You are an enterprise GRC assistant.

User request:
"{user_prompt}"

Available {entity_type}s:
{options}

Rules:
- Pick the SINGLE best matching {entity_type} based on partial/fuzzy name match
- Reply ONLY with the numeric ID
- If nothing matches, reply NONE
"""
    answer = llm.generate(prompt).strip()
    if not answer or answer.upper() == "NONE":
        return None
    try:
        return int(answer)
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────────
# HELPER: get full record by ID
# ─────────────────────────────────────────────────────────────
def get_record_by_id(records: list, id_key: str, id_val) -> dict:
    for rec in records:
        if rec.get(id_key) == id_val:
            return rec
    return {}


# ─────────────────────────────────────────────────────────────
# SMART ROUTER
# Fetches ALL entities, asks LLM to identify WHAT is being linked
# Works for ANY phrasing — user does NOT need to say entity type
# ─────────────────────────────────────────────────────────────
def smart_link_router(prompt: str):

    # ── Fetch all entity names from DB ───────────────────────
    processes  = call_lambda({"action": "select", "table": "processes",    "columns": ["process_id",    "process_name"]}).get("records", [])
    subprocs   = call_lambda({"action": "select", "table": "sub_processes","columns": ["sub_process_id","sub_process_name"]}).get("records", [])
    risks      = call_lambda({"action": "select", "table": "risk",         "columns": ["risk_id",       "risk_name"]}).get("records", [])
    controls   = call_lambda({"action": "select", "table": "control",      "columns": ["control_id",    "control_name"]}).get("records", [])
    test_plans = call_lambda({"action": "select", "table": "test_plan",    "columns": ["test_plan_id",  "test_plan_name"]}).get("records", [])
    test_steps = call_lambda({"action": "select", "table": "test_steps",   "columns": ["test_step_id",  "control_assertion"]}).get("records", [])

    def fmt(label, recs, id_k, nm_k):
        return "\n".join([f"  [{label}] id={r[id_k]} | {r[nm_k]}" for r in recs])

    all_entities = "\n".join(filter(None, [
        fmt("PROCESS",    processes,  "process_id",    "process_name"),
        fmt("SUBPROCESS", subprocs,   "sub_process_id","sub_process_name"),
        fmt("RISK",       risks,      "risk_id",       "risk_name"),
        fmt("CONTROL",    controls,   "control_id",    "control_name"),
        fmt("TEST_PLAN",  test_plans, "test_plan_id",  "test_plan_name"),
        fmt("TEST_STEP",  test_steps, "test_step_id",  "control_assertion"),
    ]))

    classification_prompt = f"""
You are an enterprise GRC assistant that links entities.

The user wants to link two things:
"{prompt}"

All available entities in the system:
{all_entities}

Your job:
1. Identify the TWO entities the user wants to link using fuzzy/partial name matching
2. Return ONLY valid JSON in this exact format:
{{
  "entity_a_type": "PROCESS|SUBPROCESS|RISK|CONTROL|TEST_PLAN|TEST_STEP",
  "entity_a_id": <numeric id>,
  "entity_b_type": "PROCESS|SUBPROCESS|RISK|CONTROL|TEST_PLAN|TEST_STEP",
  "entity_b_id": <numeric id>
}}

Rules:
- entity_a is the first entity mentioned, entity_b is the second
- Use ONLY types: PROCESS, SUBPROCESS, RISK, CONTROL, TEST_PLAN, TEST_STEP
- IDs must be exact numeric integers from the list above
- If you cannot identify both entities clearly, return {{"error": "cannot resolve"}}
- Return ONLY raw JSON — no markdown, no explanation
"""

    raw = llm.generate(classification_prompt).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        return f"❌ Smart router: could not parse LLM response: {raw[:120]}"

    if "error" in parsed:
        return f"❌ Could not identify entities from: \"{prompt}\". Please try rephrasing."

    type_a = (parsed.get("entity_a_type") or "").upper()
    type_b = (parsed.get("entity_b_type") or "").upper()
    id_a   = parsed.get("entity_a_id")
    id_b   = parsed.get("entity_b_id")

    if not type_a or not type_b or not id_a or not id_b:
        return "❌ Smart router: incomplete entity resolution from LLM"

    pair = tuple(sorted([type_a, type_b]))
    print(f"🔗 Smart router resolved: {type_a}({id_a}) ↔ {type_b}({id_b})")

    # ── Dispatch to correct handler ──────────────────────────

    if pair == ("PROCESS", "SUBPROCESS"):
        pid  = id_a if type_a == "PROCESS"    else id_b
        spid = id_a if type_a == "SUBPROCESS" else id_b
        return _do_link_process_subprocess(pid, spid, processes, subprocs)

    elif pair in [("PROCESS", "RISK"), ("RISK", "SUBPROCESS")]:
        pro_subpro_id   = id_a if type_a in ("PROCESS","SUBPROCESS") else id_b
        pro_subpro_type = type_a if type_a in ("PROCESS","SUBPROCESS") else type_b
        rid             = id_a if type_a == "RISK" else id_b
        return _do_link_process_risk(pro_subpro_id, pro_subpro_type, rid,
                                     processes, subprocs, risks)

    elif pair == ("CONTROL", "RISK"):
        rid = id_a if type_a == "RISK"    else id_b
        cid = id_a if type_a == "CONTROL" else id_b
        return _do_link_risk_control(rid, cid, risks, controls)

    elif pair == ("CONTROL", "TEST_PLAN"):
        tpid = id_a if type_a == "TEST_PLAN" else id_b
        cid  = id_a if type_a == "CONTROL"   else id_b
        return _do_link_test_plan_control(tpid, cid, test_plans, controls)

    elif pair == ("CONTROL", "TEST_STEP"):
        tsid = id_a if type_a == "TEST_STEP" else id_b
        cid  = id_a if type_a == "CONTROL"   else id_b
        return _do_link_test_step_control(tsid, cid, test_steps, controls)

    elif pair == ("TEST_PLAN", "TEST_STEP"):
        tpid = id_a if type_a == "TEST_PLAN" else id_b
        tsid = id_a if type_a == "TEST_STEP" else id_b
        return _do_link_test_plan_step(tpid, tsid, test_plans, test_steps)

    else:
        return f"❌ Unsupported link combination: {type_a} ↔ {type_b}"


# ─────────────────────────────────────────────────────────────
# LINK EXECUTORS  — each does DB insert + RAG save
# ─────────────────────────────────────────────────────────────

def _do_link_process_subprocess(process_id, sub_process_id, processes, subprocs):
    result = call_lambda({
        "action": "insert",
        "table":  "process_subprocess_map",
        "data":   {"process_id": process_id, "sub_process_id": sub_process_id}
    })
    map_id = result.get("inserted_id")

    p_rec  = get_record_by_id(processes, "process_id",     process_id)
    sp_rec = get_record_by_id(subprocs,  "sub_process_id", sub_process_id)

    save_process_to_rag("PROCESS_SUBPROCESS_LINK", {
        "process_id":              process_id,
        "sub_process_id":          sub_process_id,
        "process_name":            p_rec.get("process_name",      ""),
        "process_description":     p_rec.get("description",        ""),
        "process_department":      p_rec.get("department",         ""),
        "sub_process_name":        sp_rec.get("sub_process_name",  ""),
        "sub_process_description": sp_rec.get("description",       ""),
        "sub_process_department":  sp_rec.get("department",        ""),
        "sub_process_owner":       sp_rec.get("sub_process_owner", ""),
    }, map_id)

    return (f"✅ Linked Process '{p_rec.get('process_name', process_id)}' "
            f"↔ Sub-process '{sp_rec.get('sub_process_name', sub_process_id)}'")


def _do_link_process_risk(pro_subpro_id, pro_subpro_type, risk_id,
                          processes, subprocs, risks):
    result = call_lambda({
        "action": "insert",
        "table":  "process_subprocess_risk_map",
        "data":   {
            "pro_subpro_id":   pro_subpro_id,
            "pro_subpro_type": pro_subpro_type,
            "risk_id":         risk_id
        }
    })
    map_id = result.get("inserted_id")

    if pro_subpro_type == "PROCESS":
        entity_rec  = get_record_by_id(processes, "process_id",    pro_subpro_id)
        entity_name = entity_rec.get("process_name",     str(pro_subpro_id))
    else:
        entity_rec  = get_record_by_id(subprocs, "sub_process_id", pro_subpro_id)
        entity_name = entity_rec.get("sub_process_name", str(pro_subpro_id))

    risk_rec  = get_record_by_id(risks, "risk_id", risk_id)
    risk_name = risk_rec.get("risk_name", str(risk_id))

    save_process_to_rag("PROCESS_RISK_LINK", {
        "pro_subpro_id":    pro_subpro_id,
        "pro_subpro_type":  pro_subpro_type,
        "entity_name":      entity_name,
        "risk_id":          risk_id,
        "risk_name":        risk_name,
        "risk_description": risk_rec.get("description", ""),
        "risk_likelihood":  risk_rec.get("likelihood",  ""),
        "risk_impact":      risk_rec.get("impact",      ""),
    }, map_id)

    label = pro_subpro_type.replace("_", " ").title()
    return f"✅ Linked {label} '{entity_name}' ↔ Risk '{risk_name}'"


def _do_link_risk_control(risk_id, control_id, risks, controls):
    result = call_lambda({
        "action": "insert",
        "table":  "risk_control_map",
        "data":   {"risk_id": risk_id, "control_id": control_id}
    })
    map_id = result.get("inserted_id")

    risk_rec    = get_record_by_id(risks,    "risk_id",    risk_id)
    control_rec = get_record_by_id(controls, "control_id", control_id)

    save_process_to_rag("RISK_CONTROL_LINK", {
        "risk_id":             risk_id,
        "risk_name":           risk_rec.get("risk_name",   ""),
        "risk_description":    risk_rec.get("description", ""),
        "control_id":          control_id,
        "control_name":        control_rec.get("control_name",  ""),
        "control_type":        control_rec.get("control_type",  ""),
        "control_description": control_rec.get("description",   ""),
    }, map_id)

    return (f"✅ Linked Risk '{risk_rec.get('risk_name', risk_id)}' "
            f"↔ Control '{control_rec.get('control_name', control_id)}'")


def _do_link_test_plan_control(test_plan_id, control_id, test_plans, controls):
    result = call_lambda({
        "action": "insert",
        "table":  "test_plan_control_map",
        "data":   {"test_plan_id": test_plan_id, "control_id": control_id}
    })
    map_id = result.get("inserted_id")

    tp_rec = get_record_by_id(test_plans, "test_plan_id", test_plan_id)
    c_rec  = get_record_by_id(controls,   "control_id",   control_id)

    save_process_to_rag("TEST_PLAN_CONTROL_LINK", {
        "test_plan_id":        test_plan_id,
        "test_plan_name":      tp_rec.get("test_plan_name", ""),
        "test_plan_module":    tp_rec.get("module",         ""),
        "control_id":          control_id,
        "control_name":        c_rec.get("control_name",   ""),
        "control_type":        c_rec.get("control_type",   ""),
        "control_description": c_rec.get("description",    ""),
    }, map_id)

    return (f"✅ Linked Test Plan '{tp_rec.get('test_plan_name', test_plan_id)}' "
            f"↔ Control '{c_rec.get('control_name', control_id)}'")


def _do_link_test_step_control(test_step_id, control_id, test_steps, controls):
    result = call_lambda({
        "action": "insert",
        "table":  "test_step_control_map",
        "data":   {"test_step_id": test_step_id, "control_id": control_id}
    })
    map_id = result.get("inserted_id")

    ts_rec = get_record_by_id(test_steps, "test_step_id", test_step_id)
    c_rec  = get_record_by_id(controls,   "control_id",   control_id)

    save_process_to_rag("TEST_STEP_CONTROL_LINK", {
        "test_step_id":        test_step_id,
        "control_assertion":   ts_rec.get("control_assertion", ""),
        "step_order":          ts_rec.get("step_order",        ""),
        "control_area":        ts_rec.get("control_area",      ""),
        "control_id":          control_id,
        "control_name":        c_rec.get("control_name",       ""),
        "control_type":        c_rec.get("control_type",       ""),
        "control_description": c_rec.get("description",        ""),
    }, map_id)

    return (f"✅ Linked Test Step '{ts_rec.get('control_assertion', test_step_id)}' "
            f"↔ Control '{c_rec.get('control_name', control_id)}'")


def _do_link_test_plan_step(test_plan_id, test_step_id, test_plans, test_steps):
    result = call_lambda({
        "action": "insert",
        "table":  "test_plan_step_map",
        "data":   {"test_plan_id": test_plan_id, "test_step_id": test_step_id}
    })
    map_id = result.get("inserted_id")

    tp_rec = get_record_by_id(test_plans, "test_plan_id", test_plan_id)
    ts_rec = get_record_by_id(test_steps, "test_step_id", test_step_id)

    save_process_to_rag("TEST_PLAN_STEP_LINK", {
        "test_plan_id":      test_plan_id,
        "test_plan_name":    tp_rec.get("test_plan_name",    ""),
        "test_plan_module":  tp_rec.get("module",            ""),
        "test_step_id":      test_step_id,
        "control_assertion": ts_rec.get("control_assertion", ""),
        "step_order":        ts_rec.get("step_order",        ""),
        "control_area":      ts_rec.get("control_area",      ""),
    }, map_id)

    return (f"✅ Linked Test Plan '{tp_rec.get('test_plan_name', test_plan_id)}' "
            f"↔ Test Step '{ts_rec.get('control_assertion', test_step_id)}'")


# ─────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS  (called from system_prompts.py)
# ALL route through smart_link_router — works for ANY phrasing
# ─────────────────────────────────────────────────────────────

def link_process_subprocess(prompt: str):
    return smart_link_router(prompt)

def link_process_risk(prompt: str):
    return smart_link_router(prompt)

def link_risk_control(prompt: str):
    return smart_link_router(prompt)

def link_test_plan_control(prompt: str):
    return smart_link_router(prompt)

def link_test_step_control(prompt: str):
    return smart_link_router(prompt)

def link_test_plan_step(prompt: str):
    return smart_link_router(prompt)