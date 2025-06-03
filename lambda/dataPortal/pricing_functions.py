import os
import json
import time

import boto3

from shared.apiutils import LambdaRouter, PortalError
from utils.models import PricingCache
from utils.cognito import get_user_from_attribute, get_user_attribute
from utils.lambda_util import invoke_lambda_function

router = LambdaRouter()


class AWSPricingHelper:
    def __init__(self):
        self.pricing = boto3.client("pricing", region_name="us-east-1")

    def lookup_cache(self, cache_key):
        """
        Implement cache lookup logic here.
        Return None if not found.
        Example: return self.cache.get(cache_key)
        """
        try:
            item = PricingCache.get(
                cache_key,
            )
            if item.expiration < time.time():
                item.delete()
                return None
            return item.pricing
        except PricingCache.DoesNotExist:
            return None

    def save_to_cache(self, cache_key, value):
        """
        Implement logic to save value to cache here.
        Example: self.cache[cache_key] = value
        """
        try:
            item = PricingCache(
                cache_key,
                pricing=value,
                expiration=int(time.time()) + 3600,  # Cache for 1 hour
            )
            item.save()
        except Exception as e:
            print(f"Error saving to cache: {e}")

    def get_price_dimensions(self, data):
        price_list = data.get("PriceList", [])
        if price_list:
            price_data = json.loads(price_list[0])
            terms = price_data["terms"]["OnDemand"]
            term_key = list(terms.keys())[0]
            price_dimensions = terms[term_key]["priceDimensions"]
            return price_dimensions
        return None

    def parse_instance_pricing_data(self, data):
        price_dimensions = self.get_price_dimensions(data)
        if not price_dimensions:
            return None
        key = list(price_dimensions.keys())[0]
        price = price_dimensions[key]["pricePerUnit"]["USD"]
        return float(price)

    def parse_storage_pricing_data(self, data, volume):
        price_dimensions = self.get_price_dimensions(data)
        if not price_dimensions:
            return None
        for pricing in price_dimensions.values():
            end_range_value = pricing["endRange"]
            begin_range = int(pricing["beginRange"])
            if end_range_value == "Inf":
                if begin_range <= volume:
                    return float(pricing["pricePerUnit"]["USD"])
            else:
                if int(end_range_value) >= volume and begin_range <= volume:
                    return float(pricing["pricePerUnit"]["USD"])
        return None

    def parse_athena_pricing_data(self, data):
        price_dimensions = self.get_price_dimensions(data)
        if not price_dimensions:
            return None
        key = list(price_dimensions.keys())[0]
        price = price_dimensions[key]["pricePerUnit"]["USD"]
        return float(price)

    def get_instance_pricing(self, instance_type):
        cache_key = f"sagemaker_{instance_type}_ap-southeast-3"
        cached = self.lookup_cache(cache_key)
        if cached is not None:
            return cached
        params = {
            "ServiceCode": "AmazonSageMaker",
            "MaxResults": 10,
            "Filters": [
                {
                    "Type": "TERM_MATCH",
                    "Field": "regionCode",
                    "Value": "ap-southeast-3",
                },
                {
                    "Type": "TERM_MATCH",
                    "Field": "component",
                    "Value": "studio-jupyterlab",
                },
                {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
            ],
        }
        try:
            data = self.pricing.get_products(**params)
            price = self.parse_instance_pricing_data(data)
            self.save_to_cache(cache_key, price)
            return price
        except Exception as e:
            print("Error fetching SageMaker pricing:", e)
            return None

    def get_ebs_volume_pricing(self, volume_type, volume_size):
        cache_key = f"ebs_{volume_type}_{volume_size}_ap-southeast-3"
        cached = self.lookup_cache(cache_key)

        if cached is not None:
            return cached

        params = {
            "ServiceCode": "AmazonEC2",
            "MaxResults": 100,
            "Filters": [
                {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
                {
                    "Type": "TERM_MATCH",
                    "Field": "regionCode",
                    "Value": "ap-southeast-3",
                },
                {"Type": "TERM_MATCH", "Field": "volumeApiName", "Value": volume_type},
            ],
        }

        try:
            data = self.pricing.get_products(**params)
            price = self.parse_storage_pricing_data(data, volume_size)

            self.save_to_cache(cache_key, price)
            return price
        except Exception as e:
            print("Error fetching EBS volume pricing:", e)
            return None

    def get_volume_pricing(self, volume_size):
        cache_key = f"s3_{volume_size}_ap-southeast-3"
        cached = self.lookup_cache(cache_key)
        if cached is not None:
            return cached
        params = {
            "ServiceCode": "AmazonS3",
            "MaxResults": 10,
            "Filters": [
                {"Type": "TERM_MATCH", "Field": "productFamily", "Value": "Storage"},
                {
                    "Type": "TERM_MATCH",
                    "Field": "regionCode",
                    "Value": "ap-southeast-3",
                },
                {"Type": "TERM_MATCH", "Field": "volumeType", "Value": "Standard"},
                {
                    "Type": "TERM_MATCH",
                    "Field": "storageClass",
                    "Value": "General Purpose",
                },
            ],
        }
        try:
            data = self.pricing.get_products(**params)
            price = self.parse_storage_pricing_data(data, volume_size)
            self.save_to_cache(cache_key, price)
            return price
        except Exception as e:
            print("Error fetching S3 volume pricing:", e)
            return None

    def get_athena_count(self):
        cache_key = "athena_ap-southeast-3"
        cached = self.lookup_cache(cache_key)
        if cached is not None:
            return cached
        params = {
            "ServiceCode": "AmazonAthena",
            "Filters": [
                {
                    "Type": "TERM_MATCH",
                    "Field": "regionCode",
                    "Value": "ap-southeast-3",
                },
            ],
        }
        try:
            data = self.pricing.get_products(**params)
            price = self.parse_athena_pricing_data(data)
            self.save_to_cache(cache_key, price)
            return price
        except Exception as e:
            print("Error fetching Athena pricing:", e)
            return None


@router.attach("/dportal/pricing/instance", "get")
def get_resource_pricing(event, context):
    instance_type = event.get("queryStringParameters", {}).get("instance_type")
    volume_size = int(event.get("queryStringParameters", {}).get("volume_size"))
    pricing = AWSPricingHelper()

    if not (instance_price := pricing.get_instance_pricing(instance_type)):
        return {
            "success": False,
            "message": "Failed to fetch instance pricing.",
        }

    if not (volume_price := pricing.get_ebs_volume_pricing("gp2", volume_size)):
        return {
            "success": False,
            "message": "Failed to fetch volume pricing.",
        }

    return {
        "success": True,
        "instancePrice": instance_price,
        "volumePrice": volume_price,
    }


@router.attach("/dportal/pricing/athena", "get")
def get_resource_pricing(event, context):
    volume_size = int(event.get("queryStringParameters", {}).get("volume_size"))
    pricing = AWSPricingHelper()

    if not (athena_price := pricing.get_athena_count()):
        return {
            "success": False,
            "message": "Failed to fetch instance pricing.",
        }

    if not (volume_price := pricing.get_volume_pricing(volume_size)):
        return {
            "success": False,
            "message": "Failed to fetch volume pricing.",
        }

    return {
        "success": True,
        "athenaPrice": athena_price,
        "volumePrice": volume_price,
    }
