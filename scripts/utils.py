from configparser import ConfigParser
from enum import IntEnum


aws_config = ConfigParser()
aws_config.read('workshop_config.ini')


class EC2InstanceStatus(IntEnum):
    """
    Based on values listed here:
    https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInstanceStatus.html
    """
    PENDING = 0
    RUNNING = 16
    SHUTTING_DOWN = 32
    TERMINATED = 48
    STOPPING = 64
    STOPPED = 80


def get_aws_tag(tags, key):
    """Retrieve a tag value for the given key.

    Returns None if the given key is not in the tags.

    """
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']

    return None
