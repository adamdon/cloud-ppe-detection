import json
import boto3


def lambda_handler(event, context):
    print("lambda_label_detection.py running...")

    body = json.loads(event["Records"][0]["body"]) 
    message = json.loads(body["Message"])
    
    bucketName = message["Records"][0]["s3"]["bucket"]["name"]
    imageName = message["Records"][0]["s3"]["object"]["key"]
    tableName = ("table" + bucketName[2:])
    
    print(bucketName)
    print(imageName)
    print(tableName)
    
    rekognitionClient = boto3.client('rekognition')
    response = rekognitionClient.detect_labels(Image={'S3Object':{'Bucket':bucketName,'Name':imageName}}, MaxLabels=5)
    labels = response["Labels"]
    
    for label in labels:
        print(type(label))
        print(label)
        # del label["Instances"]
        # del label["Parents"]
    
    # table = boto3.resource("dynamodb").Table(tableName)
    # table.put_item(Item={"image": imageName, "results": "testResults"})
    
    print("... End of lambda_label_detection.py")

    return {"statusCode": 200}
