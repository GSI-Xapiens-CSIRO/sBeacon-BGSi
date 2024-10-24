from portal_functions import router as portal_router
from notebook_functions import router as notebooks_router
from admin_functions import router as admin_router
from utils.router import LambdaRouter

router = LambdaRouter()


def lambda_handler(event, context):
    router.update(portal_router)
    router.update(notebooks_router)
    router.update(admin_router)
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
