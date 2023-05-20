import boto3
from botocore.exceptions import ClientError
import requests
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

s3 = boto3.client('s3')
bucket_name = "music-bucket340822"

public_api = 'https://p7zk140dwf.execute-api.us-east-1.amazonaws.com/test/'


# load image url

def query_music(title, year, artist):
    table = dynamodb.Table('music')
    response = table.scan(
        FilterExpression=Attr('title').contains(title) & Attr('year').contains(year) & Attr('artist').contains(artist)
    )
    return response


def validate_user(email, password):
    data = {
        "operation": "read",
        "payload": {
            "Key": {
                "email": email,
            }
        }
    }
    response = requests.post(public_api + 'login', json=data)
    if response.status_code == 200:
        res = response.json()
        # login successfully
        if 'Item' in res and res['Item']['password'] == password:
            return res['Item']
    else:
        return False


def is_email_exist(email):
    data = {
        "operation": "read",
        "payload": {
            "Key": {
                "email": email,
            }
        }
    }
    response = requests.post(public_api + 'login', json=data)
    if 'Item' in response.json():
        return True
    return False


def insert_subscribe(email, title, year, artist, img_url):
    table = dynamodb.Table('subscribe')
    table.put_item(Item={'email': email, 'title': title, 'year': year, 'artist': artist, 'img_url': img_url})


def delete_subscribe(email, title, year, artist):
    table = dynamodb.Table('subscribe')
    try:
        response = table.delete_item(
            Key={
                'email': email,
                'title': title
            },
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response


def query_subscription_by_email(email):
    table = dynamodb.Table('subscribe')
    response = table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    return response


def insert_user(email, user_name, password, phone_number):
    data = {"operation": "create", "payload": {"Item": {"email": email, "user_name": user_name, "password": password, "phone_number": phone_number}}}
    requests.post(public_api + 'login', json=data)


def create_subscribe_table():
    try:
        table = dynamodb.Table('subscribe')
        table.table_status
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Table does not exist, so create it
            table = dynamodb.create_table(
                TableName='subscribe',
                KeySchema=[
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'title',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'email',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'title',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
        else:
            raise e
    else:
        print(f"Table subscribe already exists.")
