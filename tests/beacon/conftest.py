import os
import sys
from collections import defaultdict
from unittest.mock import patch
import io

import requests
import pytest
import boto3
import botocore
from moto import mock_aws

from test_utils.mock_resources import setup_resources

orig = botocore.client.BaseClient._make_api_call


sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../lambda/getDatasets/")
    )
)
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../../shared_resources/python-modules/python/"
        )
    )
)

from shared.utils import ENV_ATHENA, ENV_DYNAMO


def mock_make_api_call(self, operation_name, kwarg):
    if operation_name == "GetObject":
        # Custom interception for bucket X and prefix Y
        if kwarg.get("Bucket") == ENV_ATHENA.ATHENA_METADATA_BUCKET and kwarg.get(
            "Key", ""
        ).startswith("query-results/"):
            body = b"""id,_assemblyid,_projectname,_datasetname,_vcflocations,_vcfchromosomemap,createdatetime,datauseconditions,description,externalurl,info,name,updatedatetime,version
ci_cd_project:dataset_1,GRCH38,ci_cd_project,dataset_1,"[""s3://gasi-dataportal-uuid/projects/ci_cd_project/project-files/chr1.vcf.gz""]","[{""vcf"": ""s3://gasi-dataportal-uuid/projects/ci_cd_project/project-files/chr1.vcf.gz"", ""chromosomes"": [""1""]}]",2025-05-19 02:22:46.667849+00:00,"{""duoDataUse"": [{""id"": ""DUO:0000042"", ""label"": ""general research use"", ""version"": ""17-07-2016""}]}",Simulation set 1.,http://example.org/wiki/Main_Page,{},Dataset with fake data,2025-05-19 02:22:46.667866+00:00,v1.1
ci_cd_project:dataset_2,GRCH38,ci_cd_project,dataset_2,"[""s3://gasi-dataportal-uuid/projects/ci_cd_project/project-files/chr1.vcf.gz""]","[{""vcf"": ""s3://gasi-dataportal-uuid/projects/ci_cd_project/project-files/chr1.vcf.gz"", ""chromosomes"": [""1""]}]",2025-05-21 03:40:38.758574+00:00,"{""duoDataUse"": [{""id"": ""DUO:0000042"", ""label"": ""general research use"", ""version"": ""17-07-2016""}]}",Simulation set 1.,http://example.org/wiki/Main_Page,{},Dataset with fake data,2025-05-21 03:40:38.758592+00:00,v1.1"""
            stream = io.BytesIO(body)
            return {
                "Body": stream,
                "ContentLength": len(body),
                "ContentType": "text/plain",
                "ResponseMetadata": {
                    "HTTPStatusCode": 200,
                    "RetryAttempts": 0,
                },
                "ContentRange": "bytes 0-768/768",
            }
    if operation_name == "GetQueryResults":
        return {
            "ResultSet": {
                "Rows": [
                    {
                        "Data": [
                            {"VarCharValue": "count"},
                        ]
                    },
                    {
                        "Data": [
                            {"VarCharValue": "2"},
                        ]
                    },
                ],
                "ResultSetMetadata": {
                    "ColumnInfo": [
                        {"Name": "count", "Type": "varchar"},
                    ]
                },
            },
            "UpdateCount": 0,
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
                "RequestId": "mock-request-id",
                "RetryAttempts": 0,
            },
        }

    return orig(self, operation_name, kwarg)


@pytest.fixture(autouse=True, scope="session")
def resources_dict():
    with mock_aws():
        resources = setup_resources()
        dynamodb = boto3.client("dynamodb")

        table_name = ENV_DYNAMO.DYNAMO_PROJECT_USERS_TABLE
        gsi_name = ENV_DYNAMO.DYNAMO_PROJECT_USERS_UID_INDEX

        # Create the table
        response = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {"AttributeName": "uid", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "uid", "KeyType": "HASH"},  # Table Partition Key
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": gsi_name,
                    "KeySchema": [
                        {
                            "AttributeName": "uid",
                            "KeyType": "HASH",
                        },
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                },
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )

        dynamodb.put_item(
            TableName=table_name,
            Item={
                "uid": {"S": resources["guest_sub"]},
                "name": {"S": "ci_cd_project"},
            },
        )

        athena = boto3.client("athena")
        athena.create_work_group(
            Name=ENV_ATHENA.ATHENA_WORKGROUP,
            Configuration={
                "ResultConfiguration": {
                    "OutputLocation": f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/athena/results/",
                    "EncryptionConfiguration": {
                        "EncryptionOption": "SSE_S3",
                    },
                }
            },
        )

        with patch(
            "botocore.client.BaseClient._make_api_call",
            new=mock_make_api_call,
        ):
            yield resources
