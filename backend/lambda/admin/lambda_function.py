from admin_functions import router as admin_router
from admin_functions import log_email_notification
from shared.apiutils import LambdaRouter

router = LambdaRouter()


def lambda_handler(event, context):
    if "Records" in event:
        log_email_notification(event, context)
    else:
        router.update(admin_router)
        return router.handle_route(event, context)


if __name__ == "__main__":
    pass
