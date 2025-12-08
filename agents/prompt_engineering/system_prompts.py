import mysql.connector
import json
from groq import Groq

# ✅ Groq Client
client = Groq(api_key="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")

# -----------------------------
# Database Connection
# -----------------------------
def get_db():
    print("🔌 Connecting to database...")
    try:
        conn = mysql.connector.connect(
            host="44.218.167.158",
            user="admin",
            password="GoodLuck25",
            database="DB_GRC360",
            connection_timeout=5,
            use_pure=True,
            autocommit=True
        )
        print("✅ Database Connected")
        return conn
    except mysql.connector.Error as e:
        print("❌ Database Connection Failed:", e)
        return None

# -----------------------------
# CATEGORY DETECTION USING INTENT
# -----------------------------
def detect_category(intent, raw_text):
    db = get_db()
    if not db:
        return None

    cursor = db.cursor(dictionary=True)

    # Direct mapping: check if intent matches category
    cursor.execute("SELECT category FROM prompt_templates WHERE category LIKE %s", (intent,))
    row = cursor.fetchone()
    if row:
        cursor.close()
        db.close()
        return row["category"]

    # Fallback: keyword match
    cursor.execute("SELECT category FROM prompt_templates")
    categories = cursor.fetchall()
    raw = raw_text.lower()
    for c in categories:
        if c["category"].lower() in raw:
            cursor.close()
            db.close()
            return c["category"]

    cursor.close()
    db.close()
    return categories[0]["category"] if categories else None

# -----------------------------
# FETCH PROMPT TEMPLATE
# -----------------------------
def fetch_prompt_template(category):
    db = get_db()
    if not db:
        return None

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT content FROM prompt_templates WHERE category=%s", (category,))
    template = cursor.fetchone()
    cursor.close()
    db.close()
    return template["content"] if template else None

# -----------------------------
# INSERT INTO DB
# -----------------------------
def insert_into_table(data):
    db = get_db()
    if not db:
        return False

    cursor = db.cursor()
    query = """
      INSERT INTO processes
      (process_name, description, department,
       process_owner, frequency, triggers, outcomes)
      VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    # Ensure all keys exist with defaults
    payload = {
        "process_name": data.get("process_name", ""),
        "description": data.get("description", ""),
        "department": data.get("department", ""),
        "owner": data.get("owner", ""),
        "frequency": data.get("frequency", ""),
        "triggers": data.get("triggers", []),
        "outcomes": data.get("outcomes", [])
    }

    cursor.execute(query, (
        payload["process_name"],
        payload["description"],
        payload["department"],
        payload["owner"],
        payload["frequency"],
        ",".join(payload["triggers"]),
        ",".join(payload["outcomes"])
    ))

    db.commit()
    cursor.close()
    db.close()
    return True

# =====================================================
# ✅ MAIN FUNCTION CALLED FROM INTENT AGENT
# =====================================================
def run_pipeline(intent, raw_text):

    try:
        print("📤 Received from IntentAgent:", intent)

        # Step 1: Detect category
        category = detect_category(intent, raw_text)
        if not category:
            return "❌ No category mapping found."
        print("📂 Category:", category)

        # Step 2: Fetch prompt template
        template = fetch_prompt_template(category)
        if not template:
            return "❌ Prompt template not found."

        # ✅ Strong JSON instruction
        final_prompt = f"""
{template}

### Raw Text:
{raw_text}

### Instructions:
Return ONLY valid JSON.
❌ Do NOT wrap in ```json or markdown.
❌ Do NOT add explanation.
✅ Output must start with {{ and end with }}.
"""

        # Step 3: Call Groq AI
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.2
        )

        output = response.choices[0].message.content.strip()
        print("📌 AI Output →", output)

        # Step 4: Clean Markdown if present
        clean = output

        if clean.startswith("```"):
            clean = clean.replace("```json", "").replace("```", "").strip()

        # Step 5: Parse JSON safely
        try:
            data = json.loads(clean)
        except json.JSONDecodeError as e:
            print("❌ JSON Parse Error:", e)
            print("📌 RAW OUTPUT:", output)
            return "❌ AI returned invalid JSON."

        # Step 6: Insert into DB
        success = insert_into_table(data)
        if success:
            return "✅ Row inserted successfully into database!"
        else:
            return "❌ Failed to insert into DB."

    except Exception as e:
        print("❌ Pipeline Crash:", str(e))
        return f"❌ System Error: {str(e)}"

