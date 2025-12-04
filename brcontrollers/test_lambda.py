import boto3
import json

def test_lambda():
    client = boto3.client('lambda', region_name='us-east-1')

    payload = {
        "test": "IAM TEST"
    }

    response = client.invoke(
        FunctionName='YOUR_LAMBDA_FUNCTION_NAME',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    result = json.load(response['Payload'])
    print("Lambda Response:", result)

test_lambda()
