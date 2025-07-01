import json

from shared.apiutils import LambdaRouter
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
        institutionType = body.get("institutionType", "")

        if not uid:
            return {"success": False, "message": "Missing 'uid' in request body."}

        try:
            user_info = UserInfo.get(uid)
            user_info.update(actions=[UserInfo.institutionType.set(institutionType)])
        except UserInfo.DoesNotExist:
            user_info = UserInfo(
                uid=uid,
                institutionType=institutionType,
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
        return {
            "success": False,
            "message": f"User not found.",
        }

    return {
        "success": True,
        "message": "",
        "data": user_info.to_dict(),
    }
