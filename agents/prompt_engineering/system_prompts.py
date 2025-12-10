from groq import Groq
from connectors.lambda_mysql import call_lambda
import json

# ----------------------------
# Groq AI Client
# ----------------------------
client = Groq(api_key="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")

# ----------------------------
# Detect category using Lambda
# ----------------------------
def detect_category(intent, raw_text):
    # Direct mapping: intent = category
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"category": intent}
    }
    result = call_lambda(payload)
    if result["count"] > 0:
        return result["records"][0]["category"]

    # Fallback: keyword matching
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "columns": ["category"]
    }
    result = call_lambda(payload)
    raw_lower = raw_text.lower()
    for item in result["records"]:
        if item["category"].lower() in raw_lower:
            return item["category"]

    return result["records"][0]["category"] if result["records"] else None


# ----------------------------
# Fetch prompt template using Lambda
# ----------------------------
def fetch_prompt_template(category):
    payload = {
        "action": "select",
        "table": "prompt_templates",
        "where": {"category": category}
    }
    result = call_lambda(payload)
    if result["count"] == 0:
        return None
    return result["records"][0]["content"]


# ----------------------------
# Insert into DB using Lambda
# ----------------------------
def insert_into_table(data):
    payload = {
        "action": "insert",
        "table": "processes",
        "data": {
            "process_name": data.get("process_name", ""),
            "description": data.get("description", ""),
            "department": data.get("department", ""),
            "process_owner": data.get("owner", ""),
            "frequency": data.get("frequency", ""),
            "triggers": ",".join(data.get("triggers", [])),
            "outcomes": ",".join(data.get("outcomes", []))
        }
    }
    call_lambda(payload)
    return True


# ----------------------------
# Main pipeline function
# ----------------------------
def run_pipeline(intent, raw_text):
    try:
        print("📤 Intent received:", intent)

        # Step 1: Detect category
        category = detect_category(intent, raw_text)
        if not category:
            return "❌ No category mapping found."
        print("📂 Category:", category)

        # Step 2: Fetch prompt template
        template = fetch_prompt_template(category)
        if not template:
            return "❌ Prompt template not found."

        # Step 3: Build strong JSON prompt for Groq AI
        final_prompt = f"""
{template}

### Raw Text:
{raw_text}

### Instructions:
Return ONLY valid JSON.
❌ Do NOT wrap in markdown.
✅ Output must start with {{ and end with }}.
"""

        # Step 4: Call Groq AI
        response_ai = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2
        )

        output = response_ai.choices[0].message.content.strip()
        clean = output.replace("```json", "").replace("```", "").strip()

        # Step 5: Parse AI JSON output
        data = json.loads(clean)

        # Step 6: Insert into DB via Lambda
        insert_into_table(data)

        return "✅ Row inserted successfully via Lambda!"

    except json.JSONDecodeError:
        return "❌ AI returned invalid JSON."

    except RuntimeError as e:
        return str(e)

    except Exception as e:
        return f"❌ Pipeline Error: {str(e)}"
