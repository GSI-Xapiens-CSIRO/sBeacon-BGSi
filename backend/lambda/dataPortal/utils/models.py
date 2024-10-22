import os

import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute


SESSION = boto3.session.Session()
REGION = SESSION.region_name


class Projects(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_PROJECTS_TABLE")
        region = REGION

    id = UnicodeAttribute(hash_key=True)


class UserProjects(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_USER_PROJECTS_TABLE")
        region = REGION

    id = UnicodeAttribute(hash_key=True)
    uid = UnicodeAttribute(range_key=True)
