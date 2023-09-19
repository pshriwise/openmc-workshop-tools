"""Start Jupyter Lab servers on the AWS instances."""
import boto3

from utils import aws_config, EC2InstanceStatus

# Define parameters.
KEYPAIR_PATH = aws_config['ec2']['keypair_path']
GROUPNAME = aws_config['workshop'].get('group_name', 'openmc-workshop')

# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [GROUPNAME]}
resp = ec2.describe_instances(Filters=[filt])

# Get the public IP addresses for each running instance.
instance_ids = []
for res in resp['Reservations']:
    for inst in res['Instances']:
        # Ignore instances that are not running.
        if inst['State']['Code'] != EC2InstanceStatus.RUNNING:
            continue

        instance_ids.append(inst['InstanceId'])


print('\n'.join(instance_ids))
print(f'{len(instance_ids)} instances found.')

if instance_ids:
    ec2.stop_instances(InstanceIds=instance_ids, Force=True)

print(f'Stopped {len(instance_ids)} instances.')
