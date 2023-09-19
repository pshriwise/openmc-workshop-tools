"""Start Jupyter Lab servers on the AWS instances."""
import subprocess

import boto3

from util import aws_config


# Define parameters
KEYPAIR_PATH = aws_config['ec2']['keypair_path']
BRANCH_NAME = aws_config['repo']['branch_name']
GROUPNAME = aws_config['workshop'].get('group_name', 'openmc-workshop')
REPO_DIR = aws_config['repo'].get('repo_location', '~/openmc-workshop')

# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [GROUPNAME]}
resp = ec2.describe_instances(Filters=[filt])

# Get the public IP addresses for each running instance.
instance_ips = []
for res in resp['Reservations']:
    for inst in res['Instances']:
        # Ignore instances that are not running.
        if inst['State']['Code'] != 16:
            continue

        instance_ips.append(inst['PublicIpAddress'])

# SSH into each instance and start the server.
for inst_ip in instance_ips:
    args = ['ssh', '-o', 'UserKnownHostsFile=/dev/null', '-o',
            'StrictHostKeyChecking=no', '-i', KEYPAIR_PATH,
            f'ubuntu@{inst_ip}', 'bash -i']
    ssh_process = subprocess.Popen(args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
    ssh_process.stdin.write(f'cd {REPO_DIR} \n')
    ssh_process.stdin.write(f'ls \n')
    ssh_process.stdin.write(f'git status -uno \n')
    ssh_process.stdin.write('exit\n')
    ssh_process.stdin.close()
    ssh_process.stdout.close()
    ssh_process.wait()
    if ssh_process.returncode < 0:
        raise subprocess.CalledProcessError
    print()
