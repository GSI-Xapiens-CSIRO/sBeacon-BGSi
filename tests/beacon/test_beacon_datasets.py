import json
import os
import sys
from unittest.mock import patch

import requests
import boto3
import pytest
from moto import mock_aws


def test_get_datasets(resources_dict):
    import lambda_function

    event = {
        "resource": "/datasets",
        "path": "/datasets",
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
                "projects": ["ci_cd_project"],
                "query": {
                    "filters": [],
                    "requestedGranularity": "record",
                    "pagination": {"skip": 0, "limit": 10},
                },
                "meta": {"apiVersion": "v2.0"},
            }
        ),
    }

    response = lambda_function.lambda_handler(event, {})
    body = json.loads(response["body"])

    assert body["responseSummary"]["exists"] is True
    assert body["responseSummary"]["numTotalResults"] == 2
