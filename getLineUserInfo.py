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
    # 受け取るデータ（lineIdをURLパスパラメータとして渡す場合）
    lineId = event.get('pathParameters', {}).get('lineId', None)

    # デフォルトのレスポンスヘッダー（CORS対応）
    headers = {
        'Access-Control-Allow-Origin': '*',  # 必要なら特定のオリジンを指定
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    if not lineId:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'message': 'lineId is required.'
            })
        }
    
    try:
        # DynamoDBからデータを取得
        response = table.get_item(
            Key={'lineId': lineId}
        )
        
        if 'Item' in response:
            # DynamoDBから取得したデータをJSON形式に変換
            profile = response['Item']
            return {
                'statusCode': 200,
                'headers': headers,  # CORS対応のヘッダーを追加
                'body': json.dumps({
                    'message': 'Profile retrieved successfully!',
                    'data': profile
                }, default=decimal_to_dict)  # Decimalの処理用にdefault引数を追加
            }
        else:
            return {
                'statusCode': 404,
                'headers': headers,  # CORS対応のヘッダーを追加
                'body': json.dumps({
                    'message': 'Profile not found'
                })
            }
    
    except ClientError as e:
        # エラーハンドリング
        return {
            'statusCode': 500,
            'headers': headers,  # CORS対応のヘッダーを追加
            'body': json.dumps({
                'message': 'Error retrieving profile',
                'error': str(e)
            })
        }
