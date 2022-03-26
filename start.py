import os
import traceback
import time
import yaml
import json
import boto3
from zipfile import ZipFile
from pathlib import Path
from botocore.exceptions import ClientError



# 
# Script start here
# 
def main():
    print("")
    print("cloud-ppe-detection start up... (╯°□°)╯︵ ┻━┻")
    print("")
    
    tagId = None
    securityGroupId = None
    s3Name = None
    snsTopicArn = None
    s3EventRequestId = None
    ec2StartUpBashScript = None
    StackId = None
    ec2instanceId = None
    
    try:
        tagId = createTagId()
        securityGroupId = createSecurityGroup(tagId)
        s3Name = createS3(tagId)
        snsTopicArn = createSNS(tagId, s3Name)
        s3EventRequestId = createS3Event(tagId, s3Name, snsTopicArn)
        uploadLambdas(s3Name)
        StackId = deployCloudformationStack(tagId, snsTopicArn)
        ec2StartUpBashScript = creatEc2StartUpBashScript(tagId, s3Name)
        ec2instanceId = createEc2(tagId, securityGroupId, ec2StartUpBashScript)
    except:
        print("*** An exception occurred ***")
        print(traceback.format_exc())
        deleteResources(ec2instanceId, securityGroupId, s3Name, snsTopicArn, StackId);
        quit()
    else:
        print("")
        print("...Setup complete")
        ans=True
        while ans:
            print ("""
            1.Exit and keep resources
            2.Exit and delete resources
            """)
            ans=input("What would you like to do? ") 
            if ans=="1": 
                print("\nExit and keep resources selected")
                quit()
            elif ans=="2":
                print("\nExit and delete resources selected")
                deleteResources(ec2instanceId, securityGroupId, s3Name, snsTopicArn, StackId)
                quit()
            elif ans !="":
              print("\nNot a valid option") 
    # end of script










# 
# resource creation fuctions
# 


def uploadLambdas(s3bucketName):
    print("Lambdas uploading to S3...")
    os.chdir(Path(__file__).parent)
    pathTolambda_label_detectionPy = Path(__file__).parent / "lambda_label_detection.py"
    pathTolambda_label_detectionZip = Path(__file__).parent / "lambda_label_detection.zip"

    
    ZipFile(pathTolambda_label_detectionZip, mode='w').write(pathTolambda_label_detectionPy, "lambda_label_detection.py")

    
    s3Client = boto3.client('s3')
    with open(pathTolambda_label_detectionZip, "rb") as f:
        s3Client.upload_fileobj(f, s3bucketName, "lambda_label_detection.zip")
    time.sleep(5)    
    
    os.remove(pathTolambda_label_detectionZip)
    print("Lambdas uploaded to S3 with: ")



def deployCloudformationStack(tagId, snsTopicArn):
    print("Cloudfomation Stack deploying...")
    client = boto3.client('cloudformation')
    
    stackName = ("stack" + tagId)
    
    # pathToFile = Path(__file__).parent / "cloudformation_template.yaml"
    # with open(pathToFile, 'r') as content_file:
    #     templateYaml = yaml.safe_load(content_file)
    # templateJson = json.dumps(templateYaml)

    # pathToFile = Path(__file__).parent / "cloudformation_template.json"
    # with open(pathToFile, 'r') as content_file:
    #     templateJson = json.load(content_file)
    # fixedTemplateJsonString = str(templateJson).replace("'", '"')
    
    pathToFile = Path(__file__).parent / "cloudformation_template.json"
    with open(pathToFile, 'r') as content_file:
        templateText = content_file.read()

    response = client.create_stack(
        StackName=stackName,
        TemplateBody=templateText,
        Parameters=[{ # set as necessary. Ex: 
            'ParameterKey': 'SNSTopicARN',
            'ParameterValue': snsTopicArn
        }]
    )
    time.sleep(60) #Sleep due to AWS propagation issues
    print("Cloudfomation Stack deployed with StackId: " + response["StackId"])
    return response["StackId"]




def createTagId():
    timecurrent = int(time.time())
    timeStr = str(timecurrent)
    tagId = ("-" + timeStr + "-" + "s1025475")
    print("Resources being created with tagId: " + tagId)
    print("")
    return tagId
        
        
        
def createSecurityGroup(tagId):
    print("Security group creating...")
    ec2Client = boto3.client('ec2')
    vpcResponse = ec2Client.describe_vpcs()
    vpc_id = vpcResponse.get('Vpcs', [{}])[0].get('VpcId', '')
    
    try:
        response = ec2Client.create_security_group(GroupName=("security-group" + tagId),
                                             Description=("security-group" + tagId),
                                             VpcId=vpc_id)
        security_group_id = response['GroupId']

        data = ec2Client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ])
        print("Security group create with id: " + security_group_id)
        return security_group_id
    except ClientError as e:
        print(e)
   

def creatEc2StartUpBashScript(tagId, s3Name):
    script = ("#!/bin/bash\n"
                    "cd /home/ec2-user\n" 
                    "sudo yum -y install git\n" 
                    "pip3 install boto3\n" 
                    "git clone https://github.com/adamdon/cloud-ppe-detection.git\n" 
                    "cd cloud-ppe-detection\n"
                    "cd ec2-files\n"
                    "python3 ec2Upload.py " + s3Name +
                    "\n" 
                    "touch scriptEnded.txt")
    return script



        
def createS3(tagId):
    print("S3 bucket creating...")
    s3Client = boto3.resource('s3')
    bucketName = ('s3' + tagId)
    s3Client.create_bucket(Bucket= bucketName)

    # ec2Client.create_tags(Resources=[instance], Tags=[{'Key':'Name', 'Value':("ec2" + tagId)}])
    print("S3 bucket created with name: " + bucketName)
    return bucketName



def createSNS(tagId, s3Name):
    print("SNS topic creating...")
    snsClient = boto3.client("sns")
    snsName = ('sns' + tagId)
    
    try:
        topic = snsClient.create_topic(Name=snsName)
    except ClientError:
        print("error, could not create topic")
        raise
    
    snsTopicPolicy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "sns:Publish",
                "Resource": topic["TopicArn"],
                "Condition": {
                    "ArnLike": {"AWS:SourceArn": f"arn:aws:s3:*:*:{s3Name}"},
                },
            },
        ],
    }
    
    snsClient.set_topic_attributes(
        TopicArn=topic["TopicArn"],
        AttributeName='Policy',
        AttributeValue=json.dumps(snsTopicPolicy),
    )
    
    sns = boto3.resource("sns")
    topicsList = sns.topics.all()
    newTopic = "null"
    
    
    newTopic = sns.Topic(topic["TopicArn"])
    newTopic.subscribe(Protocol="email", Endpoint="mail@adamdon.co.uk", ReturnSubscriptionArn=False)
    
    # for currentTopic in topicsList:
    #     currentTopic.subscribe(Protocol="email", Endpoint="mail@adamdon.co.uk", ReturnSubscriptionArn=False)
    #     print(currentTopic)
    #     print(type(currentTopic))
        
    print("SNS topic created with arn: " + topic["TopicArn"])
    return topic["TopicArn"]
            
            
def createS3Event(tagId, s3Name, snsTopicArn):
    print("S3 event creating...")
    s3 = boto3.resource('s3')
    bucket_notification = s3.BucketNotification(s3Name)
    response = bucket_notification.put(
        NotificationConfiguration={
            'TopicConfigurations': [
                {
                    'Id': ("topic-configuration" + tagId),
                    'TopicArn': snsTopicArn,
                    'Events': ["s3:ObjectCreated:Put"],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'prefix',
                                    'Value': 'image'
                                },
                            ]
                        }
                    }
                },
            ],
            'EventBridgeConfiguration': {}
        },
        SkipDestinationValidation=False
    )
    print("S3 event created with RequestId: " + response["ResponseMetadata"]["RequestId"])
    return(response["ResponseMetadata"]["RequestId"])





def createEc2(tagId, securityGroupId, ec2StartUpBashScript):
    print("EC2 instance creating...")
    ec2Client = boto3.client('ec2')
    response = ec2Client.run_instances(
            ImageId= 'ami-0c02fb55956c7d316',
            InstanceType= 't2.micro',
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=[securityGroupId],
            KeyName= 'vockey',
            UserData=ec2StartUpBashScript,
            IamInstanceProfile={
                        'Name': 'EMR_EC2_DefaultRole'
                 }
            )
    instance = response["Instances"][0]["InstanceId"]
    ec2Client.create_tags(Resources=[instance], Tags=[{'Key':'Name', 'Value':("ec2" + tagId)}])
    print("EC2 instance created with ID: " + instance)
    return instance






















# 
# clean up fuctions
# 

def deleteResources(ec2instanceId, securityGroupId, s3Name, snsTopicArn, StackId):
    if ec2instanceId:
        ec2Terminate(ec2instanceId, securityGroupId)
    if s3Name:    
        s3EemptyDelete(s3Name)
    if snsTopicArn:
        snsTopicDelete(snsTopicArn)
    if StackId:
        cloudformationStackDelete(StackId)
    if securityGroupId:
        time.sleep(5)
        deleteSecurtyGroup(securityGroupId)




def deleteSecurtyGroup(securityGroupId):
    print("deleteSecurtyGroup: " + securityGroupId)
    ec2Client = boto3.client('ec2')
    try:
        response = ec2Client.delete_security_group(GroupId=securityGroupId)
    except ClientError as e:
        print(e)
    print("deleteSecurtyGroup complete")
        
        

def ec2Terminate(instanceId, securityGroupId):
    print("terminating ec2 instance: " + instanceId)
    ec2Client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instanceId)
    all_sg_ids = [sg['GroupId'] for sg in instance.security_groups]
    # response = instance.modify_attribute(Groups=[''])
    if securityGroupId in all_sg_ids:                                          
        all_sg_ids.remove(securityGroupId)
        print("Removed security Group: " + securityGroupId + " from instance: " + instanceId)
        
    response = ec2Client.terminate_instances(InstanceIds=[instanceId, ],)
    print("terminat ec2 instance complete ")
        
def s3EemptyDelete(s3Name):
    print("s3EemptyDelete: " + s3Name)
    s3Client = boto3.resource('s3')
    bucket = s3Client.Bucket(s3Name)
    bucket.objects.all().delete()
    bucket.delete()
    print("s3EemptyDelete complete")

        
def snsTopicDelete(topicArn):
    print("snsTopicDelete: " + topicArn)
    snsClient = boto3.client("sns")
    try:
        response = snsClient.delete_topic(TopicArn=topicArn)
    except ClientError:
        print('Could not delete a SNS topic.')
        raise
    else:
        print("snsTopicDelete complete")
        
        
def cloudformationStackDelete(StackId):
    print("cloudformationStackDelete: " + StackId)
    client = boto3.client('cloudformation')
    response = client.delete_stack(
        StackName=StackId
    )


    print("cloudformationStackDelete complete")
        
















if __name__ == "__main__":
    main()