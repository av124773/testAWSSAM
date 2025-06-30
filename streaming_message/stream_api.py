import uuid
import traceback
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from common.aws_clients import get_dynamodb_table, get_openai_client
from common.models import MessageRequest

app = FastAPI()

async def stream_generator(req: MessageRequest):
    """ 
    處理創建新對話 POST /message 
    串流生成器
    """
    print("DEBUG: stream_generator has started.")

    latest_response_id = None

    conversation_id = req.conversation_id
    print(f"DEBUG: conversation_id = {conversation_id}")

    user_id = req.user_id
    print(f"DEBUG: user_id = {user_id}")

    user_message = req.message
    print(f"DEBUG: user_message received: {'Yes' if user_message else 'No'}")

    is_new_conversation = not conversation_id
    stream = None

    try:
        table = get_dynamodb_table()

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
async def handle_new_message_stream(request: MessageRequest):
    """ FastAPI 進入點，接收請求並回傳串流回應 """
    return StreamingResponse(stream_generator(request), media_type='text/event-stream')
