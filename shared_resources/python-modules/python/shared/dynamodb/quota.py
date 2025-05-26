import os

import boto3
from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute, MapAttribute
from shared.utils import ENV_DYNAMO


SESSION = boto3.session.Session()
REGION = SESSION.region_name


class UsageMap(MapAttribute):
    quotaSize = NumberAttribute(attr_name="quotaSize", default=0)
    quotaQueryCount = NumberAttribute(attr_name="quotaQueryCount", default=0)
    usageSize = NumberAttribute(attr_name="usageSize", default=0)
    usageCount = NumberAttribute(attr_name="usageCount", default=0)


class Quota(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_QUOTA_USER_TABLE
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

    def increment_quota(self):
        self.update(actions=[Quota.Usage.usageCount.add(1)])

    def user_has_quota(self):
        return self.Usage.usageCount < self.Usage.quotaQueryCount
