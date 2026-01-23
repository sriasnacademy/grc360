import json
import os
import boto3
from dotenv import load_dotenv

# Load AWS creds from .env
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = "amazon.nova-lite-v1:0"  # lightweight Bedrock model

# ----------------------------
# Bedrock client
# ----------------------------
def get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

# ----------------------------
# Output Guardrail
# ----------------------------
def bedrock_duplicate_check(user_input, rag_results, top_k=3):
    """
    Uses Bedrock to decide if a candidate is a true duplicate
    """
    client = get_bedrock_client()
    
    top_results = rag_results[:top_k]
    similar_processes = [{"id": r[2], "text": r[3], "similarity": r[4]} for r in top_results]

    prompt = f"""
You are an AI assistant that enforces guardrails on process insertion.

User wants to insert: "{user_input}"

These are the similar processes found in the database:
{json.dumps(similar_processes, indent=2)}

Your task:
1. Decide if the new process is a duplicate (same intent + same entities).
2. If duplicate, respond with: 
   {{ "duplicate": true, "existing_process_id": <id>, "message": "Duplicate found. Insertion blocked." }}
3. If safe to insert, respond with: 
   {{ "duplicate": false, "message": "Process can be safely inserted." }}

Respond ONLY in valid JSON.
"""

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({"inputText": prompt})
    )

    # Bedrock returns bytes, decode JSON
    output_text = json.loads(response["body"].read())["outputText"]

    try:
        decision = json.loads(output_text)
    except json.JSONDecodeError:
        decision = {"duplicate": False, "message": "Process can be safely inserted."}

    return decision
