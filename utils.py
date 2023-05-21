import boto3
from botocore.exceptions import ClientError
import requests
from boto3.dynamodb.conditions import Key, Attr
from geopy.geocoders import  Nominatim
from geopy.distance import geodesic

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

s3 = boto3.client('s3')
bucket_name = "message-bucket340822"

public_api = 'https://p7zk140dwf.execute-api.us-east-1.amazonaws.com/test/'


def upload_image(filename, image):
    try:
        s3.upload_fileobj(image, bucket_name, filename)
        image_signed_url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename})
        return image_signed_url
    except Exception as e:
        print(f"Error uploading {filename} to S3 bucket: {e}")


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

def compute_distance(user1_lat, user1_lon, user2_lat, user2_lon):
    distance = geodesic((user1_lat, user1_lon), (user2_lat, user2_lon)).kilometers
    return  distance

def insert_post(message_id, message, image, address, user, phone_number, timestamp):
    data = {"operation": "create", "payload": {
        "Item": {"message": message, "message_id": message_id, "timestamp": timestamp, "image": image, "phone_number": phone_number
            , "user_name": user, "address": address}}}
    requests.post(public_api + 'post', json=data)

def delete_post(message, timestamp):
    data = {"operation": "delete", "payload": {"Key": {"message": message, "timestamp": timestamp}}}
    requests.post(public_api + 'post', json=data)

def insert_user(email, user_name, password, phone_number):
    data = {"operation": "create", "payload": {
        "Item": {"email": email, "user_name": user_name, "password": password, "phone_number": phone_number}}}
    requests.post(public_api + 'login', json=data)
