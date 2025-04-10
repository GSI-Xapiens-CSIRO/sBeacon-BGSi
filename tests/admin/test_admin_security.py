import json
import os
import sys

import pytest
from moto import mock_aws


def test_admin_group_association(resources_dict):
    import random
    import re
    import string

    import lambda_function

    for (route, method), func in lambda_function.router._routes.items():
        parts = route.split("/")

        for n, part in enumerate(parts):
            if re.match(r"{\w+}", part):
                random_string = "".join(
                    random.choices(string.ascii_letters + string.digits, k=10)
                )
                parts[n] = random_string
        route = "/".join(parts)

        event = {
            "resource": route,
            "path": route,
            "httpMethod": method,
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": resources_dict["admin_sub"],
                        "cognito:groups": "",
                    }
                },
            },
            "body": json.dumps(dict()),
        }

        response = lambda_function.lambda_handler(event, {})

        assert (
            response["statusCode"] == 401
        ), "API calls to all admin routes must fail without admin group"


def test_admin_fail_unauthenticated():
    import random
    import re
    import string

    import lambda_function

    print(lambda_function.router._routes)

    for (route, method), func in lambda_function.router._routes.items():
        parts = route.split("/")

        for n, part in enumerate(parts):
            if re.match(r"{\w+}", part):
                random_string = "".join(
                    random.choices(string.ascii_letters + string.digits, k=10)
                )
                parts[n] = random_string
        route = "/".join(parts)

        event = {
            "resource": route,
            "path": route,
            "httpMethod": method,
            "body": json.dumps(dict()),
        }
        res = lambda_function.lambda_handler(event, {})

        assert res["statusCode"] == 500, "API must fail without auth"
