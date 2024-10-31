import json
import os

import boto3
from botocore.exceptions import ClientError

from utils.router import PortalError, LambdaRouter
from utils.models import NextflowInstances, InstanceStatus

ec2_client = boto3.client("ec2")
ec2_instance_connect_client = boto3.client("ec2-instance-connect")
router = LambdaRouter()


@router.attach("/dportal/nextflow", "post")
def create_nextflow_server(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body_dict = json.loads(event.get("body"))
    instance_name = body_dict.get("instanceName")
    volume_size = body_dict.get("volumeSize")
    instance_type = body_dict.get("instanceType")
    identity_id = body_dict.get("identityId")

    if NextflowInstances.count(sub, NextflowInstances.instanceName == instance_name) > 0:
        raise PortalError(
            error_code=409,
            error_message=f"A nextflow instance with the name {instance_name} already exists."
        )

    response = ec2_client.run_instances(
        BlockDeviceMappings = [
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {
                    "DeleteOnTermination": True,
                    "VolumeSize": volume_size,
                    "VolumeType": "gp3",
                    "Encrypted": True
                }
            }
        ],
        ImageId="ami-0f71013b2c8bd2c29",  # AMI ID for AL2
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": instance_name},
                    {"Key": "IdentityId", "Value": identity_id}
                ]
            }
        ],
        UserData="""
        #!/bin/bash
        yum update -y
        yum install -y docker git java-11-openjdk unzip

        # Start Docker
        systemctl start docker
        systemctl enable docker

        # Install Nextflow
        curl -s https://get.nextflow.io | bash
        mv nextflow /usr/local/bin/

        # Create a project directory for user customization
        mkdir -p /home/ec2-user/nextflow-project
        chown ec2-user:ec2-user /home/ec2-user/nextflow-project

        # Add example config
        cat <<EOF > /home/ec2-user/nextflow-project/nextflow.config
        manifest {
            name = "User Customizable Pipeline"
            nextflowVersion = ">=24.04.4"
        }
        docker {
            enabled = true
        }
        EOF
        chown ec2-user:ec2-user /home/ec2-user/nextflow-project
        """,
        #IamInstanceProfile={"Name": "EC2-Nextflow-Role"}
    )
    instance_id = response["Instances"][0]["InstanceId"]
    entry = NextflowInstances(uid=sub, instanceName=instance_name, instanceId=instance_id)
    entry.save()

    return entry.attribute_values 

@router.attach("/dportal/nextflow", "get")
def list_my_nextflow_servers(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    instances = [
        nf.attribute_values["instanceName"] for nf in NextflowInstances.query(sub)
    ]

    return instances

@router.attach("/dportal/nextflow/{name}", "get")
def get_my_nextflow_server_status(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    instance_name = event["pathParameters"]["name"]
    instances = [nf for nf in NextflowInstances.query(sub)]
    instances = [
        [nf.attribute_values["instanceName"], nf.attribute_values["instanceId"]] for nf in NextflowInstances.query(sub)
    ]
    if len(instances) == 0:
        raise PortalError(
            error_code=404, error_message=f"No Nextflow instance was found with that name."
        )
    for instance in instances:
        if instance_name == instance[0]:
            instance_id = instance[1]
            break
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidInstanceID.Malformed":
            raise PortalError(
                error_code=404, error_message=f"The name matched a record, but the associated EC2 instance is unavailable."
            )
    return response["Reservations"][0]["Instances"][0]["State"]["Name"].capitalize()
