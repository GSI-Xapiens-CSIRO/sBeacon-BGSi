import json
import os

import boto3

from shared.apiutils import LambdaRouter, PortalError
from utils.models import JupyterInstances, InstanceStatus

sagemaker_client = boto3.client("sagemaker")
router = LambdaRouter()


@router.attach("/dportal/notebooks", "post")
def create_notebook(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body_dict = json.loads(event.get("body"))
    # TODO ensure name does not exceed 63 chars
    notebook_name = body_dict.get("instanceName")
    volume_size = body_dict.get("volumeSize")
    instance_type = body_dict.get("instanceType")
    # TODO check if this can be done better
    identity_id = body_dict.get("identityId")

    if JupyterInstances.count(sub, JupyterInstances.instanceName == notebook_name) > 0:
        raise PortalError(
            error_code=409,
            error_message=f"A notebook with the name {notebook_name} already exists.",
        )

    sagemaker_client.create_notebook_instance(
        NotebookInstanceName=f"{notebook_name}-{sub}",
        InstanceType=instance_type,
        VolumeSizeInGB=int(volume_size),
        RoleArn=os.getenv("JUPYTER_INSTACE_ROLE_ARN"),
        DirectInternetAccess="Enabled",
        RootAccess="Disabled",
        Tags=[{"Key": "IdentityId", "Value": identity_id}],
    )
    entry = JupyterInstances(sub, notebook_name)
    entry.save()

    return entry.attribute_values


@router.attach("/dportal/notebooks", "get")
def list_my_notebooks(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    notebooks = [
        nb.attribute_values["instanceName"] for nb in JupyterInstances.query(sub)
    ]

    return notebooks


@router.attach("/dportal/notebooks/{name}", "get")
def get_my_notebook_status(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    notebook_name = f"{name}-{sub}"
    response = sagemaker_client.describe_notebook_instance(
        NotebookInstanceName=notebook_name
    )
    notebook_status = response["NotebookInstanceStatus"]
    volme_size = response["VolumeSizeInGB"]
    instance_type = response["InstanceType"]

    return {
        "status": notebook_status,
        "volumeSize": volme_size,
        "instanceType": instance_type,
    }


@router.attach("/dportal/notebooks/{name}/stop", "post")
def stop_my_notebook(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    notebook_name = f"{name}-{sub}"

    status = sagemaker_client.describe_notebook_instance(
        NotebookInstanceName=notebook_name
    )["NotebookInstanceStatus"]

    if InstanceStatus(status) != InstanceStatus.IN_SERVICE:
        raise PortalError(
            error_code=409,
            error_message=f"Notebook must be in service before stopping.",
        )

    response = sagemaker_client.stop_notebook_instance(
        NotebookInstanceName=notebook_name
    )

    return response


@router.attach("/dportal/notebooks/{name}/start", "post")
def start_my_notebook(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    notebook_name = f"{name}-{sub}"

    status = sagemaker_client.describe_notebook_instance(
        NotebookInstanceName=notebook_name
    )["NotebookInstanceStatus"]

    if InstanceStatus(status) != InstanceStatus.STOPPED:
        raise PortalError(
            error_code=409, error_message=f"Notebook must be stopped before starting."
        )

    response = sagemaker_client.start_notebook_instance(
        NotebookInstanceName=notebook_name
    )

    return response


@router.attach("/dportal/notebooks/{name}/delete", "post")
def delete_my_notebook(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    notebook_name = f"{name}-{sub}"

    status = sagemaker_client.describe_notebook_instance(
        NotebookInstanceName=notebook_name
    )["NotebookInstanceStatus"]

    if InstanceStatus(status) != InstanceStatus.STOPPED:
        raise PortalError(
            error_code=409, error_message=f"Notebook must be stopped before deleting."
        )

    response = sagemaker_client.delete_notebook_instance(
        NotebookInstanceName=notebook_name
    )
    JupyterInstances(sub, name).delete()

    return response


@router.attach("/dportal/notebooks/{name}", "put")
def update_my_notebook(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    notebook_name = f"{name}-{sub}"
    body_dict = json.loads(event.get("body"))
    volume_size = body_dict.get("volumeSize")
    instance_type = body_dict.get("instanceType")

    status = sagemaker_client.describe_notebook_instance(
        NotebookInstanceName=notebook_name
    )["NotebookInstanceStatus"]

    if InstanceStatus(status) != InstanceStatus.STOPPED:
        raise PortalError(
            error_code=409, error_message=f"Notebook must be stopped before updating."
        )

    response = sagemaker_client.update_notebook_instance(
        NotebookInstanceName=notebook_name,
        InstanceType=instance_type,
        VolumeSizeInGB=int(volume_size),
    )
    return response


@router.attach("/dportal/notebooks/{name}/url", "get")
def get_url(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    notebook_name = f"{name}-{sub}"
    response = sagemaker_client.create_presigned_notebook_instance_url(
        NotebookInstanceName=notebook_name
    )

    return response
