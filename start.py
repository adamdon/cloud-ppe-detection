import time
import boto3



print("")
print("cloud-ppe-detection start up... (╯°□°)╯︵ ┻━┻")
print("")

timecurrent = int(time.time())
timeStr = str(timecurrent)
tagId = ("_" + timeStr + "_" + "S1025475")

print("* creating resources with tag " + tagId)



ec2Client = boto3.client('ec2')


def create():
        print("creating instance start")
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
        print("creating instance ended")
        return instance


def terminate(instanceId):
        print("terminating instance: " + instanceId)
        response = ec2Client.terminate_instances(InstanceIds=[instanceId, ],)
        # print(response)
        print("terminat instance complete ")


instanceId = create()
# terminate(instanceId)

