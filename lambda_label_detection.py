import json
import boto3


def lambda_handler(event, context):
    print("lambda_label_detection.py running...")

    body = json.loads(event["Records"][0]["body"]) 
    message = json.loads(body["Message"])
    
    bucketName = message["Records"][0]["s3"]["bucket"]["name"]
    imageName = message["Records"][0]["s3"]["object"]["key"]
    print(bucketName)
    print(imageName)
    
    print("... End of lambda_label_detection.py")

    # rekognitionClient = boto3.client("rekognition")

    return {"statusCode": 200}
