import json
import boto3
from pathlib import Path


def get_bedrock_client():
    """
    Creates and returns Bedrock Runtime client
    using credentials from config file
    """
    config_path = Path(__file__).resolve().parent.parent / "config" / "aws_bedrock_credentials.json"

    with open(config_path, "r") as f:
        cfg = json.load(f)

    return boto3.client(
        "bedrock-runtime",
        region_name=cfg["region"],
        aws_access_key_id=cfg["aws_access_key_id"],
        aws_secret_access_key=cfg["aws_secret_access_key"]
    )