import json

from shared.apiutils import PortalError, LambdaRouter
from shared.dynamodb import Quota

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
    Usage = body.get("Usage",{})
    try:
        quota = Quota.get(IdentityUser)
        actions = []
        if CostEstimation:
            actions.append(Quota.CostEstimation.set(CostEstimation))
        for key, value in Usage.items():
            if key in ['usageCount']:
                continue
            try:
                attribute = getattr(Quota.Usage, key)
                actions.append(attribute.set(value))
            except Exception as exc:
                raise PortalError(
                    error_code=404,
                    error_message=str(exc),
                )
        quota.update(
            actions=actions
        )
    except Quota.DoesNotExist:
        quota = Quota(
            uid=IdentityUser,
            CostEstimation=CostEstimation,
            Usage=Usage,
        )
        quota.save()

    return quota.to_dict()

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
@router.attach("/dportal/quota/{userIdentity}", "get")
def get_quota(event, context):
    uId = event["pathParameters"]["userIdentity"]
    try:
        myQuota = Quota.get(uId)

    except Quota.DoesNotExist:
        return {'success': False, 'data': None}
    
    return {'success': True, 'data': myQuota.to_dict()}

@router.attach("/dportal/quota/{userIdentity}/increment_usagecount", "post")
def increment_usagecount(event, context):
    uId = event["pathParameters"]["userIdentity"]
    
    try:
        myQuota = Quota.get(uId)
        myQuota.update(
            actions=[Quota.Usage.usageCount.add(1)]
        )
    except Quota.DoesNotExist:
        raise PortalError(
            error_code=409,
            error_message="No data available here.",
        )
    
    return myQuota.to_dict()
