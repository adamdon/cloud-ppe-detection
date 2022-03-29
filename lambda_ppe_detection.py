import json
import boto3


def lambda_handler(event, context):
    print("lambda_ppe_detection.py running...")

    body = json.loads(event["Records"][0]["body"]) 
    message = json.loads(body["Message"])
    
    bucketName = message["Records"][0]["s3"]["bucket"]["name"]
    imageName = message["Records"][0]["s3"]["object"]["key"]
    tableName = ("table" + bucketName[2:])
    
    print("bucketName: " + bucketName)
    print("imageName: " + imageName)
    print("tableName: " + tableName)
    
    # rekognitionClient = boto3.client('rekognition')
    # response = rekognitionClient.detect_labels(Image={'S3Object':{'Bucket':bucketName,'Name':imageName}}, MaxLabels=5)
    # labels = response["Labels"]
    
    # for label in labels:
    #     del label["Instances"]
    #     del label["Parents"]
    #     label["Confidence"] = str(label["Confidence"])
    #     print("label found: " + str(label))
        
    # # print(labels)    
    
    # table = boto3.resource("dynamodb").Table(tableName)
    # table.put_item(Item={"image": imageName, "results": str(labels)})
    
    print("... End of lambda_ppe_detection.py")

    return {"statusCode": 200}