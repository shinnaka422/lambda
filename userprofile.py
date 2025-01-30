import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# DynamoDBのリソースを作成
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('LineUserProfiles')  # 使用するテーブル名

def decimal_to_dict(obj):
    """
    Decimal 型を含むオブジェクトをJSONに変換可能な型に変換する関数。
    """
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)  # 整数に変換
        else:
            return float(obj)  # 小数に変換
    raise TypeError("Type not serializable")

def lambda_handler(event, context):
    # デフォルトのレスポンスヘッダー（CORS対応）
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }

    # クエリパラメータからLineIDを取得
    line_id = event.get('queryStringParameters', {}).get('lineId')

    # LineIDが提供されていない場合
    if not line_id:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'message': 'lineId is required as a query parameter'
            })
        }
    
    try:
        # DynamoDBからデータを取得
        response = table.get_item(
            Key={'lineId': line_id}
        )
        
        if 'Item' in response:
            # DynamoDBから取得したデータをJSON形式に変換
            profile = response['Item']
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Profile retrieved successfully!',
                    'data': profile
                }, default=decimal_to_dict)
            }
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Profile not found'
                })
            }
    
    except ClientError as e:
        # エラーハンドリング
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Error retrieving profile',
                'error': str(e)
            })
        }