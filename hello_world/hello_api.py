import json
from datetime import datetime, timezone
from fastapi import FastAPI, Query, HTTPException
from common.aws_clients import get_dynamodb_table
from common.models import HelloResponse, ConversationItem, ConversationResponse

app = FastAPI()
table = get_dynamodb_table()

@app.get("/hello", response_model=HelloResponse)
async def get_hello():
    """ 
    處理測試點 GET /hello
    FastAPI 會自動將回傳字典轉為 JSON 
    """
    print("Health check endpoint /hello was called.")
    
    return {
        'message': 'Hello from your AI Chatroom backend. And test.',
        'status': 'OK',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@app.get("/conversations", response_model=ConversationResponse)
async def get_conversations(
    user_id: str = Query(..., description="The ID of the user to fetch conversation for")
):
    """ 
    處理取得對話紀錄 GET /conversations?user_id... 
    """
    print(f"Handling request to get conversation list for user_id: {user_id}.")
    try:
        response = table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False
        )

        items = response.get('Items', [])
        print(f"Found {len(items)} conversations.")

        return {"items": items}
    except Exception as e:
        print(f"Error in handle_get_conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# def lambda_handler(event, context):
""" 
使用 Docker 方式部屬 lambda 無須 lambda_handle
uvicorn 會直接運行這個 'app'
"""
