import time
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
   



def createEc2():
        print("creating Ec2 instance")
        response = ec2Client.run_instances(
                ImageId= 'ami-0c02fb55956c7d316',
                InstanceType= 't2.micro',
                MaxCount=1,
                MinCount=1,
                SecurityGroupIds=[securityGroupId],
                KeyName= 'vockey',
                UserData=ec2StartUpBashScript
                )
        instance = response["Instances"][0]["InstanceId"]
        ec2Client.create_tags(Resources=[instance], Tags=[{'Key':'Name', 'Value':("ec2" + tagId)}])
        print("new EC2 instance created with ID: " + instance)
        return instance
        
        
def createS3():
        print("creating s3 bucket")
        bucketName = ('s3' + tagId)
        s3Client.create_bucket(Bucket= bucketName)

        # ec2Client.create_tags(Resources=[instance], Tags=[{'Key':'Name', 'Value':("ec2" + tagId)}])
        print("new s3 bucket created")
        return bucketName



# 
# clean up fuctions
# 

def deleteSecurtyGroup(securityGroupId):
        print("deleteSecurtyGroup: " + securityGroupId)
        try:
            response = ec2Client.delete_security_group(GroupId=securityGroupId)
        except ClientError as e:
            print(e)
        print("deleteSecurtyGroup complete")
        
        

def ec2Terminate(instanceId):
        print("terminating ec2 instance: " + instanceId)
        response = ec2Client.terminate_instances(InstanceIds=[instanceId, ],)
        # print(response)
        print("terminat ec2 instance complete ")
        
def s3EemptyDelete(s3Name):
        print("s3EemptyDelete: " + s3Name)
        bucket = s3Client.Bucket(s3Name)
        bucket.objects.all().delete()
        bucket.delete()
        print("s3EemptyDelete complete")





# 
# Script start here
# 

print("")
print("cloud-ppe-detection start up... (╯°□°)╯︵ ┻━┻")
print("")

ec2Client = boto3.client('ec2')
s3Client = boto3.resource('s3')

ec2StartUpBashScript = ("#!/bin/bash\n"
                        "cd /home/ec2-user\n" 
                        "sudo yum -y install git\n" 
                        "git clone https://github.com/adamdon/cloud-ppe-detection.git\n" 
                        "cd cloud-ppe-detection\n" 
                        "touch test.txt")


tagId = createTagId()


securityGroupId = createSecurityGroup()

# creating instances
ec2instanceId = createEc2()
# s3Name = createS3()


# clean up
# deleteSecurtyGroup(securityGroupId)
# ec2Terminate(ec2instanceId)
# s3EemptyDelete(s3Name)

