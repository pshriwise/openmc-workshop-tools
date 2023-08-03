"""Launch AWS instances that will host the Jupyter Lab notebooks.

Note that this script will attach a "ws_group" tag to each instance and set it
to the given group name. The group name is purely a bookkeeping measure which
makes it easier to e.g handle machines for workshop hosts differently than
machines for participants.

"""

import sys

import boto3

from configparser import ConfigParser

config = ConfigParser()
config.read('workshop_config.ini')

# Define parameters.
AMI = config['ec2'].get('ami')
KEYPAIR_NAME = config['ec2'].get('keypair_name')
SECURITY_GROUP = config['ec2'].get('security_group')
INSTANCE_TYPE = config['ec2'].get('instance_type','t3a.medium')
GROUPNAME = config['workshop'].get('group_name', 'openmc-workshop')
# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the group name and number of instances from commandline args.
n_instances = int(sys.argv[1])

# Launch the instances.
resp = ec2.run_instances(
    ImageId=AMI,
    MinCount=n_instances,
    MaxCount=n_instances,
    InstanceType=INSTANCE_TYPE,
    KeyName=KEYPAIR_NAME,
    SecurityGroupIds=(SECURITY_GROUP, ),
    TagSpecifications=[{
      'ResourceType': 'instance',
      'Tags': [{'Key': 'ws_group', 'Value': GROUPNAME}]
    }],
    )

print('------ Request Response ------')
print(resp)
print('------ Request Response ------\n')

for inst in resp['Instances']:
    print('------')
    print(f'Instance ID: {inst["InstanceId"]}')
    print(f'Private IP: {inst["PrivateIpAddress"]}')
    print('------\n')
