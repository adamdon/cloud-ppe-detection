import time
import json
import boto3
from botocore.exceptions import ClientError



def createTagId():
        timecurrent = int(time.time())
        timeStr = str(timecurrent)
        tagId = ("-" + timeStr + "-" + "s1025475")
        print("* created tag " + tagId)
        return tagId
        
        
        
def createSecurityGroup():
        print("creating security group")
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
            print("new security group create with security_group_id: " + security_group_id)
            return security_group_id
        except ClientError as e:
            print(e)
   

def creatEc2StartUpBashScript():
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



def createEc2():
        print("creating Ec2 instance")
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
        print("new EC2 instance created with ID: " + instance)
        return instance
        
        
def createS3():
        print("creating s3 bucket")
        s3Client = boto3.resource('s3')
        bucketName = ('s3' + tagId)
        s3Client.create_bucket(Bucket= bucketName)

        # ec2Client.create_tags(Resources=[instance], Tags=[{'Key':'Name', 'Value':("ec2" + tagId)}])
        print("new s3 bucket created")
        return bucketName



def createSNS():
        print("creating SNS topic")
        snsClient = boto3.client("sns")
        snsName = ('sns' + tagId)
        
        try:
            topic = snsClient.create_topic(Name=snsName)
            print("SNS topic created with arn: " + topic["TopicArn"])
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
        

        print(newTopic)
        for currentTopic in topicsList:
            # currentTopic.subscribe(Protocol="email", Endpoint="mail@adamdon.co.uk", ReturnSubscriptionArn=False)

            # if currentTopic["TopicArn"] == topic["TopicArn"]:
            #     newTopic = currentTopic
            print(currentTopic)
        print(newTopic)
        
        return topic["TopicArn"]
            
            
def createS3Event():
        print("creating S3 event")
        s3 = boto3.resource('s3')
        bucket_notification = s3.BucketNotification(s3Name)
        response = bucket_notification.put(
            NotificationConfiguration={
                'TopicConfigurations': [
                    {
                        'Id': ("topic-configuration" + tagId),
                        'TopicArn': snsTopicArn,
                        'Events': ["s3:ObjectCreated:Put"],
                    },
                ],
                'EventBridgeConfiguration': {}
            },
            SkipDestinationValidation=False
        )
        #print(response)













# 
# clean up fuctions
# 

def deleteSecurtyGroup(securityGroupId):
        print("deleteSecurtyGroup: " + securityGroupId)
        ec2Client = boto3.client('ec2')
        try:
            response = ec2Client.delete_security_group(GroupId=securityGroupId)
        except ClientError as e:
            print(e)
        print("deleteSecurtyGroup complete")
        
        

def ec2Terminate(instanceId):
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








# 
# Script start here
# 

print("")
print("cloud-ppe-detection start up... (╯°□°)╯︵ ┻━┻")
print("")



tagId = createTagId()
securityGroupId = createSecurityGroup()
s3Name = createS3()
snsTopicArn = createSNS()
createS3Event()
ec2StartUpBashScript = creatEc2StartUpBashScript()
ec2instanceId = createEc2()



print("...Setup complete")
ans=True
while ans:
    print ("""
    1.Exit and keep resources
    2.Exit and delete resources
    """)
    ans=input("What would you like to do? ") 
    if ans=="1": 
        print("\n Exit and keep resources selected")
        quit()
    elif ans=="2":
        print("\n Exit and delete resources selected")
        ec2Terminate(ec2instanceId)
        s3EemptyDelete(s3Name)
        snsTopicDelete(snsTopicArn)
        time.sleep(30)
        deleteSecurtyGroup(securityGroupId)
        quit()
    elif ans !="":
      print("\n Not a valid option") 
