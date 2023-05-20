import boto3
from botocore.exceptions import ClientError
import json
import io
from application import application
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
    # login_table = dynamodb.Table('login')
    #
    # try:
    #     response = login_table.get_item(
    #         Key={
    #             'email': email
    #         }
    #     )
    # except ClientError as e:
    #     application.logger.info(e.response['error']['message'])
    #     return False
    #
    # else:
    #     # check whether response contains item and password matches
    #     if 'Item' in response and response['Item']['password'] == password:
    #         return response['Item']
    #     else:
    #         return False
    data = {"operation": "read", "payload": {"Item": {"email": email, "password": password}}}
    response = requests.get(public_api + 'login', json=data)
    if response.status_code == 200:
        # 登录成功
        if 'Item' in response and response['Item']['password'] == password:
            return response['Item']
    else:
        # 登录失败
        return False



def is_email_exist(email):
    table = dynamodb.Table('login')
    response = table.get_item(Key={'email': email})
    if 'Item' in response:
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


def insert_user(email, user_name, password):
    data = {"operation": "create", "payload": {"Item": {"email": email,"user_name":user_name, "password": password}}}
    requests.post(public_api+'login', json=data)
    # table = dynamodb.Table('login')
    # table.put_item(Item={'email': email, 'user_name': username, 'password': password})


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


def create_login_table():
    try:
        table = dynamodb.Table('login')
        table.table_status
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = dynamodb.create_table(
                TableName='login',
                KeySchema=[
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'email',
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
        print(f"Table login already exists.")


def create_music_table():
    table_name = 'music'
    try:
        table = dynamodb.Table(table_name)
        table.table_status
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'artist',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'title',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'artist',
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
        print(f"Table {table_name} already exists.")


