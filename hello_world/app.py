import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

# import requests

def get_secret():

    secret_name = "prod/testAWSSAM/test-key"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
             SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']

    return secret


def handle_get_hello(event):
    """ 處理測試點 GET /hello """
    print("Health check endpoint /hello was called.")

    response_body = {
        'message': 'Hello from your AI Chatroom backend.',
        'status': 'OK',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response_body)
    }

def lambda_handler(event, context):
    """ Lambda 主要進入點，這裡負責將請求陸游到正確的處理函式 """

    print(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'GET' and path == '/hello':
        return handle_get_hello(event)

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Not Found"})
    }
