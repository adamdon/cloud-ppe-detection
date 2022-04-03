# cloud-ppe-detection

A cloud application that deploys a fully automated AWS system, this system scans images using pre-trained models to provide both Personal Protective Equipment (PPE) and item Label detection. The results report on Labels found as well as if any detected persons are wearing full PPE correctly on both hands and face.  

## System Architecture

![Systems Architecture](https://raw.githubusercontent.com/adamdon/cloud-ppe-detection/main/systems_architecture.png)

## CloudFormation Design

![CloudFormation Design](https://raw.githubusercontent.com/adamdon/cloud-ppe-detection/main/cloudformation_design.png)

## Installation

With Python and [boto3](https://github.com/boto/boto3) installed, the application can be run from anywhere with access to your aws credentials. The simplest way to do this if from the [Cloud9](https://aws.amazon.com/cloud9/) IDE.  

```bash
pip install boto3
git clone https://github.com/adamdon/cloud-ppe-detection.git
cd cloud-ppe-detection
```

## Environment

The only AWS setup required is to have a IAM Role with permissions for CreateRole and AttachRolePolicy. A valid RSA key pair must also be in place for use with the EC2

If the permissions aren't in place you can add the IAM policy bellow to any Role.    

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "iam:AttachRolePolicy",
        "iam:CreateRole"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
```
To use the optional SMS alert feature, ensure that your account is out of [SNS Sandbox](https://docs.aws.amazon.com/sns/latest/dg/sns-sms-sandbox.html). If this is not the case you can just pre-authorise your cell phone number and make sure the budget is set to at least $1.


## Usage

There are three parameters configuration options for running the application.

**Default values**
(suitable for AWS Academy Learner Lab)
```bash
python3 start.py
```

**Custom values** ("tagSuffix" is the unique name to add to all resources)
```bash 
python3 start.py [tagSuffix] [iamName] [KeyName]
```
**Custom values (optional)** ("alertNumber" is a mobile number for PPE violation alerts)
```bash 
python3 start.py [tagSuffix] [iamName] [KeyName] [alertNumber]
```

*examples* 
```bash 
python3 start.py
python3 start.py s1025475 LabRole vockey
python3 start.py s1025475 LabRole vockey +447700900000
```

The output is viewable from the DynamoDB Table resource. 

## License
[MIT](https://github.com/adamdon/cloud-ppe-detection/blob/main/LICENSE.md)