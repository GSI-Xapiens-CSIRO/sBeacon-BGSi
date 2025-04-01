import sys
import os
import json
from moto import mock_aws

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lambda/dataPortal/"))
)
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../shared_resources/python-modules/python/"
        )
    )
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from test_utils.mock_resources import setup_resources


@mock_aws
def test_create_notebook():
    resources_dict = setup_resources()

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
                    "sub": resources_dict["sub"],
                    "cognito:groups": "administrators",
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

    print(response)

    assert "instanceName" in json.loads(response["body"])
    assert len(list(JupyterInstances.scan())) == 1
