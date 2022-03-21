import time
import boto3



def createTagId():
        timecurrent = int(time.time())
        timeStr = str(timecurrent)
        tagId = ("-" + timeStr + "-" + "s1025475")
        print("* created tag " + tagId)
        return tagId



def createEc2():
        print("creating Ec2 instance")
        response = ec2Client.run_instances(
                ImageId= 'ami-08e4e35cccc6189f4',
                InstanceType= 't2.micro',
                MaxCount=1,
                MinCount=1,
                KeyName= 'vockey'
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


tagId = createTagId()


# creating instances
ec2instanceId = createEc2()
s3Name = createS3()


# clean up
ec2Terminate(ec2instanceId)
s3EemptyDelete(s3Name)

