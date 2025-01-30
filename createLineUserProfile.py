import json
import time
import boto3
from botocore.exceptions import ClientError

# DynamoDBのリソースを作成
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('LineUserProfiles')  # 使用するテーブル名

def lambda_handler(event, context):
    # 受け取るデータ（フロントエンドから送られてくる）
    lineId = event['lineId']
    birthDate = event['birthDate']
    gender = event['gender']
    height = event['height']
    weight = event['weight']
    targetWeight = event['targetWeight']
    targetPeriod = event['targetPeriod']
    priority = event['priority']
    pastExperience = event['pastExperience']
    exerciseFrequency = event['exerciseFrequency']
    mealFrequency = event['mealFrequency']
    alcoholFrequency = event['alcoholFrequency']
    allergies = event['allergies']
    restrictions = event['restrictions']
    illness = event['illness']
    motivation = event['motivation']
    
    # プロフィールIDの生成（lineId + 現在のタイムスタンプ）
    profileId = f"{lineId}-{str(int(time.time()))}"

    try:
        # データをDynamoDBに登録
        response = table.put_item(
            Item={
                'lineId': lineId,
                'profileId': profileId,
                'birthDate': birthDate,
                'gender': gender,
                'height': height,
                'weight': weight,
                'targetWeight': targetWeight,
                'targetPeriod': targetPeriod,
                'priority': priority,
                'pastExperience': pastExperience,
                'exerciseFrequency': exerciseFrequency,
                'mealFrequency': mealFrequency,
                'alcoholFrequency': alcoholFrequency,
                'allergies': allergies,
                'restrictions': restrictions,
                'illness': illness,
                'motivation': motivation,
                'createdAt': str(int(time.time())),  # 作成日時
                'updatedAt': str(int(time.time()))   # 更新日時
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Profile created successfully!',
                'data': {
                    'profileId': profileId,
                    'lineId': lineId,
                    'birthDate': birthDate,
                    'gender': gender,
                    'height': height,
                    'weight': weight,
                    'targetWeight': targetWeight,
                    'targetPeriod': targetPeriod,
                    'priority': priority,
                    'pastExperience': pastExperience,
                    'exerciseFrequency': exerciseFrequency,
                    'mealFrequency': mealFrequency,
                    'alcoholFrequency': alcoholFrequency,
                    'allergies': allergies,
                    'restrictions': restrictions,
                    'illness': illness,
                    'motivation': motivation,
                    'createdAt': str(int(time.time())),
                    'updatedAt': str(int(time.time()))
                }
            })
        }

    except ClientError as e:
        # エラーハンドリング
        print(f"Error creating profile: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error creating profile',
                'error': str(e)
            })
        }
