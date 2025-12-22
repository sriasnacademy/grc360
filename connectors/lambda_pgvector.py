# db_pgvector.py

import json
import boto3


class PGVectorDB:

    #def __init__(self, function_name="grc-vectordb"):
    #   self.lambda_client = boto3.client("lambda") 
    #   self.function_name = function_name

    def __init__(self, function_name="grc-vectordb"):   #Meghana
        self.function_name = function_name
        self.lambda_client = None

    def _get_lambda_client(self):
        if self.lambda_client is None:
            self.lambda_client = boto3.client(
                "lambda",
                region_name="ap-south-1"
            )
        return self.lambda_client   #Meghana

    def execute(self, query: str, params=None):
        """
        Calls AWS Lambda and returns rows.
        """
        payload = {
            "query": query,
            "params": params
        }

        response = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        response_payload = json.loads(response["Payload"].read())

        if response.get("FunctionError"):
            raise Exception(response_payload)

        body = response_payload.get("body")

        # body may be string (API Gateway style)
        if isinstance(body, str):
            body = json.loads(body)

        return body.get("rows", [])
