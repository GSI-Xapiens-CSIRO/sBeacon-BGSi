import json

from shared.apiutils import PortalError, LambdaRouter
from shared.dynamodb import UserInfo

router = LambdaRouter()


@router.attach("/dportal/userinfo", "post")
def store_user_info(event, context):
    if isinstance(event["body"], str):
        body = json.loads(event["body"])
    else:
        body = event["body"]

    uid = body.get("uid")
    institutionName = body.get("institutionName", "")

    try:
        user_info = UserInfo.get(uid)
        user_info.update(actions=[UserInfo.institutionName.set(institutionName)])
    except UserInfo.DoesNotExist:
        user_info = UserInfo(
            uid=uid,
            institutionName=institutionName,
        )
        user_info.save()

    return user_info.to_dict()


@router.attach("/dportal/userinfo", "get")
def get_user_info(event, context):
    if isinstance(event["body"], str):
        body = json.loads(event["body"])
    else:
        body = event["body"]

    uid = body.get("uid")

    try:
        user_info = UserInfo.get(uid)
    except UserInfo.DoesNotExist:
        raise PortalError(
            error_code=404,
            error_message=f"User not found.",
        )

    return user_info.to_dict()
