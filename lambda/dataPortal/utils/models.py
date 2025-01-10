import os
from enum import Enum

import boto3
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection
from pynamodb.models import Model
from pynamodb.attributes import (
    NumberAttribute,
    UnicodeAttribute,
    UnicodeSetAttribute,
    MapAttribute,
)


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


class UsageMap(MapAttribute):
    quotaSize = NumberAttribute(attr_name="quotaSize")
    quotaQueryCount = NumberAttribute(attr_name="quotaQueryCount")
    usageSize = NumberAttribute(attr_name="usageSize")
    usageCount = NumberAttribute(attr_name="usageCount")


class Quota(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_QUOTA_USER_TABLE")
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    CostEstimation = NumberAttribute()
    Usage = UsageMap()

    def to_dict(self):
        return {
            "uid": self.uid,
            "CostEstimation": self.CostEstimation,
            "Usage": self.Usage.as_dict(),
        }


class SavedQueries(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_SAVED_QUERIES_TABLE")
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    description = UnicodeAttribute(default_for_new="")
    query = UnicodeAttribute()
