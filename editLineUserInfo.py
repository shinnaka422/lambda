import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# DynamoDBのリソースを取得
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('LineUserProfiles')

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
    # リクエストボディからデータを取得
    body = json.loads(event['body'])
    line_id = event['pathParameters']['lineId']  # URLパラメータからlineIdを取得
    
    # デフォルトのレスポンスヘッダー（CORS対応）
    headers = {
        'Access-Control-Allow-Origin': '*',  # 必要なら特定のオリジンを指定
        'Access-Control-Allow-Methods': 'PUT, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    # 更新するデータを取得
    update_expression = "SET "
    expression_attribute_values = {}
    attributes_to_update = []

    # 更新するフィールドを指定
    for key in body:
        if key in ['birthDate', 'gender', 'height', 'weight', 'targetWeight', 'targetPeriod', 
                    'motivation', 'pastExperience', 'exerciseFrequency', 'mealFrequency', 
                    'alcoholFrequency', 'allergies', 'restrictions', 'illness']:
            # データ型に応じて値を設定
            if key in ['height', 'weight', 'targetWeight']:  # 数値型
                attributes_to_update.append(f"{key} = :{key}")
                expression_attribute_values[f":{key}"] = str(body[key])  # 数値を文字列に変換
            else:  # 文字列型
                attributes_to_update.append(f"{key} = :{key}")
                expression_attribute_values[f":{key}"] = body[key]

    # 更新式を作成
    update_expression += ", ".join(attributes_to_update)

    try:
        # DynamoDBのテーブルを更新
        response = table.update_item(
            Key={
                'lineId': line_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW"  # 更新後の新しい値を返す
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'User information updated successfully!',
                'data': response['Attributes']  # 更新された属性を返す
            })
        }

    except ClientError as e:
        print(e.response['Error']['Message'])
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to update user information.',
                'error': e.response['Error']['Message']
            })
        }
