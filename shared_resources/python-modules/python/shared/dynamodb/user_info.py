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
        table_name = ENV_DYNAMO.DYNAMO_USER_INFO_TABLE
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    institutionType = UnicodeAttribute(attr_name="institutionType", default="")
    institutionName = UnicodeAttribute(attr_name="institutionName", default="")

    def to_dict(self):
        return {
            "uid": self.uid,
            "institutionType": self.institutionType,
            "institutionName": self.institutionName,
        }
