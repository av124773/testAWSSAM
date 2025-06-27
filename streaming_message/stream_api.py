import os
import json
import uuid
import boto3
import openai
import traceback
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
OPENAI_API_KEY_SECRET_NAME = os.environ.get("OPENAI_API_KEY_SECRET_NAME")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME")

dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)
openai_client = None

app = FastAPI()

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

async def stream_generator(body: dict):
    """ 
    處理創建新對話 POST /message 
    串流生成器
    """
    print("DEBUG: stream_generator has started.")

    latest_response_id = None

    conversation_id = body.get('conversation_id')
    print(f"DEBUG: conversation_id = {conversation_id}")

    user_id = body.get('user_id')
    print(f"DEBUG: user_id = {user_id}")

    user_message = body.get('message', '')
    print(f"DEBUG: user_message received: {'Yes' if user_message else 'No'}")

    is_new_conversation = not conversation_id
    stream = None

    try:
        if not user_id or not user_message:
            print("DEBUG: user_id or message is missing. Yielding error.")
            yield json.dumps({'error': 'user_id and message are required!'}).encode('utf-8')
            return

        previous_response_id = None
        print(f"DEBUG: is_new_conversation = {is_new_conversation}")

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

        for event in stream:
            print(f"DEBUG: Processing event of type: '{event.type}'")
            if event.type == 'response.created':
                print("DEBUG: 'response.created' event FOUND. Attempting to capture ID.")
                latest_response_id = event.response.id
                print(f"DEBUG: Captured Response ID: {latest_response_id}")

            if event.type == 'response.output_text.delta':
                if event.delta:
                    yield event.delta.encode("utf-8")

        print(f"DEBUG: Loop finished. Final value of latest_response_id is: '{latest_response_id}'")

        
    except Exception as e:
        print(f"Error in stream: {e}")
        traceback.print_exc()
        yield json.dumps({'error': 'An error occurred during streaming.'}).encode('utf-8')

    finally:
        if latest_response_id and conversation_id:
            print(f"Stream finished. Final response ID: {latest_response_id}. Updating DB...")
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
            print("DB update complete.")

@app.post("/message")
async def handle_new_message_stream(request: Request):
    """ FastAPI 進入點，接收請求並回傳串流回應 """
    print("DEBUG: Entered handle_new_message_stream function.")
    try:
        print("DEBUG: Awaiting request.json().")
        body = await request.json()
        print(f"DEBUG: Request body parsed successfully: {body}")
        
        print("DEBUG: Creating StreamingResponse with stream_generator.")
        response = StreamingResponse(stream_generator(body), media_type="text/plain")
        print("DEBUG: StreamingResponse object created. Returning response.")
        return response
        
    except Exception as e:
        print(f"FATAL: Exception in handle_new_message_stream: {e}")
        traceback.print_exc()
        # 如果請求解析失敗，回傳一個標準的 JSON 錯誤
        return { "error": "Failed to process request body.", "details": str(e) }


