from services.main_bedrock_client import get_bedrock_client
from pathlib import Path
import json

# ---- GUARDRAIL CONFIG (ONE PLACE) ----
grdpath = Path(__file__).resolve().parent.parent / "config" / "aws_bedrock_credentials.json"

with open(grdpath, "r") as f:
    path = json.load(f)
GUARDRAIL_ID = path["guardrail_id"]
GUARDRAIL_VERSION = path["guardrail_version"]

client = get_bedrock_client()


def validate_with_guardrail(
    text: str,
    source: str  # INPUT or OUTPUT
):
    """
    Validates any text using Bedrock Guardrails

    Returns:
    {
        is_valid: bool,
        action: ALLOWED | GUARDRAIL_INTERVENED,
        details: raw_response
    }
    """

    response = client.apply_guardrail(
        guardrailIdentifier=GUARDRAIL_ID,
        guardrailVersion=GUARDRAIL_VERSION,
        source=source,
        content=[{"text": {"text": text}}],
        outputScope="INTERVENTIONS"
    )

    action = response.get("action")

    return {
    "is_valid": action != "GUARDRAIL_INTERVENED",
    "action": action,
    "details": response
}