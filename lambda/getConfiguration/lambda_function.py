from shared.apiutils import LambdaRouter, configuration, bundle_response

router = LambdaRouter()


@router.attach("/configuration", "post")
def get_configuration(event, context):
    response = configuration()
    return bundle_response(200, response)


def lambda_handler(event, context):
    return router.handle_route(event, context)
