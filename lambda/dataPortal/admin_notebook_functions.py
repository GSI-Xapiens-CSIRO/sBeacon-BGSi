import os

import boto3

from utils.router import LambdaRouter, PortalError
from utils.models import InstanceStatus, JupyterInstances
from utils.cognito import get_user_from_attribute, get_user_attribute
from shared.cognitoutils import authenticate_admin

router = LambdaRouter()
cognito_client = boto3.client("cognito-idp")
sagemaker_client = boto3.client("sagemaker")
USER_POOL_ID = os.environ.get("USER_POOL_ID")
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


#
# Project User Functions
#


@router.attach("/dportal/admin/notebooks", "get", authenticate_admin)
def list_notebooks(event, context):
    instances = list(JupyterInstances.scan())
    statuses = [
        sagemaker_client.describe_notebook_instance(
            NotebookInstanceName=f"{instance.instanceName}-{instance.uid}"
        )
        for instance in instances
    ]

    return [
        {
            "instanceName": f"{instance.instanceName}-{instance.uid}",
            "userFirstName": get_user_attribute(
                get_user_from_attribute("sub", instance.uid), "given_name"
            ),
            "userLastName": get_user_attribute(
                get_user_from_attribute("sub", instance.uid), "family_name"
            ),
            "userEmail": get_user_attribute(
                get_user_from_attribute("sub", instance.uid), "email"
            ),
            "status": status["NotebookInstanceStatus"],
            "volumeSize": status["VolumeSizeInGB"],
            "instanceType": status["InstanceType"],
        }
        for instance, status in zip(instances, statuses)
    ]


@router.attach("/dportal/admin/notebooks/{name}", "get", authenticate_admin)
def get_notebook_status(event, context):
    notebook_name = event["pathParameters"]["name"]

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


@router.attach("/dportal/admin/notebooks/{name}/stop", "post", authenticate_admin)
def stop_notebook(event, context):
    notebook_name = event["pathParameters"]["name"]

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


@router.attach("/dportal/admin/notebooks/{name}/delete", "post", authenticate_admin)
def delete_my_notebook(event, context):
    notebook_name = event["pathParameters"]["name"]

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
    JupyterInstances(notebook_name[-36:], notebook_name[:-37]).delete()

    return response
