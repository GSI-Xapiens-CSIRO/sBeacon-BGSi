import os
from enum import Enum
from datetime import datetime, timezone

import boto3
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection, AllProjection
from pynamodb.models import Model
from pynamodb.attributes import (
    NumberAttribute,
    UnicodeAttribute,
    UnicodeSetAttribute,
    MapAttribute,
    ListAttribute,
    UTCDateTimeAttribute,
)


SESSION = boto3.session.Session()
REGION = SESSION.region_name


def get_current_time_utc():
    return datetime.now(timezone.utc)


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
    pending_files = UnicodeSetAttribute(default=tuple())
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
            "pending_files": list(self.pending_files) if self.pending_files else [],
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


class ClinicJobsProjectNameIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "project-name-index"
        projection = AllProjection()

    project_name = UnicodeAttribute(hash_key=True)


class ClinicJobs(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_CLINIC_JOBS_TABLE")
        region = REGION

    job_id = UnicodeAttribute(hash_key=True)
    job_name = UnicodeAttribute(default="")
    job_name_lower = UnicodeAttribute(default="")  # for case-insensitive search
    created_at = UTCDateTimeAttribute(
        default_for_new=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
    )
    project_name = UnicodeAttribute(default="")
    input_vcf = UnicodeAttribute(default="")
    job_status = UnicodeAttribute(default="")
    failed_step = UnicodeAttribute(default="")
    error_message = UnicodeAttribute(default="")
    uid = UnicodeAttribute(default="")
    project_index = ClinicJobsProjectNameIndex()

    def save(self, *args, **kwargs):
        """Override save() to ensure lowercase fields are stored."""
        self.job_name_lower = self.job_name.lower()
        super().save(*args, **kwargs)


class ClinicalAnnotations(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_CLINICAL_ANNOTATIONS_TABLE")
        region = REGION

    project_job = UnicodeAttribute(hash_key=True)
    annotation_name = UnicodeAttribute(range_key=True)
    annotation = UnicodeAttribute(default="")
    variants = UnicodeAttribute(default="")
    uid = UnicodeAttribute(default="")
    created_at = UTCDateTimeAttribute(default_for_new=get_current_time_utc)


class ClinicalVariants(Model):
    class Meta:
        table_name = os.environ.get("DYNAMO_CLINICAL_VARIANTS_TABLE")
        region = REGION

    project_job = UnicodeAttribute(hash_key=True)
    collection_name = UnicodeAttribute(range_key=True)
    comment = UnicodeAttribute(default="")
    variants = UnicodeAttribute(default="")
    variants_annotations = UnicodeAttribute(default="")
    uid = UnicodeAttribute(default="")
    created_at = UTCDateTimeAttribute(default_for_new=get_current_time_utc)


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
