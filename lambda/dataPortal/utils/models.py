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
    ListAttribute,
)


SESSION = boto3.session.Session()
REGION = SESSION.region_name


class ProjectErrorMessages(MapAttribute):
    error = UnicodeAttribute()
    file = UnicodeAttribute()


class Projects(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_PROJECTS_TABLE")
        region = REGION

    name = UnicodeAttribute(hash_key=True)
    name_lower = UnicodeAttribute()
    description = UnicodeAttribute()
    description_lower = UnicodeAttribute()
    files = UnicodeSetAttribute(default=tuple())
    total_samples = NumberAttribute(default=0)
    ingested_datasets = UnicodeSetAttribute(default=tuple())
    error_messages = ListAttribute(default=tuple(), of=ProjectErrorMessages)

    def save(self, *args, **kwargs):
        """Override save() to ensure lowercase fields are stored."""
        self.name_lower = self.name.lower()
        self.description_lower = self.description.lower()
        super().save(*args, **kwargs)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            # Convert set to list for JSON serialization
            "files": list(self.files) if self.files else [],
            "ingested_datasets": (
                list(self.ingested_datasets) if self.ingested_datasets else []
            ),
            "error_messages": [
                message.attribute_values for message in self.error_messages
            ],
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


class ClinicalAnnotations(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_CLINICAL_ANNOTATIONS_TABLE")
        region = REGION

    project_job = UnicodeAttribute(hash_key=True)
    annotation_name = UnicodeAttribute(range_key=True)
    annotation = UnicodeAttribute(default="")
    variants = UnicodeAttribute(default="")


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


class SavedQueries(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_SAVED_QUERIES_TABLE")
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)
    description = UnicodeAttribute(default_for_new="")
    savedQuery = UnicodeAttribute(attr_name="query")
