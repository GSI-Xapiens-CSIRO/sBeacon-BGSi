import os
from enum import Enum

import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute


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


class InstanceStatus(Enum):
    PENDING = "Pending"
    IN_SERVICE = "InService"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    FAILED = "Failed"
    DELETING = "Deleting"
    UPDATING = "Updating"


class JupyterInstances(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_JUPYTER_INSTANCES_TABLE")
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    instanceName = UnicodeAttribute(range_key=True)
