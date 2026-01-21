import json
import os
import boto3
from dotenv import load_dotenv

# Load .env
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

MODEL_ID = "amazon.nova-lite-v1:0"  # lightweight, fast, cheap

def bedrock_healthcheck():
    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "inputText": "Hello Bedrock"
            })
        )

        result = json.loads(response["body"].read())

        print("✅ Bedrock connection successful!")
        print("Model response:", result)

    except Exception as e:
        print("❌ Bedrock connection failed")
        print(type(e).__name__, str(e))

if __name__ == "__main__":
    bedrock_healthcheck()
