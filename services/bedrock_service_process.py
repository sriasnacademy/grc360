import json
import os
import boto3
from dotenv import load_dotenv

# ================= LOAD ENV =================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

print("✅ AWS credentials loaded")

# ================= INPUT =================

user_text = """
My name is Megha.
My email is megha@gmail.com.
My phone number is 9876543210.
"""

prompt = f"""
Repeat the text below exactly, but mask any sensitive information.

Text:
{user_text}
"""

payload = {
    "messages": [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]
}

# ================= GUARDRAIL =================

response = bedrock_runtime.invoke_model(
    modelId="amazon.nova-micro-v1:0",
    body=json.dumps(payload),
    guardrailIdentifier="kt0thsln579m",
    guardrailVersion="DRAFT",
    contentType="application/json",
    accept="application/json",
)

# ================= OUTPUT =================

result = json.loads(response["body"].read())
print("\n🔐 MASKED OUTPUT:\n")
print(result["output"]["message"]["content"][0]["text"])
