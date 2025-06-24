import os
import json
import uuid
import boto3
import openai
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
OPENAI_API_KEY_SECRET_NAME = os.environ.get("OPENAI_API_KEY_SECRET_NAME")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")

dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)
openai_client = None

def get_openai_client():
    """
    取得 OpenAI 客戶端物件與讀取 Secret，並將其儲存至全域變數 openai_client
    避免每次請求都要重複初始化與讀取 AWS Secret
    """
    global openai_client
    if openai_client is None:
        print("Initializing OpenAI client for the first time...")
        try:
            secrets_client = boto3.client(service_name='secretsmanager', region_name=AWS_REGION_NAME)
            get_secret_value_response = secrets_client.get_secret_value(SecretId=OPENAI_API_KEY_SECRET_NAME)
            secret = json.loads(get_secret_value_response['SecretString'])
            api_key = secret['OPENAI_API_KEY']

            openai_client = openai.OpenAI(api_key=api_key)
            print("OpenAI client initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            raise e   
    return openai_client

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
        'body': json.dumps(response_body, ensure_ascii=False)
    }

def handle_get_conversations(event):
    """ 處理取得對話紀錄 GET /conversations?user_id... """
    print("Handling request to get conversation list.")
    try:
        query_params = event.get('queryStringParameters', {})
        user_id = query_params.get('user_id')

        if not user_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'user_id query parameter is required.'})}

        print(f"Querying conversations for user_id: {user_id}")

        response = table.query(
            IndexName='user-id-index',
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False
        )

        items = response.get('Items', [])
        print(f"Found {len(items)} conversations.")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(items, ensure_ascii=False)
        }
    except Exception as e:
        print(f"Error in handle_get_conversations: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})}

def handle_new_message_stream(event, response_stream):
    """ 處理創建新對話 POST /message """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id')
        conversation_id = body.get('conversation_id')
        user_message = body.get('message', '')
        
        if not user_id or not user_message:
            error_msg = json.dumps({'error': 'user_id and message are required!'})
            response_stream.write(error_msg.encode('utf-8'))
            return

        previous_response_id = None
        is_new_conversation = not conversation_id

        if is_new_conversation:
            print(f"User '{user_id}' is starting a NEW conversation.")
            conversation_id = str(uuid.uuid4())
        else: 
            print(f"User '{user_id}' is continuing conversation '{conversation_id}'.")
            response = table.get_item(Key={'conversation_id': conversation_id})
            if 'Item' in response:
                previous_response_id = response['Item'].get('latest_response_id')
                print(f"Found previous response ID: {previous_response_id}")
            else:
                is_new_conversation = True
                print(f"Warning: conversation_id '{conversation_id}' not found. Treating as new.")
        
        client = get_openai_client()
        print("Calling OpenAI Responses API...")
        stream = client.responses.create(
            model="gpt-4o",
            input=user_message,
            store=True,
            previous_response_id=previous_response_id,
            stream=True  # <-- 啟動串流
        )

        for chunk in stream:
            if chunk.output and chunk.output.content:
                for block in chunk.output.content:
                    if block.type == 'text_delta' and block.text_delta and block.text_delta.value:
                        text_chunk = block.text_delta.value
                        response_stream.write(text_chunk.encode('utf-8'))
        
        final_response = stream.get_final_response()
        latest_response_id = final_response.id
        print(f"Stream finished. Final response ID: {latest_response_id}")

        current_timestamp = datetime.now(timezone.utc).isoformat()
        if is_new_conversation:
            title = user_message[:20] + '...' if len(user_message) > 20 else user_message
            table.put_item(
                Item={
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'latest_response_id': latest_response_id,
                    'title': title,
                    'created_at': current_timestamp,
                    'last_updated_at': current_timestamp
                }
            )
            print(f"Created new conversation metadata in DynamoDB for conversation '{conversation_id}'.")
        else:
            table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression="set #resp_id = :r, #updated_at = :u",
                ExpressionAttributeNames={
                    '#resp_id': 'latest_response_id',
                    '#updated_at': 'last_updated_at'
                },
                ExpressionAttributeValues={
                    ':r': latest_response_id,
                    ':u': current_timestamp
                }
            )

    except Exception as e:
        print(f"Error in stream: {e}")
        error_msg = json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        response_stream.write(error_msg.encode('utf-8'))

def lambda_handler(event, context):
    """ Lambda 主要進入點，這裡負責將請求路由到正確的處理函式 """
    http_method = event.get('httpMethod')
    path = event.get('path')

    is_streaming_request = (http_method == 'POST' and path == '/message')

    if is_streaming_request:
        response_stream = event.pop("response_stream", None)
        event.pop("aws_request_id", None)
        print(f"Received event: {json.dumps(event)}")

        response_stream.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Access-Control-Allow-Origin: *\r\n"
            b"\r\n"
        )

        try:
            handle_new_message_stream(event, response_stream)
        except Exception as e:
            print(f"Top-level error: {e}")
            error_msg = json.dumps({"error": "An unexpected error occurred"})
            response_stream.write(error_msg.encode('utf-8'))
        finally:
            if response_stream:
                response_stream.close()

    else:
        print(f"Non-streaming request received; {json.dumps(event)}")

        if http_method == 'GET' and path == '/hello':
            return handle_get_hello(event)
        if http_method == 'GET' and path == '/conversations':
            return handle_get_conversations(event)
        
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Not Found"})
        }