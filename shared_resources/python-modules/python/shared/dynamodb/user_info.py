import os

import boto3
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
)
from shared.utils import ENV_DYNAMO


SESSION = boto3.session.Session()
REGION = SESSION.region_name


class UserInfo(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_QUOTA_USER_TABLE
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    institutionName = UnicodeAttribute(attr_name="institutionName", default="")

    def to_dict(self):
        return {
            "uid": self.uid,
            "institutionName": self.institutionName,
        }
