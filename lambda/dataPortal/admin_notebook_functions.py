import json
import os

import boto3
from pynamodb.exceptions import DeleteError

from shared.apiutils import LambdaRouter, PortalError
from utils.models import InstanceStatus, JupyterInstances
from utils.cognito import list_users, get_user_from_attribute, get_user_attribute
from utils.sagemaker import list_all_notebooks
from shared.cognitoutils import authenticate_manager

router = LambdaRouter()
cognito_client = boto3.client("cognito-idp")
sagemaker_client = boto3.client("sagemaker")
USER_POOL_ID = os.environ.get("USER_POOL_ID")
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


#
# Project User Functions
#


@router.attach("/dportal/admin/notebooks", "get", authenticate_manager)
def list_notebooks(event, context):
    query_params = event.get("queryStringParameters", {})
    if query_params:
        limit = int(query_params.get("limit", 3))
        last_evaluated_index = int(query_params.get("last_evaluated_index", 0))
        search_term = query_params.get("search", None)

    instances = JupyterInstances.scan()
    if search_term:
        search_term = search_term.lower()
        users = list_users()
        subs = {
            user["sub"]
            for user in users
            if search_term in user.get("email", "").lower()
            or search_term in user.get("given_name", "").lower()
            or search_term in user.get("last_name", "").lower()
        }
        instances = [
            instance
            for instance in instances
            if instance.uid in subs or search_term in instance.instanceName.lower()
        ]

    instance_dict = {
        f"{instance.instanceName}-{instance.uid}": instance for instance in instances
    }
    sorted_instance_keys = sorted(instance_dict.keys())

    total_count = len(sorted_instance_keys)
    start_index = last_evaluated_index
    end_index = min(start_index + limit, total_count)

    paginated_instance_keys = sorted_instance_keys[start_index:end_index]
    paginated_instance_dict = {
        key: instance_dict[key] for key in paginated_instance_keys
    }

    notebooks = list_all_notebooks(paginated_instance_keys)

    for notebook in notebooks:
        try:
            user = get_user_from_attribute(
                "sub", paginated_instance_dict[notebook["instanceName"]].uid
            )
            notebook["userFirstName"] = get_user_attribute(user, "given_name")
            notebook["userLastName"] = get_user_attribute(user, "family_name")
            notebook["userEmail"] = get_user_attribute(user, "email")
        except (PortalError, KeyError):
            notebook["userFirstName"] = "Unassigned"
            notebook["userLastName"] = "Unassigned"
            notebook["userEmail"] = "Unassigned"

    last_evaluated_index = None if end_index >= total_count else end_index

    response = {
        "success": True,
        "notebooks": notebooks,
        "lastEvaluatedIndex": last_evaluated_index,
    }
    print(f"Returning response: {response}")
    return response


@router.attach("/dportal/admin/notebooks/{name}", "get", authenticate_manager)
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


@router.attach("/dportal/admin/notebooks/{name}/stop", "post", authenticate_manager)
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


@router.attach("/dportal/admin/notebooks/{name}/delete", "post", authenticate_manager)
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

    try:
        JupyterInstances(notebook_name[-36:], notebook_name[:-37]).delete()
    except DeleteError:
        print("Notebook not found in database, skipping deletion.")

    return response
