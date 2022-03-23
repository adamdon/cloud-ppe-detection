import sys
import time
import boto3


print("")
print("cloud-ppe-detection ex2 updload files...")
print("")

def updloadFile(filename):
    keyname = filename[:-4]
    print("Uploading file: " + filename)
    with open(filename, "rb") as f:
        s3Client.upload_fileobj(f, s3bucketName, filename)
    time.sleep(3)


s3Client = boto3.client('s3')
s3bucketName = sys.argv[1]
# s3bucketName = "s3-1647897276-s1025475"

updloadFile("image1.jpg")
updloadFile("image2.png")
updloadFile("image3.jpg")
updloadFile("image4.jpg")
updloadFile("image5.jpg")


print("Uploaded files to: " + s3bucketName)