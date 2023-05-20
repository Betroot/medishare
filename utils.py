import boto3
from botocore.exceptions import ClientError
import requests
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

s3 = boto3.client('s3')
bucket_name = "message-bucket340822"

public_api = 'https://p7zk140dwf.execute-api.us-east-1.amazonaws.com/test/'


def upload_image(filename, image):
    try:
        s3.upload_fileobj(image, bucket_name, filename + '.jpg')
        image_signed_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename})
        return image_signed_url
    except Exception as e:
        print(f"Error uploading {filename} to S3 bucket: {e}")


def query_music(title, year, artist):
    table = dynamodb.Table('music')
    response = table.scan(
        FilterExpression=Attr('title').contains(title) & Attr('year').contains(year) & Attr('artist').contains(artist)
    )
    return response


def query_all_post():
    data = {
        "operation": "read_all",
        "payload": {
        }
    }
    response = requests.post(public_api + 'post', json=data)
    return response.json()


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


def return_user_by_email(email):
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
        return response.json()['Item']
    return False


def insert_post(message, image, location, user, phone_number, timestamp):
    data = {"operation": "create", "payload": {
        "Item": {"message": message, "timestamp": timestamp, "image": image, "phone_number": phone_number
            , "user_name": user, "location": location}}}
    requests.post(public_api + 'post', json=data)


def delete_post(message, timestamp):
    data = {"operation": "delete", "payload": {"Key": {"message": message, "timestamp": timestamp}}}
    requests.post(public_api + 'post', json=data)


def query_subscription_by_email(email):
    table = dynamodb.Table('subscribe')
    response = table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    return response


def insert_user(email, user_name, password, phone_number):
    data = {"operation": "create", "payload": {
        "Item": {"email": email, "user_name": user_name, "password": password, "phone_number": phone_number}}}
    requests.post(public_api + 'login', json=data)
