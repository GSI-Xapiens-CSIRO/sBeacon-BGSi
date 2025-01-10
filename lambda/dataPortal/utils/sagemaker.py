import boto3

sagemaker_client = boto3.client("sagemaker")


def list_all_notebooks():
    response = sagemaker_client.list_notebook_instances()
    notebooks = response["NotebookInstances"]
    statuses = [
        sagemaker_client.describe_notebook_instance(
            NotebookInstanceName=notebook["NotebookInstanceName"]
        )
        for notebook in notebooks
    ]

    while "NextToken" in response:
        next_token = response["NextToken"]
        response = sagemaker_client.list_notebook_instances(NextToken=next_token)
        notebooks += response["NotebookInstances"]
        statuses += [
            sagemaker_client.describe_notebook_instance(
                NotebookInstanceName=notebook["NotebookInstanceName"]
            )
            for notebook in notebooks
        ]

    return [
        {
            "instanceName": notebook["NotebookInstanceName"],
            "status": notebook["NotebookInstanceStatus"],
            "instanceType": notebook["InstanceType"],
            "volumeSize": status["VolumeSizeInGB"],
        }
        for (notebook, status) in zip(notebooks, statuses)
    ]
