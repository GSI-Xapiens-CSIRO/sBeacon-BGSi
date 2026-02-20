from auth_functions import router as auth_routher
from shared.apiutils import LambdaRouter

router = LambdaRouter()
router.update(auth_routher)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass