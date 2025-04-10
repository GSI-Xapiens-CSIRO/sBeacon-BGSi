import json
import os
import sys
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from test_utils.mock_resources import mock_make_api_call


@pytest.mark.dependency(name="test_create_notebook")
def test_create_notebook(resources_dict):
    import lambda_function
    from utils.models import JupyterInstances

    JupyterInstances.create_table()

    event = {
        "resource": "/dportal/{proxy+}",
        "path": "/dportal/notebooks",
        "httpMethod": "POST",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": resources_dict["guest_sub"],
                    "cognito:groups": "",
                }
            },
        },
        "body": json.dumps(
            {
                "instanceName": "my-instance",
                "volumeSize": "5",
                "instanceType": "ml.t3.medium",
                "identityId": "1234",
            }
        ),
    }

    response = lambda_function.lambda_handler(event, {})

    assert "instanceName" in json.loads(response["body"])
    assert len(list(JupyterInstances.scan())) == 1


def test_get_notebook_url(resources_dict):
    import lambda_function

    event = {
        "resource": "/dportal/{proxy+}",
        "path": "/dportal/notebooks/my-instance-1234/url",
        "httpMethod": "GET",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": resources_dict["guest_sub"],
                    "cognito:groups": "",
                }
            },
        },
    }

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        response = lambda_function.lambda_handler(event, {})

    assert "AuthorizedUrl" in json.loads(
        response["body"]
    ), "AuthorizedUrl must be present"
    assert json.loads(response["body"])["AuthorizedUrl"].startswith(
        f"https://notebook-url.aws.amazon.com/sagemaker/my-instance-1234-{resources_dict["guest_sub"]}"
    ), "AuthorizedUrl must contain concatenated instance name and sub of the user"


@pytest.mark.dependency(depends=["test_create_notebook"])
def test_list_my_notebooks(resources_dict):
    import lambda_function

    event = {
        "resource": "/dportal/{proxy+}",
        "path": "/dportal/notebooks",
        "httpMethod": "GET",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": resources_dict["guest_sub"],
                    "cognito:groups": "",
                }
            },
        },
    }

    response = lambda_function.lambda_handler(event, {})

    # assert response["statusCode"] == 200
    # assert len(json.loads(response["body"])["notebooks"]) == 1
