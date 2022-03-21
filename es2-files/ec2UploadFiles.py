import sys
import time
import boto3


print("")
print("cloud-ppe-detection ex2 updload files...")
print("")

def updloadFile(filename):
    keyname = filename[:-4]
    s3Client.upload_file(filename, s3bucketName, keyname)
    time.sleep(3)


s3Client = boto3.resource('s3')
s3bucketName = sys.argv[1]

updloadFile("image1.jpg")

print("Uploading files to: " + s3bucketName)