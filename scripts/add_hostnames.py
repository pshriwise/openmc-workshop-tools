"""Add ws_hostname tags to Jupyter instances."""
import boto3

from utils import aws_config, get_aws_tag, EC2InstanceStatus

# Connect to EC2
ec2 = boto3.client('ec2')

# Get the group name from the commandline
GROUPNAME = aws_config['workshop'].get('group_name', 'openmc-workshop')

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [GROUPNAME]}
resp = ec2.describe_instances(Filters=[filt])

# Look through the instances in this group. If they do not yet have an assigned
# hostname, record their ID so a hostanme can be added. If they do have a
# hostname, record the hostname so that it is not reused.
instance_ids = []
taken_hostnames = set()
for res in resp['Reservations']:
    for inst in res['Instances']:
        # ignore terminated instances
        if inst['State']['Code'] == EC2InstanceStatus.TERMINATED:
            continue
        if inst['State']['Code'] != EC2InstanceStatus.RUNNING:
            continue
        hostname = get_aws_tag(inst['Tags'], 'ws_hostname')

        if hostname is None:
            instance_ids.append(inst['InstanceId'])
        else:
            taken_hostnames.add(hostname)

print('Taken hostnames:')
print('\n'.join(list(taken_hostnames)))
print()

# Assign hostnames to the instances that need them.
for inst_id in instance_ids:
    found = False
    for i in range(1000):
        hostname = f'{GROUPNAME}-{i:d}'
        if hostname not in taken_hostnames:
            taken_hostnames.add(hostname)
            found = True
            break

    assert found

    resp = ec2.create_tags(
        Resources=(inst_id, ),
        Tags=[{'Key': 'ws_hostname', 'Value': hostname}])
    resp = ec2.create_tags(
        Resources=(inst_id, ),
        Tags=[{'Key': 'Name', 'Value': hostname}])
    print(resp)
    print()

    print('------')
    print(f'Instance ID: {inst["InstanceId"]}')
    print(f'Private ID: {inst["PrivateIpAddress"]}')
    print(f'Hostname: {hostname}')
    print('------\n')
