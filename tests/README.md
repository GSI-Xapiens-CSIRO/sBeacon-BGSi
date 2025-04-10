# Integration and Unit Tests

This directory contains integrations and unit tests for sBeacon.

Please note that we use `moto` to mock most of the AWS boto3 API calls we make.

## Running tests

Each folder corresponds to a lambda function with the exception of `test_utils`.

```bash
cd <TEST FOLDER>
pytest  -p no:warnings -vv
```

Output look like below

```text
=================== test session starts ====================
platform linux -- Python 3.12.8, pytest-8.3.5, pluggy-1.5.0 -- /var/lang/bin/python3.12
cachedir: .pytest_cache
rootdir: /workspaces/GUI/sbeacon/tests/dataportal
plugins: ordering-0.6, order-1.3.0
collected 1 item

test_notebook_functions.py::test_create_notebook PASSED [100%]

==================== 1 passed in 0.86s =====================
```

To run all tests use `bash tests.sh` from this directory.

## Writing New Tests

1. Create a folder if not already there for the corresponding lambda.
2. Add the test function `test_*`.
3. Add any missing resources to the `test_util`.
4. Make sure all the tests are running and succeeds before committing the code.

Note: tests for each lambda function must be run in a separate session (pytest invocation).

# Troubleshooting Notes

There can be missing `moto` APIs. They can be easily mocked.

Refer to the `test_utils/mock_resources.py` file and how it has been used in `dataportal/test_notebook_functions.py`

```python
# test_utils/mock_resources.py
def mock_make_api_call(self, operation_name, kwarg):
    if operation_name == "CreatePresignedNotebookInstanceUrl":
        return {
            "AuthorizedUrl": f"https://notebook-url.aws.amazon.com/sagemaker/{kwarg['NotebookInstanceName']}?token=1234",
        }

    return orig(self, operation_name, kwarg)

# dataportal/test_notebook_functions.py
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
```