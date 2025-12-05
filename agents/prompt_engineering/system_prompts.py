import mysql.connector
from openai import OpenAI
import json
# -----------------------------
# OpenAI Client
# -----------------------------
client = OpenAI(api_key="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" \
"")

# -----------------------------
# Database Connection Helper
# -----------------------------
def get_db():
    return mysql.connector.connect(
        host="grc360.cmhggsagqy8d.us-east-1.rds.amazonaws.com",
        user="admin",
        password="GoodLuck25",
        database="DB_GRC360"
    )

# -----------------------------
# Detect Category based on raw text
# -----------------------------
def detect_category(raw_text):
    """
    Simplified: Just return the first template that matches the category name in text,
    or None if no match. Since we don't have keywords, detection can be basic.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT category FROM prompt_templates")
    templates = cursor.fetchall()

    cursor.close()
    db.close()

    raw_lower = raw_text.lower()
    for temp in templates:
        if temp["category"].lower() in raw_lower:
            return temp["category"]

    # If no exact match, return the first category (or None)
    return templates[0]["category"] if templates else None

# -----------------------------
# Fetch Template Content
# -----------------------------
def fetch_prompt_template(category):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT content FROM prompt_templates WHERE category=%s", (category,))
    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result["content"] if result else None

# -----------------------------
# Check if table exists
# -----------------------------
def check_table_exists(table_name):
    db = get_db()
    cursor = db.cursor()

    query = "SHOW TABLES LIKE %s"
    cursor.execute(query, (table_name,))
    exists = cursor.fetchone()

    cursor.close()
    db.close()

    return exists is not None

# -----------------------------
# Insert structured data JSON
# -----------------------------
def insert_into_table(table_name, data):
    db = get_db()
    cursor = db.cursor()

    query = """
        INSERT INTO processes (process_name, description, department, process_owner, frequency, triggers, outcomes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        data.get("process_name"),
        data.get("description"),
        data.get("department"),
        data.get("owner"),
        data.get("frequency"),
        ",".join(data.get("triggers")) if isinstance(data.get("triggers"), list) else data.get("triggers"),
        ",".join(data.get("outcomes")) if isinstance(data.get("outcomes"), list) else data.get("outcomes")
    ))

    db.commit()
    cursor.close()
    db.close()


# ---------------------------------------------------
# MAIN EXECUTION FLOW
# ---------------------------------------------------

#raw_text = 


def GetCategoryfromIntentAgent(intent, raw_text):
    category = intent
    if not category:
        print("❌ No matching template found for this text.")
    exit()

    print(f"🔍 Detected Category: {category}")

    if not check_table_exists(category.lower()):
        print(f"⚠ Table '{category.lower()}' does not exist. Cannot insert data.")
    exit()

    template = fetch_prompt_template(category)

    final_prompt = f"""
    {template}

    ### Raw Text:
    {raw_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": final_prompt}]
    )

    structured_data = response.choices[0].message.content
    print("\n📌 Structured Output:\n", structured_data)

    json_data = json.loads(structured_data)
    insert_into_table(category.lower(), json_data)

    print("✅ Data successfully inserted into", category.lower(), "table.")
