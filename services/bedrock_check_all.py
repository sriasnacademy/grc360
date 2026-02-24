import boto3
import os
from services.rag_retrieval_service import (
    extract_process_ids_from_rag_for_duplicate_check,
    rag_find_process_ids
)
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")      # kt0thsln579m
GUARDRAIL_VERSION = "1"                  # ✅ CORRECT

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION
)


def check_content_with_guardrails(user_text: str):
    """
    ✔ Blocks harmful content
    ✔ Masks sensitive data
    ✔ Does NOT change pipeline behaviour
    """

    try:
        print("In Guardrail File")
        print(GUARDRAIL_ID)
        print(GUARDRAIL_VERSION)
        response = bedrock.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source="INPUT",
            content=[
                {
                    "text": {
                        "text": user_text
                    }
                }
            ]
        )
        print(response)
        # 🔍 DEBUG (TEMP – VERY IMPORTANT)
        print("🛡 Guardrail action:", response.get("action"))

        action = response.get("action")
        print(action)
        if action == "BLOCK":
            return {
                "allowed": False,
                "message": "❌ Input blocked due to harmful content.",
                "safe_text": None
            }
        # ===============================
        # STEP 1: RAG DUPLICATE CHECK
        # ===============================

        rag_results = rag_find_process_ids(
            query=user_text,
            entitytype="PROCESS",
            top_k=3
        )
        print(rag_results)
        duplicate_process_ids = extract_process_ids_from_rag_for_duplicate_check(
            rag_results,
            min_similarity=0.7
        )

        if duplicate_process_ids:
            print("🚫 Duplicate process IDs found:", duplicate_process_ids)
            return {
                "allowed":False,
                "message":"❌ Process already exists. Duplicate detected.",
                "safe_text":user_text
                }
        else:
            outputs = response.get("outputs", [])
            print(outputs)
            safe_text = user_text

        if outputs:
            safe_text = outputs[0]["text"]["text"]

        return {
            "allowed": True,
            "message": "✅ Guardrail passed",
            "safe_text": safe_text
        }

    except Exception as e:
        return {
            "allowed": False,
            "message": "⚠ Guardrail error – continuing pipeline",
            "safe_text": {e}
        }
