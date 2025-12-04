import boto3
import json

def call_lambda():
    client = boto3.client("lambda", region_name="ap-south-1")

    payload = {"action": "getTime"}

    response = client.invoke(
        FunctionName="grc-mysql-test",
        InvocationType="RequestResponse",
        Payload=json.dumps(payload)
    )

    data = json.loads(response['Payload'].read())

    # Parse lambda body JSON
    body = json.loads(data["body"])

    return body["current_time"]
