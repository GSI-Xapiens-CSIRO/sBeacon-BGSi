import os
from enum import Enum

import boto3
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection
from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute, UnicodeSetAttribute


SESSION = boto3.session.Session()
REGION = SESSION.region_name


class Projects(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_PROJECTS_TABLE")
        region = REGION

    name = UnicodeAttribute(hash_key=True)
    description = UnicodeAttribute()
    files = UnicodeSetAttribute(default=tuple())
    total_samples = NumberAttribute(default=0)
    ingested_datasets = UnicodeSetAttribute(default=tuple())

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            # Convert set to list for JSON serialization
            "files": list(self.files) if self.files else [],
            "ingested_datasets": (
                list(self.ingested_datasets) if self.ingested_datasets else []
            ),
            "total_samples": self.total_samples,
        }


class ProjectUsersIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "uid-index"
        projection = KeysOnlyProjection()

    uid = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)


class ProjectUsers(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_PROJECT_USERS_TABLE")
        region = REGION

    name = UnicodeAttribute(hash_key=True)
    uid = UnicodeAttribute(range_key=True)
    uid_index = ProjectUsersIndex()


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
