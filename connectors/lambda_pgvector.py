# db_pgvector.py

import json
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


class PGVectorDB:
    def __init__(self, function_name, region="ap-south-1"):
        self.function_name = function_name

        try:
            self.lambda_client = boto3.client(
                "lambda",
                region_name=region
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create Lambda client: {e}")

    def execute(self, query: str, params=None):
        if not self.lambda_client:
            raise RuntimeError("Lambda client not initialized")

        payload = {
            "query": query,
            "params": params
        }

        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload)
            )
        except NoCredentialsError:
            raise RuntimeError(
                "AWS credentials not found. Run `aws configure`."
            )
        except ClientError as e:
            raise RuntimeError(f"AWS Lambda invoke failed: {e}")

        response_payload = json.loads(response["Payload"].read())

        if response.get("FunctionError"):
            raise RuntimeError(response_payload)

        body = response_payload.get("body")

        if isinstance(body, str):
            body = json.loads(body)

        return body.get("rows", [])
