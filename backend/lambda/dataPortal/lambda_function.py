from admin_dportal_functions import router as admin_dportal_router
from admin_notebook_functions import router as admin_notebook_router
from notebook_functions import router as notebooks_router
from nextflow_functions import router as nextflow_router
from user_functions import router as user_router
from utils.router import LambdaRouter

router = LambdaRouter()


def lambda_handler(event, context):
    router.update(user_router)
    router.update(notebooks_router)
    router.update(nextflow_router)
    router.update(admin_dportal_router)
    router.update(admin_notebook_router)
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
