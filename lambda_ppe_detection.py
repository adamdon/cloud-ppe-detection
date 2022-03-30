import traceback
import time
import os
import json
import boto3


def lambda_handler(event, context):
    print("lambda_ppe_detection.py running...")
    
    alertNumber = os.environ['alertNumber']

    body = json.loads(event["Records"][0]["body"]) 
    message = json.loads(body["Message"])
    
    bucketName = message["Records"][0]["s3"]["bucket"]["name"]
    imageName = message["Records"][0]["s3"]["object"]["key"]
    tableName = ("table" + bucketName[2:])
    
    print("bucketName: " + bucketName)
    print("imageName: " + imageName)
    print("tableName: " + tableName)
    
    rekognitionClient = boto3.client('rekognition')
    response = rekognitionClient.detect_protective_equipment(
        Image={'S3Object': {'Bucket': bucketName,'Name': imageName,}},
        SummarizationAttributes={'MinConfidence': float("75"),'RequiredEquipmentTypes': ['FACE_COVER', 'HAND_COVER']}
    )
    
    
    compliance = ""
    compliant = True
    
    
    bodyParts = response["Persons"][0]["BodyParts"]
    
    for part in bodyParts:
        partName = part["Name"].lower().replace("_", " ")
        equipmentDetectionsList = part["EquipmentDetections"]
        if partName != "head":
            if len(equipmentDetectionsList) > 0:
                compliance = (compliance + "" + partName + " is pretected, ")
            else:
                compliant = False
                compliance = (compliance + "" + partName + " is exposed, ") 
    if compliant == True:
        compliance = "PASSED: " + compliance
    else:
        compliance = "FAILED: " + compliance
        if alertNumber != "ZZ-ZZZZZZZZZZ":
            message = ("Cloud-PPE-Detection Alert - " + imageName + " - " + compliance)
            lambda_client = boto3.client('lambda')
            role_response = lambda_client.get_function_configuration(FunctionName = os.environ['AWS_LAMBDA_FUNCTION_NAME'])
            print(role_response)
            lambdaRoleArn = role_response['Role']
            
            sns = boto3.client('sns')
            sns.set_sms_attributes(
                attributes={
                    "DeliveryStatusIAMRole": lambdaRoleArn,
                    "DefaultSenderID": "aws",
                    "DefaultSMSType": "Transactional"
                }
            )            
            snsPublishresponse = sns.publish(PhoneNumber=alertNumber, Message=message)
            print(snsPublishresponse)
            print("SMS sent to " + alertNumber + ", with message:   " + message)
        
    # print(bodyParts)    
    print(compliance)
    
    # time.sleep(3)
    table = boto3.resource("dynamodb").Table(tableName)
    try:
        existingItem = table.get_item(Key={'image': imageName})
        table.update_item(Key={'image': imageName},UpdateExpression="SET compliance = :updated", ExpressionAttributeValues={':updated': compliance})
    except:
        table.put_item(Item={"image": imageName, "results": "Not yet set", "compliance": str(compliance)})
        # print(traceback.format_exc())

            
    
    print("... End of lambda_ppe_detection.py")

    return {"statusCode": 200}