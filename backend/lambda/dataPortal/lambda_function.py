from portal_functions import router as portal_router
from shared.apiutils import LambdaRouter

router = LambdaRouter()


def lambda_handler(event, context):
    router.update(portal_router)
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
