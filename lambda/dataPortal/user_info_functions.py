import json

from shared.apiutils import PortalError, LambdaRouter
from shared.dynamodb import UserInfo

router = LambdaRouter()


@router.attach("/dportal/userinfo", "post")
def store_user_info(event, context):
    try:
        if isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            body = event["body"]

        uid = body.get("uid")
        institutionName = body.get("institutionName", "")

        if not uid:
            return {"success": False, "message": "Missing 'uid' in request body."}

        try:
            user_info = UserInfo.get(uid)
            user_info.update(actions=[UserInfo.institutionName.set(institutionName)])
        except UserInfo.DoesNotExist:
            user_info = UserInfo(
                uid=uid,
                institutionName=institutionName,
            )
            user_info.save()

        return {"success": True, "message": ""}

    except Exception as e:
        return {"success": False, "message": f"An error occurred: {str(e)}"}


@router.attach("/dportal/userinfo/{uid}", "get")
def get_user_info(event, context):
    uid = event["pathParameters"]["uid"]

    try:
        user_info = UserInfo.get(uid)
    except UserInfo.DoesNotExist:
        raise PortalError(
            error_code=409,
            error_message=f"User not found.",
        )

    return user_info.to_dict()
