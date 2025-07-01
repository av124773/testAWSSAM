import boto3
import json
import openai
from functools import lru_cache
from .config import settings

@lru_cache(maxsize=1)
def get_dynamodb_table():
    print("Initializing DynamoDB table resource...")
    dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION_NAME)
    return dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

@lru_cache(maxsize=1)
def get_openai_client() -> openai.OpenAI:
    print("Initializing OpenAI client for the first time...")
    secrets_client = boto3.client(service_name='secretsmanager', region_name=settings.AWS_REGION_NAME)
    get_secret_value_response = secrets_client.get_secret_value(SecretId=settings.OPENAI_API_KEY_SECRET_NAME)
    secret = json.loads(get_secret_value_response['SecretString'])
    api_key = secret['OPENAI_API_KEY']
    return openai.OpenAI(api_key=api_key)
