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

def handle_new_message(event):
    """ 處理創建新對話 POST /message """
    try:
        body = json.loads(event.get('body', '{}'))
        conversation_id = body.get('conversation_id')
        user_message = body.get('message', '')

        if conversation_id is None:
            # 新對話
            print("Request received for a NEW conversation.")
            conversation_id = str(uuid,uuid4())
            # 假裝AI回復(暫)
            reply_message = f"成功創建新對話。你的訊息是: '{user_message}'"
        else:
            # 既有對話
            print(f"Request received for EXISTING conversation: {conversation_id}")
            # 假裝AI回復(暫)
            reply_message = f"對話ID: '{conversation_id}' 中收到訊息: '{user_message}'"
        
        response_body = {
            'conversation_id': conversation_id,
            'reply': reply_message
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 200,
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }

def lambda_handler(event, context):
    """ Lambda 主要進入點，這裡負責將請求陸游到正確的處理函式 """

    print(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'GET' and path == '/hello':
        return handle_get_hello(event)

    if http_method == 'POST' and path == '/message':
        return handle_new_message(event)
    

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Not Found"})
    }
