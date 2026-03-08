#!/usr/bin/env python3

"""
Launch an EC2 parent instance with Nitro Enclaves enabled.

Configuration is loaded from utils.aws_config.
"""

import json
import sys
import time

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from utils import aws_config


# ----------------------------
# Config values
# ----------------------------

REGION = aws_config['ec2']['region']
AMI = aws_config['ec2']['server_ami']
KEYPAIR_NAME = aws_config['ec2']['keypair_name']
SECURITY_GROUP_NAME = aws_config['ec2']['security_group']
INSTANCE_TYPE = aws_config['ec2']['instance_type']

CERTIFICATE_ARN = aws_config['acm']['arn']

ROLE_NAME = "nitro-enclave-ec2-role"
INSTANCE_PROFILE_NAME = "nitro-enclave-ec2-instance-profile"
INLINE_POLICY_NAME = "NitroEnclaveAcmAccess"

INSTANCE_NAME = aws_config['workshop'].get(
    'group_name',
    'nitro-enclave-parent'
)


# ----------------------------
# Validation
# ----------------------------

def validate_instance_type_supports_enclaves():

    ec2 = boto3.client("ec2", region_name=REGION)

    response = ec2.describe_instance_types(
        InstanceTypes=[INSTANCE_TYPE]
    )

    info = response["InstanceTypes"][0]

    support = info.get("NitroEnclavesSupport", "unsupported")

    if support != "supported":
        raise RuntimeError(
            f"Instance type '{INSTANCE_TYPE}' does not support Nitro Enclaves"
        )


def validate_certificate_region():

    arn_parts = CERTIFICATE_ARN.split(":")

    if len(arn_parts) < 6:
        raise RuntimeError(f"Invalid certificate ARN: {CERTIFICATE_ARN}")

    cert_region = arn_parts[3]

    if cert_region != REGION:
        raise RuntimeError(
            f"Certificate region '{cert_region}' does not match EC2 region '{REGION}'"
        )


# ----------------------------
# Infrastructure resolution
# ----------------------------

def resolve_default_vpc():

    ec2 = boto3.client("ec2", region_name=REGION)

    response = ec2.describe_vpcs(
        Filters=[{"Name": "is-default", "Values": ["true"]}]
    )

    vpcs = response["Vpcs"]

    if not vpcs:
        raise RuntimeError("No default VPC found")

    return vpcs[0]["VpcId"]


def resolve_subnet(vpc_id):

    ec2 = boto3.client("ec2", region_name=REGION)

    response = ec2.describe_subnets(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "default-for-az", "Values": ["true"]},
        ]
    )

    subnets = response["Subnets"]

    if not subnets:
        raise RuntimeError("No default subnet found")

    subnets.sort(key=lambda s: (s["AvailabilityZone"], s["SubnetId"]))

    return subnets[0]["SubnetId"]


def resolve_security_group(vpc_id):

    ec2 = boto3.client("ec2", region_name=REGION)

    response = ec2.describe_security_groups(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "group-name", "Values": [SECURITY_GROUP_NAME]},
        ]
    )

    groups = response["SecurityGroups"]

    if not groups:
        raise RuntimeError(
            f"Security group '{SECURITY_GROUP_NAME}' not found in VPC {vpc_id}"
        )

    groups.sort(key=lambda g: g["GroupId"])

    return groups[0]["GroupId"]


# ----------------------------
# IAM setup
# ----------------------------

def ec2_assume_role_policy():

    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }]
    }


def build_inline_acm_policy():

    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "acm:DescribeCertificate",
                "acm:GetCertificate",
                "acm:ListCertificates"
            ],
            "Resource": CERTIFICATE_ARN
        }]
    }


def ensure_role(iam):

    try:
        response = iam.get_role(RoleName=ROLE_NAME)
        return response["Role"]["Arn"], False

    except iam.exceptions.NoSuchEntityException:

        response = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(
                ec2_assume_role_policy()
            ),
            Description="Nitro Enclave EC2 role",
        )

        return response["Role"]["Arn"], True


def ensure_inline_policy(iam):

    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName=INLINE_POLICY_NAME,
        PolicyDocument=json.dumps(
            build_inline_acm_policy()
        ),
    )


def ensure_instance_profile(iam):

    try:

        response = iam.get_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME
        )

        return response["InstanceProfile"]["Arn"], False

    except iam.exceptions.NoSuchEntityException:

        response = iam.create_instance_profile(
            InstanceProfileName=INSTANCE_PROFILE_NAME
        )

        return response["InstanceProfile"]["Arn"], True


def ensure_role_in_instance_profile(iam):

    response = iam.get_instance_profile(
        InstanceProfileName=INSTANCE_PROFILE_NAME
    )

    roles = response["InstanceProfile"].get("Roles", [])

    for role in roles:
        if role["RoleName"] == ROLE_NAME:
            return False

    iam.add_role_to_instance_profile(
        InstanceProfileName=INSTANCE_PROFILE_NAME,
        RoleName=ROLE_NAME
    )

    return True


def ensure_role_and_instance_profile():

    iam = boto3.client("iam")

    ensure_role(iam)
    ensure_inline_policy(iam)
    ensure_instance_profile(iam)

    for _ in range(10):

        try:
            ensure_role_in_instance_profile(iam)
            break

        except ClientError:
            time.sleep(2)

# ----------------------------
# User confirmation
# ----------------------------

def confirm_launch():
    while True:
        answer = input("Proceed with launching instance? [y/n]: ").strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter 'y' or 'n'.")

# ----------------------------
# Launch instance
# ----------------------------

def launch_instance(subnet, sg_id):

    ec2 = boto3.client("ec2", region_name=REGION)

    try:
        response = ec2.run_instances(

            ImageId=AMI,
            InstanceType=INSTANCE_TYPE,

            MinCount=1,
            MaxCount=1,

            KeyName=KEYPAIR_NAME,

            IamInstanceProfile={
                "Name": INSTANCE_PROFILE_NAME
            },

            EnclaveOptions={
                "Enabled": True
            },

            SubnetId=subnet,
            SecurityGroupIds=[sg_id],

            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": INSTANCE_NAME}
                ],
            }],
        )
    except ClientError as e:
        print(
            "Error encountered. If this is the first time running this. "
            "Wait a few moments and try again, as IAM role and instance "
            "profile changes may take some time to propagate."
        )
        raise RuntimeError(f"Failed to launch instance: {e}")
    return response["Instances"][0]["InstanceId"]


# ----------------------------
# Main
# ----------------------------

def main():

    try:

        validate_instance_type_supports_enclaves()
        validate_certificate_region()

        vpc = resolve_default_vpc()

        subnet = resolve_subnet(vpc)

        sg = resolve_security_group(vpc)

        ensure_role_and_instance_profile()

        print("Resolved configuration")
        print("  VPC:", vpc)
        print("  Subnet:", subnet)
        print("  Security group:", sg)

        if not confirm_launch():
            print("Launch cancelled.")
            sys.exit(0)

        instance_id = launch_instance(subnet, sg)

        print("\nInstance launched:", instance_id)

    except (ClientError, BotoCoreError, RuntimeError) as e:

        print("ERROR:", e)

        sys.exit(1)


if __name__ == "__main__":
    main()