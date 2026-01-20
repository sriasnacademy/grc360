import boto3, json

def bedrock_healthcheck():
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    response = client.invoke_model(
        modelId="amazon.titan-text-lite-v1",
        body=json.dumps({
            "inputText": "ping",
            "textGenerationConfig": {"maxTokenCount": 5}
        })
    )

    return json.loads(response["body"].read())
