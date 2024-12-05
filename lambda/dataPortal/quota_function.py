import json

from utils.router import PortalError, LambdaRouter
from utils.models import Quota

router = LambdaRouter()

"""
This module provides Lambda functions to store and retrieve quota information.

Functions:
    store_quota(event, context):
        Stores or updates quota information for a given user.
        Args:
            event (dict): The event dictionary containing the request body.
            context (object): The context object provided by AWS Lambda.
        Returns:
            dict: The attribute values of the stored or updated quota.
"""
@router.attach("/dportal/quota", "post")
def store_quota(event, context):
    if isinstance(event["body"], str):
        body = json.loads(event["body"])
    else:
        body = event["body"]
        
    IdentityUser = body.get("IdentityUser")
    CostEstimation = body.get("CostEstimation")
    Usage = body.get("Usage")
    Updatedat = body.get("Updatedat")
    print(IdentityUser, CostEstimation, Usage, Updatedat)
    try:
        quota = Quota.get(IdentityUser, Updatedat)
        quota.update(
            actions=[
                Quota.CostEstimation.set(CostEstimation),
                Quota.Usage.set(Usage)
            ]
        )
    except Quota.DoesNotExist:
        quota = Quota(
            IdentityUser=IdentityUser,
            CostEstimation=CostEstimation,
            Usage=Usage,
            Updatedat=Updatedat
        )
        quota.save()

    return quota.attribute_values

"""
This module provides Lambda functions to store and retrieve quota information.

Functions:
    get_quota(event, context, IdentityUser):
        Retrieves quota information for a given user.
        Args:
            event (dict): The event dictionary containing the request parameters.
            context (object): The context object provided by AWS Lambda.
            IdentityUser (str): The identifier of the user whose quota information is to be retrieved.
        Returns:
            dict: The attribute values of the retrieved quota.
"""
@router.attach("/dportal/quota/{userIdentity}/{updatedAt}", "get")
def get_quota(event, context):
    uId = event["pathParameters"]["userIdentity"]
    updatedAt = event["pathParameters"]["updatedAt"]
    
    try:
        myQuota = Quota.get(uId, updatedAt)

    except Quota.DoesNotExist:
        raise PortalError(
            error_code=409,
            error_message="No data available here.",
        )
    
    return myQuota