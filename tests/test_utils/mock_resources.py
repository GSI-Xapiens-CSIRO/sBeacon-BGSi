import sys
import os
import boto3
from moto import mock_aws

from .env import keys

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../shared_resources/python-modules/python/"
        )
    )
)


for key, value in keys.items():
    os.environ[key] = value

from shared.dynamodb import Quota, UsageMap


@mock_aws
def setup_resources():
    # Create a Cognito User Pool
    cognito_client = boto3.client(
        "cognito-idp", region_name=os.environ["AWS_DEFAULT_REGION"]
    )
    dynamodb_client = boto3.client(
        "dynamodb", region_name=os.environ["AWS_DEFAULT_REGION"]
    )
    sagemaker_client = boto3.client(
        "sagemaker", region_name=os.environ["AWS_DEFAULT_REGION"]
    )

    # create cognito user pool
    response = cognito_client.create_user_pool(
        PoolName=keys["COGNITO_USER_POOL_ID"],
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": True,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": True,
            }
        },
    )

    userpool_id = response["UserPool"]["Id"]
    os.environ["COGNITO_USER_POOL_ID"] = userpool_id

    # create cognito user
    response = cognito_client.admin_create_user(
        UserPoolId=userpool_id,
        Username="testuser",
        TemporaryPassword="testpassword",
        MessageAction="SUPPRESS",
        UserAttributes=[
            {"Name": "email", "Value": "test@test.com"},
            {"Name": "given_name", "Value": "test"},
            {"Name": "family_name", "Value": "Test"},
            {"Name": "email_verified", "Value": "true"},
        ],
    )

    sub = next(filter(lambda x: x["Name"] == "sub", response["User"]["Attributes"]))[
        "Value"
    ]

    Quota.create_table()
    Quota(
        uid=sub,
        CostEstimation=100,
        Usage=UsageMap(quotaSize=100, quotaQueryCount=100, usageSize=50, usageCount=50),
    ).save()

    # create sagemaker life cycle config
    response = sagemaker_client.create_notebook_instance_lifecycle_config(
        NotebookInstanceLifecycleConfigName=keys["JUPYTER_LIFECYCLE_CONFIG_NAME"],
        OnCreate=[
            {
                "Content": f"""#!/bin/bash
                echo "Hello World" > /home/ec2-user/SageMaker/hello.txt
                """,
            },
        ],
        OnStart=[
            {
                "Content": f"""#!/bin/bash
                echo "Hello World" > /home/ec2-user/SageMaker/hello.txt
                """,
            },
        ],
    )
    

    return {
        "sub": sub,
        "userpool_id": userpool_id,
    }


if __name__ == "__main__":
    setup_resources()
