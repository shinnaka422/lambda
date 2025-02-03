import json
import time
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
    # デバッグ用のログ出力
    print("Full event:", json.dumps(event))

    # デフォルトのレスポンスヘッダー（CORS対応）
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }

    # HTTPメソッドとパスを取得
    http_method = event["requestContext"]["http"]["method"]
    
    try:
        # POSTメソッド：プロフィール作成
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            # 必須フィールドのバリデーション
            required_fields = ['lineId', 'birthDate', 'gender', 'height', 'weight', 
                               'targetWeight', 'targetPeriod', 'priority', 'motivation']
            for field in required_fields:
                if field not in body:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'message': f'Missing required field: {field}'})
                    }
            
            # プロフィールIDの生成
            profile_id = f"{body['lineId']}-{str(int(time.time()))}"
            
            # DynamoDBにデータを登録
            table.put_item(
                Item={
                    'lineId': body['lineId'],
                    'profileId': profile_id,
                    'createdAt': str(int(time.time())),
                    'updatedAt': str(int(time.time())),
                    **body
                }
            )
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Profile created successfully!',
                    'data': {**body, 'profileId': profile_id}
                })
            }
        
        # GETメソッド：プロフィール取得
        elif http_method == 'GET':
            # クエリパラメータからLineIDを取得
            # デバッグのため、様々な方法で lineId を取得
            line_id = (
                event.get('queryStringParameters', {}).get('lineId') or
                event.get('pathParameters', {}).get('lineId') or
                json.loads(event.get('body', '{}')).get('lineId')
            )
            
            print(f"Extracted lineId: {line_id}")
            
            if not line_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'lineId is required',
                        'details': {
                            'queryStringParameters': event.get('queryStringParameters'),
                            'pathParameters': event.get('pathParameters'),
                            'body': event.get('body')
                        }
                    })
                }
            
            # DynamoDBからデータを取得
            response = table.get_item(Key={'lineId': line_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'Profile retrieved successfully!',
                        'data': response['Item']
                    }, default=decimal_to_dict)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'message': 'Profile not found'})
                }
        
        # PUTメソッド：プロフィール更新
        elif http_method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            line_id = body.get('lineId')
            
            if not line_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'lineId is required'})
                }
            
            # 更新するデータを準備
            update_parts = []
            expression_attribute_values = {}

            updateable_fields = [
                'birthDate', 'gender', 'height', 'weight', 'targetWeight', 
                'targetPeriod', 'motivation', 'pastExperience', 'exerciseFrequency', 
                'mealFrequency', 'alcoholFrequency', 'allergies', 'restrictions', 
                'illness', 'priority', 'notificationTime'
            ]

            for key, value in body.items():
                if key in updateable_fields:
                    update_parts.append(f"#{key} = :{key}")
                    expression_attribute_values[f":{key}"] = value

            if update_parts:
                # 更新式を作成
                update_expression = "SET " + ", ".join(update_parts) + ", #updatedAt = :updatedAt"
                expression_attribute_values[":updatedAt"] = str(int(time.time()))

                # ExpressionAttributeNamesの作成
                expression_attribute_names = {
                    f"#{key}": key for key in [field for field in body.keys() if field in updateable_fields]
                }
                expression_attribute_names["#updatedAt"] = "updatedAt"

                try:
                    response = table.update_item(
                        Key={
                            'lineId': line_id
                        },
                        UpdateExpression=update_expression,
                        ExpressionAttributeValues=expression_attribute_values,
                        ExpressionAttributeNames=expression_attribute_names,
                        ReturnValues="UPDATED_NEW"
                    )

                    return {
                        'statusCode': 200,
                        'headers': headers,
                        'body': json.dumps({
                            'message': 'User information updated successfully!',
                            'data': response.get('Attributes', {})
                        })
                    }

                except Exception as e:
                    print(f"Update error: {str(e)}")
                    return {
                        'statusCode': 500,
                        'headers': headers,
                        'body': json.dumps({
                            'message': 'Failed to update item',
                            'error': str(e)
                        })
                    }
            else:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'No valid fields to update'})
                }
        
        # DELETEメソッド：プロフィール削除
        elif http_method == 'DELETE':
            body = json.loads(event.get('body', '{}'))
            line_id = body.get('lineId')
            
            if not line_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'lineId is required'})
                }
            
            # アイテムの削除
            table.delete_item(
                Key={'lineId': line_id},
                ReturnValues='ALL_OLD'
            )
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Item deleted successfully',
                    'lineId': line_id
                })
            }
        
        # OPTIONSメソッド：CORS プリフライトリクエスト
        elif http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # サポートされていないメソッド
        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'message': 'Method Not Allowed'})
            }
    
    except ClientError as e:
        # ClientError の詳細なログ出力
        print(f"ClientError: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'An error occurred',
                'error': str(e)
            })
        }
    except Exception as e:
        # より詳細なエラーログ
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()  # tracebackを表示

        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Unexpected error',
                'error': str(e),
                'type': str(type(e))
            })
        }