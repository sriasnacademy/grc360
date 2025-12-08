import json
import mysql.connector
from models.my_llm_client import LLMClient
from agents.prompt_engineering.system_prompts import run_pipeline


class IntentAgent:

    # -----------------------------
    # Database Connection
    # -----------------------------
    @staticmethod
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
    # Fetch Intent Prompt Template
    # -----------------------------
    @staticmethod
    def fetch_prompt_template(category="INTENT_CLASSIFICATION"):

        db = IntentAgent.get_db()
        if not db:
            return None

        # ✅ buffered=True fixes "Unread result found"
        cursor = db.cursor(dictionary=True, buffered=True)

        cursor.execute(
            "SELECT content FROM prompt_templates WHERE category=%s",
            (category,)
        )

        rows = cursor.fetchall()   # ✅ Read ALL rows

        cursor.close()
        db.close()

        return rows[0]["content"] if rows else None

    # -----------------------------
    # Init
    # -----------------------------
    def __init__(self):
        self.llm = LLMClient()

    # -----------------------------
    # Intent Detection
    # -----------------------------
    def classify_intent(self, raw_text):

        try:
            # ✅ Fetch intent prompt from DB
            template = IntentAgent.fetch_prompt_template("INTENT_CLASSIFICATION")

            if not template:
                print("⚠ INTENT_CLASSIFICATION template missing in DB.")
                return "OTHER", "❌ Intent prompt missing in database"

            # ✅ Construct prompt
            prompt = f"""
{template}

### Input:
{raw_text}

### Rules:
Return STRICT JSON only.
Do NOT wrap in markdown.
Format:
{{ "intent": "VALUE" }}
"""

            # ✅ Call LLM
            response = self.llm.generate(prompt)

            print("🔎 RAW INTENT RESPONSE:", repr(response))

            # ✅ Handle empty output
            if not response or response.strip() == "":
                intent = "OTHER"
            else:
                clean = response.strip()

                # ✅ Remove markdown fences if any
                if clean.startswith("```"):
                    clean = clean.replace("```json", "").replace("```", "").strip()

                # ✅ Parse JSON
                try:
                    parsed = json.loads(clean)
                    intent = parsed.get("intent", "OTHER")
                except Exception as e:
                    print("❌ JSON PARSE ERROR:", e)
                    intent = "OTHER"

            print("🧠 Intent Detected:", intent)

            # ✅ Call pipeline
            status = run_pipeline(intent, raw_text)

            if not status:
                status = "⚠ System returned no response."

            return intent, status

        except Exception as e:
            print("❌ INTENT AGENT CRASH:", str(e))
            return "OTHER", f"❌ Intent Agent Error: {str(e)}"
