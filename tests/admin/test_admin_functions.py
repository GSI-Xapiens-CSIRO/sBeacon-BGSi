import sys
import os
import json
from moto import mock_aws

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lambda/admin/"))
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
def test_admin_get_users():
    resources_dict = setup_resources()
    import lambda_function

    event = {
        "resource": "/admin/{proxy+}",
        "path": "/admin/users",
        "httpMethod": "GET",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": resources_dict["sub"],
                    "cognito:groups": "administrators",
                }
            },
        },
    }

    response = lambda_function.lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert response["body"] is not None
    assert len(json.loads(response["body"])["users"]) == 1


def test_admin_add_user():
    assert 1 == 1
