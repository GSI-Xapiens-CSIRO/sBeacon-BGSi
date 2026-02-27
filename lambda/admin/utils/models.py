"""
PynamoDB Models for Admin User Data Cleanup
All DynamoDB tables that store user-related data (Cognito sub)
"""

import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection

from shared.utils.lambda_utils import ENV_DYNAMO


class ProjectUsersIndex(GlobalSecondaryIndex):
    """GSI for querying ProjectUsers by uid"""
    class Meta:
        index_name = ENV_DYNAMO.DYNAMO_PROJECT_USERS_UID_INDEX
        projection = KeysOnlyProjection()
    uid = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)


class ProjectUsers(Model):
    """Many-to-many mapping: users <-> projects"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_PROJECT_USERS_TABLE
        region = boto3.session.Session().region_name
    name = UnicodeAttribute(hash_key=True)
    uid = UnicodeAttribute(range_key=True)
    uid_index = ProjectUsersIndex()


class ClinicJobs(Model):
    """Clinical workflow jobs per user"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_CLINIC_JOBS_TABLE
        region = boto3.session.Session().region_name
    job_id = UnicodeAttribute(hash_key=True)
    uid = UnicodeAttribute()


class ClinicalAnnotations(Model):
    """User-created clinical annotations"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_CLINICAL_ANNOTATIONS_TABLE
        region = boto3.session.Session().region_name
    project_job = UnicodeAttribute(hash_key=True)
    annotation_name = UnicodeAttribute(range_key=True)
    uid = UnicodeAttribute()


class ClinicalVariants(Model):
    """Clinical variant collections"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_CLINICAL_VARIANTS_TABLE
        region = boto3.session.Session().region_name
    project_job = UnicodeAttribute(hash_key=True)
    collection_name = UnicodeAttribute(range_key=True)
    uid = UnicodeAttribute()


class JupyterInstances(Model):
    """Jupyter notebooks per user"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_JUPYTER_INSTANCES_TABLE
        region = boto3.session.Session().region_name
    uid = UnicodeAttribute(hash_key=True)
    instanceName = UnicodeAttribute(range_key=True)


class SavedQueries(Model):
    """User saved sBeacon queries"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_SAVED_QUERIES_TABLE
        region = boto3.session.Session().region_name
    uid = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(range_key=True)


class CliUpload(Model):
    """CLI upload sessions per user"""
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_CLI_UPLOAD_TABLE
        region = boto3.session.Session().region_name
    uid = UnicodeAttribute(hash_key=True)
    upload_id = UnicodeAttribute(range_key=True)
