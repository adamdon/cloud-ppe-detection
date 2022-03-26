import json
import boto3


def lambda_handler(event, context):
    print("lambda_label_detection.py running...")
    print(event)

    # rekognitionClient = boto3.client("rekognition")

    return {"statusCode": 200}
