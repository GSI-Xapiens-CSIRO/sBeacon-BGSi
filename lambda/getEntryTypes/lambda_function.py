from shared.apiutils import LambdaRouter, entry_types, bundle_response

router = LambdaRouter()


@router.attach("/entry_types", "post")
def get_entry_types(event, context):
    response = entry_types()
    return bundle_response(200, response)


def lambda_handler(event, context):
    return router.handle_route(event, context)
