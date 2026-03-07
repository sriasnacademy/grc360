import json
import boto3
from connectors import mysqldb_engine
# ----------------------------
# AWS Lambda Info
# ----------------------------
LAMBDA_NAME = "grc-mysql-test"
AWS_ACCESS_KEY_ID = "AKIA2OAJTQGXVYLRTKTB"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "ap-south-1"  # change if needed

# ----------------------------
# Initialize Lambda client
# ----------------------------
def get_lambda_client():
    try:
        return boto3.client(
            "lambda",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
    except Exception as e:
        raise RuntimeError(f"❌ Failed to initialize Lambda client: {str(e)}")


# ----------------------------
# Call Lambda function
# ----------------------------
def call_lambda(payload):
    lambda_client = mysqldb_engine.lambda_handler(payload,"")
    try:
       

        # raw = lambda_client["records"]
        # data = json.loads(raw)

        # if data.get("statusCode") != 200:
        #     raise Exception(data.get("body"))

        # return json.loads(data["body"])

        response_data = json.loads(lambda_client['body'])
    
        records = response_data.get("records", [])
    
        return response_data

    except Exception as e:
        raise RuntimeError(f"❌ Lambda invocation failed: {str(e)}")