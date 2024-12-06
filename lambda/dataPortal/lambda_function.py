from admin_dportal_functions import router as admin_dportal_router
from admin_notebook_functions import router as admin_notebook_router
from notebook_functions import router as notebooks_router
from user_functions import router as user_router
from quota_function import router as quota_router
from utils.router import LambdaRouter

router = LambdaRouter()


def lambda_handler(event, context):
    router.update(user_router)
    router.update(notebooks_router)
    router.update(admin_dportal_router)
    router.update(admin_notebook_router)
    router.update(quota_router)
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
