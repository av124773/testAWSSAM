import os
import json
import uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone

# --- 全域變數 ---
OPENAI_API_KEY_SECRET_NAME = os.environ.get("OPENAI_API_KEY_SECRET_NAME")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")

def get_secret():
    secret_name = "prod/testAWSSAM/test-key"
    region_name = "us-east-1"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return secret

def handle_get_hello(event):
    """ 處理測試點 GET /hello """
    print("Health check endpoint /hello was called.")
    response_body = {
        'message': 'Hello from your AI Chatroom backend. And test.',
        'status': 'OK',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'OPENAI_API_KEY_SECRET_NAME': OPENAI_API_KEY_SECRET_NAME,
        'AWS_REGION_NAME': AWS_REGION_NAME
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

        if conversation_id is None or conversation_id == "":
            # 新對話
            print("Request received for a NEW conversation.")
            conversation_id = str(uuid.uuid4())
            reply_message = f"成功創建新對話。你的訊息是: '{user_message}'"
        else:
            # 既有對話
            print(f"Request received for EXISTING conversation: {conversation_id}")
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
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }

def lambda_handler(event, context):
    """ Lambda 主要進入點，這裡負責將請求路由到正確的處理函式 """
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