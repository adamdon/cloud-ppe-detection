import sys
import boto3


print("")
print("cloud-ppe-detection ex2 updload files...")
print("")

s3bucketName = sys.argv[1]
s3Client = boto3.resource('s3')

print("Uploading files to: " + s3bucketName)