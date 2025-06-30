import json
from common.aws_clients import get_dynamodb_table

table = get_dynamodb_table()

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

def handle_get_conversations(event, context):
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

def lambda_handler(event, context):
    """ Lambda 主要進入點，這裡負責將請求路由到正確的處理函式 """
    print("Received event:", json.dumps(event))

    try:
        request_context = event.get('requestContext', {})
        http_info = request_context.get('http', {}) 

        method = http_info.get('method')
        path = http_info.get('path')

        print(f"Request received for {method} {path}")

        if method == 'GET' and path == '/hello':
            return handle_get_hello(event)

        if method == 'GET' and path == '/conversations':
            return handle_get_conversations(event, context)
            
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "headers": { "Content-Type": "application/json" },
            "body": json.dumps({"error": "Internal server error"})
        }
    return {
        "statusCode": 404,
        "headers": { "Content-Type": "application/json" },
        "body": json.dumps({"error": "Not Found"})
    }
