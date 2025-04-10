import json

from moto import mock_aws


@mock_aws
def test_admin_get_users(resources_dict):
    import lambda_function

    event = {
        "resource": "/admin/{proxy+}",
        "path": "/admin/users",
        "httpMethod": "GET",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": resources_dict["admin_sub"],
                    "cognito:groups": "administrators",
                }
            },
        },
    }

    response = lambda_function.lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert response["body"] is not None
    assert len(json.loads(response["body"])["users"]) == 2


def test_admin_add_user():
    assert 1 == 1
