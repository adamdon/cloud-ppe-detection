import sys
import os
import traceback
import time
import json
import boto3
from zipfile import ZipFile
from pathlib import Path
from botocore.exceptions import ClientError




# # # main function
# start of script to create resources
def main():
    print("")
    print("cloud-ppe-detection start up... (╯°□°)╯︵ ┻━┻")
    print("")
    
    # Checking if command-line arguments passed
    if len(sys.argv) == 5: # optional SMS alert feature is in use if 4 additional arguments used
        tagSuffix = sys.argv[1] # this will show at the end of the name for all resources created
        iamName = sys.argv[2] # iamName is name of the Role used to deploy the cloudformation 
        keyName = sys.argv[3] # name of RSA key pair to be used with EC2 instance 
        alertNumber = sys.argv[4] # the cell phone number in international format that SMS alerts will be sent to
    elif len(sys.argv) == 4: # if 3 additional arguments used the SMS alert fecture will not be used
        tagSuffix = sys.argv[1]
        iamName = sys.argv[2]
        keyName = sys.argv[3]
        alertNumber = "ZZ-ZZZZZZZZZZ"
    else:  # if no arguments passed, default settings will be used
        tagSuffix = "s1025475"
        iamName = "LabRole"
        keyName = "vockey"
        alertNumber = "ZZ-ZZZZZZZZZZ"
    
    tagId = None # the full name used to append the name for all resources created including unix timestamp
    securityGroupId = None # the id of the created Security Group that will be used with the EC2
    s3Name = None # the name of the created s3 bucket
    snsTopicArn = None # the ARN of the created SNS topic 
    s3EventRequestId = None # the id of the created event that has the s3 bucket trigger a SNS event
    ec2StartUpBashScript = None # the full text of the crated bash script that will be ran on the EC2 once running
    StackId = None # the of the created cloudformation stack
    ec2instanceId = None # the instance id the of crated EC2 instance
    
    try: # main applicaion logic where all resporces are created sequentially
        tagId = createTagId(tagSuffix)
        securityGroupId = createSecurityGroup(tagId)
        s3Name = createS3(tagId)
        snsTopicArn = createSNS(tagId, s3Name)
        s3EventRequestId = createS3Event(tagId, s3Name, snsTopicArn)
        uploadLambdas(s3Name)
        StackId = deployCloudformationStack(tagId, snsTopicArn, iamName, alertNumber)
        ec2StartUpBashScript = creatEc2StartUpBashScript(tagId, s3Name)
        ec2instanceId = createEc2(tagId, securityGroupId, ec2StartUpBashScript, keyName)
    except: # if any exceptions bubble up during resource creation, a clean up will start
        print("*** An exception occurred ***")
        print(traceback.format_exc())
        deleteResources(ec2instanceId, securityGroupId, s3Name, snsTopicArn, StackId);
        quit()
    else: # if resource creation is successful, a menu will be shown to the user
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
# # # # resource creation fuctions
# 



# # # uploadLambdas function
# #
# loads and zips both lambda files
# PUTs the zip files on the named s3 bucket
# then deletes the newly created zip files from local storage
def uploadLambdas(s3bucketName):
    print("Lambdas uploading to S3...")
    os.chdir(Path(__file__).parent)
    
    pathTolambda_label_detectionPy = Path(__file__).parent / "lambda_label_detection.py"
    pathTolambda_label_detectionZip = Path(__file__).parent / "lambda_label_detection.zip"
    
    pathTolambda_ppe_detectionPy = Path(__file__).parent / "lambda_ppe_detection.py"
    pathTolambda_ppe_detectionZip = Path(__file__).parent / "lambda_ppe_detection.zip"

    
    ZipFile(pathTolambda_label_detectionZip, mode='w').write(pathTolambda_label_detectionPy, "lambda_label_detection.py")
    ZipFile(pathTolambda_ppe_detectionZip, mode='w').write(pathTolambda_ppe_detectionPy, "lambda_ppe_detection.py")

    
    s3Client = boto3.client('s3')
    with open(pathTolambda_label_detectionZip, "rb") as f:
        s3Client.upload_fileobj(f, s3bucketName, "lambda_label_detection.zip")
    time.sleep(1)
    with open(pathTolambda_ppe_detectionZip, "rb") as f:
        s3Client.upload_fileobj(f, s3bucketName, "lambda_ppe_detection.zip")
    time.sleep(1)

    os.remove(pathTolambda_label_detectionZip)
    os.remove(pathTolambda_ppe_detectionZip)
    print("Lambdas uploaded to S3 with filenames: lambda_label_detection.zip && lambda_ppe_detection.zip")




# # # deployCloudformationStack function
# #
# gets the Role ARN of the Role name
# loads the cloudformation json file from local storage
# creates the stack using the found Role ARN and loaded template json file
# checks that the stack is created
# polls the status of the stack untill it changes to CREATE_COMPLETE
# if any problem with deployment with ROLLBACK_COMPLETE, an Exception is Raised to start clean up
def deployCloudformationStack(tagId, snsTopicArn, iamName, alertNumber):
    print("Cloudfomation Stack deploying...")
    
    roleName = iamName
    iamClient = boto3.client('iam')
    iamResponse = iamClient.get_role(RoleName=roleName)
    roleArn = iamResponse["Role"]["Arn"]
    
    print("Cloudfomation Stack using Role ARN: " + roleArn)
    
    
    
    
    client = boto3.client('cloudformation')
    
    stackName = ("stack" + tagId)
    
    
    pathToFile = Path(__file__).parent / "cloudformation_template.json"
    with open(pathToFile, 'r') as content_file:
        templateText = content_file.read()

    response = client.create_stack(
        StackName=stackName,
        TemplateBody=templateText,
        Parameters=[{ # set as necessary. Ex: 
            'ParameterKey': 'snsTopicArn',
            'ParameterValue': snsTopicArn
        },
        {
            'ParameterKey': 'tagId',
            'ParameterValue': tagId
        },
        {
            'ParameterKey': 'alertNumber',
            'ParameterValue': alertNumber
        }
        ],
        Capabilities=['CAPABILITY_IAM'],
        RoleARN=roleArn,
    )
    time.sleep(5)
    
    stackDescriptionResponse = client.describe_stacks(StackName=stackName)
    foundStackName = stackDescriptionResponse["Stacks"][0]["StackName"]
    
    if foundStackName == stackName:
        currentStatus = stackDescriptionResponse["Stacks"][0]["StackStatus"]
        
        while currentStatus != "CREATE_COMPLETE":
            print("Cloudfomation Stack deploying, status: " + currentStatus + "...")
            time.sleep(15)
            
            newStackDescriptionResponse = client.describe_stacks(StackName=stackName)
            currentStatus = newStackDescriptionResponse["Stacks"][0]["StackStatus"]
            if currentStatus == "ROLLBACK_COMPLETE":
                raise Exception('Cloudfomation Stack ERROR - ROLLBACK_COMPLETE')
            
        print("Cloudfomation Stack deploying complete, status: " + currentStatus)    
    else:
        raise Exception('Cloudfomation Stack ERROR - not found')
        

    print("Cloudfomation Stack deployed with StackId: " + response["StackId"])
    return response["StackId"]




# # # createTagId function
# #
# get unix epoch time
# concatenates time with user defind tag suffix
def createTagId(tagSuffix):
    timecurrent = int(time.time())
    timeStr = str(timecurrent)
    tagId = ("-" + timeStr + "-" + tagSuffix)
    print("Resources being created with tagId: " + tagId)
    print("")
    return tagId
        
        
        
        
# # # createSecurityGroup function
# #
# creates a new security group for EC2 with default VPC
# creates a ingress rule that allows port 22 (SSH) to be used        
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
   



# # # creatEc2StartUpBashScript function
# #
# creates bash script that will run on EC2 start up
# concatenates a bash script as a String with the s3 bucket pass as a argument
# script navigates to default users home directory
# script installs git and boto3
# script clones repository containing images and upload script
# script runs python load up file
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



        
# # # createS3 function
# #
# creates s3 bucket using tag provided
# returns id of bucket
def createS3(tagId):
    print("S3 bucket creating...")
    
    s3Client = boto3.resource('s3')
    bucketName = ('s3' + tagId)
    s3Client.create_bucket(Bucket= bucketName)

    print("S3 bucket created with name: " + bucketName)
    return bucketName




# # # createSNS function
# #
# creates SNS Topic using tag given
# creates Policy that only allows this topic to be published to by the S3 bucket
# attaches the Policy onto the SNS Topic
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
    
    # sns = boto3.resource("sns")
    # topicsList = sns.topics.all()
    # newTopic = "null"
    
    
    # newTopic = sns.Topic(topic["TopicArn"])
    # newTopic.subscribe(Protocol="email", Endpoint="mail@email.co.uk", ReturnSubscriptionArn=False)
    
    # for currentTopic in topicsList:
    #     currentTopic.subscribe(Protocol="email", Endpoint="mail@email.co.uk", ReturnSubscriptionArn=False)
    #     print(currentTopic)
    #     print(type(currentTopic))
        
    print("SNS topic created with arn: " + topic["TopicArn"])
    return topic["TopicArn"]

 
 
 
            
# # # createS3Event function
# #
# gets s3 bucket resource from name
# creates a bucket notification
# sets event to triger on Put
# adds filter show only files names starting with "image" trigger then event
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




# # # createEc2  function
# #
# creates a EC2 instance using user defined KeyName
# creates a tag onto EC2 with name lable
# passes created bash script into instance to be ran on start-up
def createEc2(tagId, securityGroupId, ec2StartUpBashScript, keyName):
    print("EC2 instance creating...")
    ec2Client = boto3.client('ec2')
    response = ec2Client.run_instances(
            ImageId= 'ami-0c02fb55956c7d316',
            InstanceType= 't2.micro',
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=[securityGroupId],
            KeyName=keyName,
            UserData=ec2StartUpBashScript,
            IamInstanceProfile={
                        'Name': 'EMR_EC2_DefaultRole'
                 }
            )
    instance = response["Instances"][0]["InstanceId"]
    time.sleep(3)
    ec2Client.create_tags(Resources=[instance], Tags=[{'Key':'Name', 'Value':("ec2" + tagId)}])
    print("EC2 instance created with ID: " + instance)
    return instance






















# 
# clean up fuctions
# 

# # # deleteResources  function
# #
# Root clean up function deletes all created resource
# checks that resource IDs are not null are stage which this could be called is unknown
# deletes each resource sequentially
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




# # # deleteSecurtyGroup  function
# #
# deletes the create securty group
def deleteSecurtyGroup(securityGroupId):
    print("deleteSecurtyGroup: " + securityGroupId)
    ec2Client = boto3.client('ec2')
    try:
        response = ec2Client.delete_security_group(GroupId=securityGroupId)
    except ClientError as e:
        print(e)
    print("deleteSecurtyGroup complete")
        
        

# # # ec2Terminate  function
# #
# decatches the security group
# terminates the EC2 instance
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
       
       
# # # s3EemptyDelete  function
# #
# deletes all objects within bucket
# deletes bucket        
def s3EemptyDelete(s3Name):
    print("s3EemptyDelete: " + s3Name)
    s3Client = boto3.resource('s3')
    bucket = s3Client.Bucket(s3Name)
    bucket.objects.all().delete()
    bucket.delete()
    print("s3EemptyDelete complete")


# # # snsTopicDelete  function
# #
# deletes SNS topic
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
        

# # # cloudformationStackDelete function
# #
# deletes whole cloudformation stack        
def cloudformationStackDelete(StackId):
    print("cloudformationStackDelete: " + StackId)
    client = boto3.client('cloudformation')
    response = client.delete_stack(
        StackName=StackId
    )


    print("cloudformationStackDelete complete")
        
















if __name__ == "__main__":
    main()