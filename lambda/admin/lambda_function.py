from admin_functions import router as admin_router
from shared.apiutils import LambdaRouter

router = LambdaRouter()
router.update(admin_router)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
