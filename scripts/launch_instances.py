"""Launch AWS instances that will host the Jupyter Lab notebooks.

Note that this script will attach a "ws_group" tag to each instance and set it
to the given group name. The group name is purely a bookkeeping measure which
makes it easier to e.g handle machines for workshop hosts differently than
machines for participants.

"""

import sys

import boto3


# Define parameters.
#IMAGE_ID = 'ami-0479c7fcf536b157c' # NEA Course
IMAGE_ID = 'ami-0a7819cfcb08b9d71'
KEYPAIR_NAME = 'X1 Extreme 2'
SECURITY_GROUP = 'sg-130bcb6b'

# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the group name and number of instances from commandline args.
groupname = sys.argv[1]
n_instances = int(sys.argv[2])

# Launch the instances.
resp = ec2.run_instances(
    ImageId=IMAGE_ID,
    MinCount=n_instances,
    MaxCount=n_instances,
    InstanceType='c6i.large',
    KeyName=KEYPAIR_NAME,
    SecurityGroupIds=(SECURITY_GROUP, ),
    TagSpecifications=[{
      'ResourceType': 'instance',
      'Tags': [{'Key': 'ws_group', 'Value': groupname}]
    }],
    )

print(resp)
print()

for inst in resp['Instances']:
    print(inst['InstanceId'])
    print(inst['PrivateIpAddress'])
    print()
