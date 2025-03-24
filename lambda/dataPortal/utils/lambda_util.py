import boto3
import json


def invoke_lambda_function(function_name, payload, event=False):
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="Event" if event else "RequestResponse",
        Payload=json.dumps(payload),
    )
    print(f'Invoked lambda function: "{function_name}" with requestID: "{response['ResponseMetadata']['RequestId']}" as {"event" if event else "request"}')
    return response if event else json.loads(response["Payload"].read())
