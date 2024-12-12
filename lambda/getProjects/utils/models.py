import os
from enum import Enum

import boto3
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
