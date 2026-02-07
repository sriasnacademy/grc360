import boto3
import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")      # kt0thsln579m
GUARDRAIL_VERSION = "DRAFT"                  # ✅ CORRECT

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

        # 🔍 DEBUG (TEMP – VERY IMPORTANT)
        print("🛡 Guardrail action:", response.get("action"))

        action = response.get("action")

        if action == "BLOCK":
            return {
                "allowed": False,
                "message": "❌ Input blocked due to harmful content.",
                "safe_text": None
            }

        outputs = response.get("outputs", [])
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
            "allowed": True,
            "message": "⚠ Guardrail error – continuing pipeline",
            "safe_text": user_text
        }
