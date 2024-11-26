import boto3
import json


def invoke_lambda_function(function_name, payload, event=False):
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="Event" if event else "RequestResponse",
        Payload=json.dumps(payload),
    )

    return response if event else json.loads(response["Payload"].read())
